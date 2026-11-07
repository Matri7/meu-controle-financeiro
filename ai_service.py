import json
from datetime import datetime

import streamlit as st
from google import genai
from google.genai import types

from database import salvar_no_banco

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

MODELOS_GEMINI = ("gemini-3.8-flash", "gemini-2.5-flash")
CATEGORIAS_VALIDAS = {"Alimentação", "Transporte", "Moradia", "Lazer", "Saúde", "Serviços", "Outros"}
METODOS_VALIDOS = {"Pix", "Crédito", "Débito", "Dinheiro", "Boleto", "Conta Corrente"}


def _gerar_com_fallback(contents, config):
    """Executa o modelo preferencial e tenta o modelo de fallback se necessário."""
    ultimo_erro = None
    for modelo in MODELOS_GEMINI:
        try:
            return gemini_client.models.generate_content(
                model=modelo,
                contents=contents,
                config=config,
            )
        except Exception as erro:
            ultimo_erro = erro
    raise RuntimeError(f"Não foi possível consultar o Gemini: {ultimo_erro}")


def _ler_json_resposta(response):
    texto = (response.text or "").strip()
    if texto.startswith("```"):
        texto = texto.replace("```json", "", 1).replace("```", "").strip()
    return json.loads(texto)


def _normalizar_transacao(dados):
    """Garante o formato aceito pela tabela transacoes antes da gravação."""
    if isinstance(dados, list):
        dados = dados[0] if dados else {}
    if not isinstance(dados, dict):
        raise ValueError("A IA não retornou uma transação válida.")

    try:
        valor_bruto = dados.get("valor", 0)
        if isinstance(valor_bruto, (int, float)):
            valor = abs(float(valor_bruto))
        else:
            texto_valor = str(valor_bruto).replace("R$", "").strip()
            if "." in texto_valor and "," in texto_valor:
                texto_valor = texto_valor.replace(".", "").replace(",", ".")
            else:
                texto_valor = texto_valor.replace(",", ".")
            valor = abs(float(texto_valor))
    except (TypeError, ValueError):
        valor = 0.0
    if valor <= 0:
        raise ValueError("Não foi possível identificar um valor positivo na entrada.")

    tipo = str(dados.get("tipo", "despesa")).lower().strip()
    if tipo not in {"despesa", "receita"}:
        tipo = "despesa"

    categoria = str(dados.get("categoria", "Outros")).strip()
    if categoria not in CATEGORIAS_VALIDAS:
        categoria = "Outros"

    metodo = str(dados.get("metodo_pagamento", "Pix")).strip()
    if metodo not in METODOS_VALIDOS:
        metodo = "Pix"

    data = str(dados.get("data", "")).strip()
    try:
        data = datetime.strptime(data[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        data = datetime.today().strftime("%Y-%m-%d")

    descricao = str(dados.get("descricao", "Transação importada")).strip() or "Transação importada"
    return {
        "data": data,
        "descricao": descricao[:160],
        "valor": round(valor, 2),
        "tipo": tipo,
        "categoria": categoria,
        "metodo_pagamento": metodo,
    }


def _config_json():
    return types.GenerateContentConfig(response_mime_type="application/json")


def interpretar_comando_texto(texto_usuario):
    hoje_iso = datetime.today().strftime("%Y-%m-%d")
    prompt = f"""
    O usuário informou a seguinte transação financeira em linguagem informal:
    "{texto_usuario}"

    Data de referência de hoje: {hoje_iso}.
    Retorne APENAS um objeto JSON com data, descricao, valor, tipo, categoria e metodo_pagamento.
    O valor deve ser um número positivo. A data deve estar no formato AAAA-MM-DD.
    tipo deve ser "despesa" ou "receita".
    categoria deve ser uma entre Alimentação, Transporte, Moradia, Lazer, Saúde, Serviços ou Outros.
    metodo_pagamento deve ser uma entre Pix, Crédito, Débito, Dinheiro, Boleto ou Conta Corrente.
    Se a data não for dita, use {hoje_iso}. Se o método não for citado, use Pix.
    """
    resposta = _gerar_com_fallback(prompt, _config_json())
    return _normalizar_transacao(_ler_json_resposta(resposta))


def processar_comando_texto(texto_usuario):
    try:
        dados = interpretar_comando_texto(texto_usuario)
        return salvar_no_banco(dados)
    except Exception as erro:
        return False, f"Não foi possível registrar o texto: {erro}"


def interpretar_comando_audio(audio_bytes, mime_type="audio/wav"):
    hoje_iso = datetime.today().strftime("%Y-%m-%d")
    prompt = f"""
    Ouça o áudio e identifique uma única transação financeira. Data de hoje: {hoje_iso}.
    Retorne APENAS um objeto JSON com data, descricao, valor, tipo, categoria e metodo_pagamento.
    O valor deve ser positivo, a data deve estar no formato AAAA-MM-DD e, se não houver data, use {hoje_iso}.
    """
    audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type or "audio/wav")
    resposta = _gerar_com_fallback([audio_part, prompt], _config_json())
    return _normalizar_transacao(_ler_json_resposta(resposta))


def processar_comando_audio(audio_bytes, mime_type="audio/wav"):
    try:
        dados = interpretar_comando_audio(audio_bytes, mime_type)
        return salvar_no_banco(dados)
    except Exception as erro:
        return False, f"Não foi possível registrar o áudio: {erro}"


def interpretar_arquivo_extrato(arquivo_ou_img, is_pdf=False):
    prompt = """
    Analise este extrato bancário, fatura, comprovante ou imagem.
    Extraia TODOS os lançamentos financeiros individuais visíveis e retorne obrigatoriamente uma lista JSON.
    Ignore saldos, totais, cabeçalhos, telefones e juros.
    Cada item deve conter data (AAAA-MM-DD), descricao, valor positivo, tipo, categoria e metodo_pagamento.
    tipo deve ser despesa ou receita. Categorias: Alimentação, Transporte, Moradia, Lazer, Saúde, Serviços ou Outros.
    Métodos: Pix, Crédito, Débito, Dinheiro, Boleto ou Conta Corrente.
    """
    if is_pdf:
        parte = types.Part.from_bytes(data=arquivo_ou_img, mime_type="application/pdf")
        payload = [parte, prompt]
    else:
        payload = [arquivo_ou_img, prompt]

    resposta = _gerar_com_fallback(payload, _config_json())
    dados = _ler_json_resposta(resposta)
    if isinstance(dados, dict):
        dados = [dados]
    return [_normalizar_transacao(item) for item in dados if isinstance(item, dict)]


def processar_arquivo_extrato(arquivo_ou_img, is_pdf=False):
    return interpretar_arquivo_extrato(arquivo_ou_img, is_pdf=is_pdf)


def gerar_auditoria_semanal(dados_resumidos_txt):
    prompt = f"""
    Você é um consultor financeiro pessoal ágil e analítico.
    Analise o consolidado da semana financeira do usuário:

    {dados_resumidos_txt}

    Retorne OBRIGATORIAMENTE um JSON puro com:
    {{
        "resumo_curto": "Frase de 1 a 2 linhas resumindo a situação.",
        "analise_completa": "Análise em markdown com diagnóstico, categorias e recomendações práticas."
    }}
    """
    try:
        resposta = _gerar_com_fallback(prompt, _config_json())
        return _ler_json_resposta(resposta)
    except Exception:
        return {
            "resumo_curto": "Dados da semana compilados com sucesso.",
            "analise_completa": "Não foi possível gerar a análise detalhada no momento.",
        }
