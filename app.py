import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client
from google import genai
from google.genai import types
from PIL import Image
import json
from datetime import datetime

# Configuração de página Streamlit
st.set_page_config(
    page_title="FinSmart | Controle Financeiro",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS inspirada no layout Pocketwise
st.markdown("""
<style>
    .stApp {
        background-color: #0b1118;
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #080d13;
        border-right: 1px solid #162433;
    }
    .metric-card {
        background: #101c27;
        border: 1px solid #1c2e40;
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 16px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
    }
    .metric-title {
        color: #7b94a8;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #f8fafc;
    }
    .metric-highlight {
        color: #10b981;
    }
    
    /* Container do Gráfico estilizado */
    .chart-box {
        background: #101c27;
        border: 1px solid #1c2e40;
        border-radius: 16px;
        padding: 20px;
        margin-top: 20px;
    }
    .chart-pre-header {
        color: #5eead4;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 4px;
    }
    .chart-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 2px;
    }
    .chart-sub {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 12px;
    }

    div.stButton > button:first-child {
        background-color: #10b981;
        color: #062419;
        font-weight: 600;
        border: none;
        border-radius: 10px;
        padding: 10px 22px;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:first-child:hover {
        background-color: #059669;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# Inicialização de Clientes via Secrets do Streamlit
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception:
    st.error("⚠️ Configurações não encontradas. Certifique-se de preencher os Secrets no painel do Streamlit Cloud.")
    st.stop()

# Navegação lateral
st.sidebar.markdown("### 💳 FinSmart")
st.sidebar.caption("Seu orçamento sob foco")
aba = st.sidebar.radio("Navegar", ["Visão Geral", "Escanear Extrato (IA)", "Lançamento Rápido"])

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
        return False, f"⚠️ Transação duplicada ignorada: já existe '{dados['descricao']}' no valor de R$ {dados['valor']:.2f} nesta mesma data."
    else:
        supabase.table("transacoes").insert(dados).execute()
        return True, f"✅ Lançado com sucesso: {dados['descricao']} - R$ {dados['valor']:.2f} ({dados['categoria']} / {dados['metodo_pagamento']})"

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
    
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=config
        )
    except Exception:
        response = gemini_client.models.generate_content(
            model='gemini-3.8-flash',
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

    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[audio_part, prompt],
            config=config
        )
    except Exception:
        response = gemini_client.models.generate_content(
            model='gemini-3.8-flash',
            contents=[audio_part, prompt],
            config=config
        )

    dados = json.loads(response.text)
    if isinstance(dados, list) and len(dados) > 0:
        dados = dados[0]
        
    return salvar_no_banco(dados)

@st.dialog("Histórico Completo de Transações", width="large")
def exibir_modal_historico(dados_completos):
    df_modal = dados_completos[["data", "descricao", "categoria", "tipo", "metodo_pagamento", "valor"]].copy()
    df_modal["data"] = df_modal["data"].apply(formatar_data_br)
    df_modal.rename(columns={
        "data": "Data",
        "descricao": "Descrição",
        "categoria": "Categoria",
        "tipo": "Tipo",
        "metodo_pagamento": "Método",
        "valor": "Valor (R$)"
    }, inplace=True)
    
    st.caption(f"Exibindo todas as {len(df_modal)} transações registradas.")
    st.dataframe(df_modal, use_container_width=True, hide_index=True)

df = carregar_transacoes()

# ----------------- ABA 1: VISÃO GERAL -----------------
if aba == "Visão Geral":
    st.markdown("## Seu dinheiro, em foco.")
    st.caption("Visão em tempo real das suas receitas, despesas e distribuição de gastos.")
    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("⚡ Lançamento Rápido (Texto ou Gravar Voz)", expanded=False):
        modo_entrada = st.radio("Escolha a forma de entrada:", ["Digitar Frase", "Gravar Áudio"], horizontal=True, key="modo_vg")
        
        if modo_entrada == "Digitar Frase":
            col_txt, col_btn = st.columns([4, 1])
            with col_txt:
                frase_topo = st.text_input(
                    "Dite ou digite o gasto:",
                    placeholder="Ex: Paguei 35 reais no almoço no débito hoje...",
                    key="input_frase_topo",
                    label_visibility="collapsed"
                )
            with col_btn:
                btn_topo = st.button("Lançar", key="btn_frase_topo")

            if btn_topo and frase_topo.strip():
                with st.spinner("Processando..."):
                    ok, msg = processar_comando_texto(frase_topo)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.warning(msg)

        elif modo_entrada == "Gravar Áudio":
            audio_vg = st.audio_input("Grave seu comando de voz:", key="audio_input_vg")
            if audio_vg is not None:
                if st.button("Processar Áudio Gravado", key="btn_proc_audio_vg"):
                    with st.spinner("Processando áudio com IA..."):
                        audio_bytes = audio_vg.read()
                        ok, msg = processar_comando_audio(audio_bytes, mime_type="audio/wav")
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.warning(msg)

    st.markdown("<br>", unsafe_allow_html=True)

    receitas = df[df["tipo"] == "receita"]["valor"].sum() if not df.empty else 0.0
    despesas = df[df["tipo"] == "despesa"]["valor"].sum() if not df.empty else 0.0
    saldo = receitas - despesas

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Saldo Líquido</div>
            <div class="metric-value metric-highlight">R$ {saldo:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Receitas</div>
            <div class="metric-value">R$ {receitas:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Gastos Totais</div>
            <div class="metric-value">R$ {despesas:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Seção do Gráfico de Fluxo de Caixa no estilo da imagem ---
    st.markdown("""
    <div class="chart-box">
        <div class="chart-pre-header">A VISÃO GERAL</div>
        <div class="chart-header">Fluxo de caixa ao longo do tempo</div>
        <div class="chart-sub">Entrada e saída de dinheiro mês a mês.</div>
    """, unsafe_allow_html=True)

    if not df.empty:
        df_temp = df.copy()
        df_temp['data_dt'] = pd.to_datetime(df_temp['data'])
        df_temp['mes_ano'] = df_temp['data_dt'].dt.to_period('M')

        # Agrupa os valores de receita e despesa por mês
        df_fluxo = df_temp.groupby(['mes_ano', 'tipo'])['valor'].sum().unstack(fill_value=0).reset_index()
        df_fluxo = df_fluxo.sort_values('mes_ano')
        
        # Garante as duas colunas mesmo se não houver registros
        if 'receita' not in df_fluxo.columns:
            df_fluxo['receita'] = 0.0
        if 'despesa' not in df_fluxo.columns:
            df_fluxo['despesa'] = 0.0

        # Formata o eixo X (Ex: Jan, Fev, Mar...)
        meses_rotulo = [d.strftime('%b') for d in df_fluxo['mes_ano'].
