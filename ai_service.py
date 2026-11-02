import streamlit as st
import json
from datetime import datetime
from google import genai
from google.genai import types
from database import salvar_no_banco

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

def processar_comando_texto(texto_usuario):
    hoje_iso = datetime.today().strftime("%Y-%m-%d")
    prompt = f"""
    O usuário informou a seguinte transação financeira em linguagem informal:
    "{texto_usuario}"

    Data de referência de hoje: {hoje_iso}.

    Retorne APENAS um objeto JSON com estes campos:
    {{
        "data": "AAAA-MM-DD",
        "descricao": "Nome do estabelecimento ou despesa",
        "valor": 12.34,
        "tipo": "despesa" ou "receita",
        "categoria": "Alimentação" | "Transporte" | "Moradia" | "Lazer" | "Saúde" | "Serviços" | "Outros",
        "metodo_pagamento": "Pix" | "Crédito" | "Débito" | "Dinheiro" | "Boleto"
    }}
    Regras:
    - O campo 'valor' deve ser SEMPRE float numérico positivo.
    - Se a data não for dita, use '{hoje_iso}'.
    - Se não citar o método, use 'Pix' ou 'Débito'.
    """
    config = types.GenerateContentConfig(response_mime_type="application/json")
    
    # Prioridade 3.8 Flash, com fallback para 2.5 Flash
    try:
        response = gemini_client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt,
            config=config
        )
    except Exception:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=config
        )
    
    dados = json.loads(response.text)
    if isinstance(dados, list) and len(dados) > 0:
        dados = dados[0]
        
    return salvar_no_banco(dados)

def processar_comando_audio(audio_bytes, mime_type="audio/wav"):
    hoje_iso = datetime.today().strftime("%Y-%m-%d")
    prompt = f"""
    Ouça esta transação financeira. Data de hoje: {hoje_iso}.
    Retorne APENAS um objeto JSON puro:
    {{
        "data": "AAAA-MM-DD",
        "descricao": "Nome do estabelecimento ou despesa",
        "valor": 12.34,
        "tipo": "despesa" ou "receita",
        "categoria": "Alimentação" | "Transporte" | "Moradia" | "Lazer" | "Saúde" | "Serviços" | "Outros",
        "metodo_pagamento": "Pix" | "Crédito" | "Débito" | "Dinheiro" | "Boleto"
    }}
    """
    config = types.GenerateContentConfig(response_mime_type="application/json")
    audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)

    # Prioridade 3.8 Flash, com fallback para 2.5 Flash
    try:
        response = gemini_client.models.generate_content(
            model='gemini-3.8-flash',
            contents=[audio_part, prompt],
            config=config
        )
    except Exception:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[audio_part, prompt],
            config=config
        )

    dados = json.loads(response.text)
    if isinstance(dados, list) and len(dados) > 0:
        dados = dados[0]
        
    return salvar_no_banco(dados)

def processar_arquivo_extrato(arquivo_ou_img, is_pdf=False):
    prompt = """
    Analise este arquivo de extrato bancário, fatura ou comprovante financeiro.
    Extraia TODOS os lançamentos financeiros individuais visíveis e responda OBRIGATORIAMENTE em formato JSON com uma lista de objetos.
    
    IGNORE linhas que sejam apenas: saldos do dia, saldo anterior, juros de cheque especial, cabeçalhos, telefones de SAC ou totais de página.
    
    Cada objeto deve conter:
    - data: no formato AAAA-MM-DD (se não houver ano legível, use o ano atual).
    - descricao: nome do recebedor, estabelecimento ou operação.
    - valor: número positivo float (ex: 29.90).
    - tipo: "despesa" para pagamentos/saídas ou "receita" para recebimentos/entradas.
    - categoria: uma entre "Alimentação", "Transporte", "Moradia", "Lazer", "Serviços", "Saúde" ou "Outros".
    - metodo_pagamento: "Pix", "Crédito", "Débito" ou "Boleto".
    """
    config = types.GenerateContentConfig(response_mime_type="application/json")

    if is_pdf:
        content_part = types.Part.from_bytes(data=arquivo_ou_img, mime_type="application/pdf")
        payload = [content_part, prompt]
    else:
        payload = [arquivo_ou_img, prompt]

    # Prioridade 3.8 Flash para PDF e imagens, com fallback para 2.5 Flash
    try:
        response = gemini_client.models.generate_content(
            model='gemini-3.8-flash',
            contents=payload,
            config=config
        )
    except Exception:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=payload,
            config=config
        )

    dados = json.loads(response.text)
    if isinstance(dados, dict):
        dados = [dados]
    return dados

def gerar_auditoria_semanal(dados_resumidos_txt):
    prompt = f"""
    Você é um consultor financeiro pessoal ágil e analítico.
    Analise o consolidado da semana financeira do usuário (incluindo receitas, despesas e comparação com os tetos de orçamento planejados):

    {dados_resumidos_txt}

    Retorne OBRIGATORIAMENTE um JSON puro com esta estrutura:
    {{
        "resumo_curto": "Frase de 1 a 2 linhas resumindo a situação e destacando se alguma categoria estourou ou está perto do teto.",
        "analise_completa": "Análise em markdown (com bullet points): 1. Diagnóstico do fluxo, 2. Categorias que mais consumiram o teto orçado, 3. Recomendações práticas para equilibrar o orçamento esta semana."
    }}
    """
    config = types.GenerateContentConfig(response_mime_type="application/json")
    
    # Prioridade 3.8 Flash para o relatório analítico, com fallback para 2.5 Flash
    try:
        response = gemini_client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt,
            config=config
        )
        return json.loads(response.text)
    except Exception:
        try:
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=config
            )
            return json.loads(response.text)
        except Exception:
            return {
                "resumo_curto": "Dados da semana compilados com sucesso.",
                "analise_completa": "Não foi possível gerar a análise detalhada no momento."
            }
