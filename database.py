import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Inicializa o cliente do Supabase usando os Secrets do Streamlit
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
