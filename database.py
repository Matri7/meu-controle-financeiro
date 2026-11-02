import streamlit as st
import pandas as pd
from supabase import create_client, Client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def formatar_data_br(data_val):
    try:
        return pd.to_datetime(data_val).strftime("%d/%m/%Y")
    except Exception:
        return str(data_val)

def carregar_transacoes():
    res = supabase.table("transacoes").select("*").order("data", desc=True).execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame(columns=["id", "data", "descricao", "valor", "tipo", "categoria", "metodo_pagamento"])

def salvar_no_banco(dados):
    duplicado = supabase.table("transacoes").select("id")\
        .eq("data", dados["data"])\
        .eq("descricao", dados["descricao"])\
        .eq("valor", dados["valor"])\
        .execute()

    if duplicado.data and len(duplicado.data) > 0:
        return False, f"⚠️ Transação duplicada ignorada: já existe '{dados['descricao']}' no valor de R$ {dados['valor']:.2f} nesta data."
    else:
        supabase.table("transacoes").insert(dados).execute()
        return True, f"✅ Lançado com sucesso: {dados['descricao']} - R$ {dados['valor']:.2f} ({dados['categoria']} / {dados['metodo_pagamento']})"

def atualizar_transacao(id_transacao, dados_atualizados):
    supabase.table("transacoes").update(dados_atualizados).eq("id", id_transacao).execute()

def excluir_transacao(id_transacao):
    supabase.table("transacoes").delete().eq("id", id_transacao).execute()

# --- Funções de Orçamento (Budget) ---
def carregar_orcamentos():
    res = supabase.table("orcamentos").select("*").execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame(columns=["categoria", "valor_teto"])

def salvar_orcamento(categoria, valor_teto):
    payload = {"categoria": categoria, "valor_teto": float(valor_teto)}
    supabase.table("orcamentos").upsert(payload, on_conflict="categoria").execute()

# --- Funções do Módulo Uber ---
def salvar_diaria_uber(dados_uber):
    supabase.table("diarias_uber").insert(dados_uber).execute()
    
    transacao_payload = {
        "data": dados_uber["data"],
        "descricao": f"Ganhos Uber ({dados_uber['km_rodados']} km)",
        "valor": dados_uber["ganho_bruto"],
        "tipo": "receita",
        "categoria": "Outros",
        "metodo_pagamento": "Conta Corrente"
    }
    salvar_no_banco(transacao_payload)

def carregar_diarias_uber():
    res = supabase.table("diarias_uber").select("*").order("data", desc=True).execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame(columns=["id", "data", "ganho_bruto", "km_rodados", "horas_online", "custo_km_padrao", "outros_gastos", "observacao"])

def atualizar_diaria_uber(id_diaria, dados_atualizados):
    supabase.table("diarias_uber").update(dados_atualizados).eq("id", id_diaria).execute()

def excluir_diaria_uber(id_diaria):
    supabase.table("diarias_uber").delete().eq("id", id_diaria).execute()

# --- Funções de Cache de Relatório Semanal ---
def obter_relatorio_semanal(semana_ano):
    res = supabase.table("relatorios_semanais").select("*").eq("semana_ano", semana_ano).execute()
    if res.data and len(res.data) > 0:
        return res.data[0]
    return None

def salvar_relatorio_semanal(semana_ano, resumo_curto, analise_completa):
    payload = {
        "semana_ano": semana_ano,
        "resumo_curto": resumo_curto,
        "analise_completa": analise_completa
    }
    supabase.table("relatorios_semanais").upsert(payload, on_conflict="semana_ano").execute()
