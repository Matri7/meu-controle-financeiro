import streamlit as st
import pandas as pd
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
    /* Fundo geral e fontes */
    .stApp {
        background-color: #0b1118;
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #080d13;
        border-right: 1px solid #162433;
    }
    
    /* Cards métricos customizados */
    .metric-card {
        background: #101c27;
        border: 1px solid #1c2e40;
        border-radius: 16px;
        padding: 22px;
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
    
    /* Botões */
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

# Função para carregar transações do Supabase
def carregar_transacoes():
    res = supabase.table("transacoes").select("*").order("data", desc=True).execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame(columns=["id", "data", "descricao", "valor", "tipo", "categoria", "metodo_pagamento"])

df = carregar_transacoes()

# ----------------- ABA 1: VISÃO GERAL -----------------
if aba == "Visão Geral":
    st.markdown("## Seu dinheiro, em foco.")
    st.caption("Visão em tempo real das suas receitas, despesas e distribuição de gastos.")
    st.markdown("<br>", unsafe_allow_html=True)

    # Cálculo dos totais
    receitas = df[df["tipo"] == "receita"]["valor"].sum() if not df.empty else 0.0
    despesas = df[df["tipo"] == "despesa"]["valor"].sum() if not df.empty else 0.0
    saldo = receitas - despesas

    # Cards no estilo Pocketwise
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

    # Gráficos e tabela
    col_g1, col_g2 = st.columns([1.2, 1])
    
    with col_g1:
        st.subheader("Extrato Recente")
        if not df.empty:
            st.dataframe(
                df[["data", "descricao", "categoria", "tipo", "valor"]].head(10),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhuma transação cadastrada ainda.")

    with col_g2:
        st.subheader("Onde foi o dinheiro (Categorias)")
        despesas_df = df[df["tipo"] == "despesa"] if not df.empty else pd.DataFrame()
        if not despesas_df.empty:
            fig = px.pie(
                despesas_df,
                names="categoria",
                values="valor",
                hole=0.65,
                color_discrete_sequence=px.colors.sequential.Tealgrn_r
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#cbd5e1",
                showlegend=True,
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem despesas para exibir o gráfico.")

# ----------------- ABA 2: ESCANEAR EXTRATO COM GEMINI -----------------
elif aba == "Escanear Extrato (IA)":
    st.subheader("Leitor Inteligente de Extratos e Prints")
    st.caption("Suba o print de uma fatura, extrato bancário ou comprovante Pix.")

    uploaded_file = st.file_uploader("Escolha a imagem", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="Print carregado", width=380)

        if st.button("Processar com IA do Gemini"):
            with st.spinner("Analisando extrato e extraindo transações..."):
                prompt = """
                Analise esta imagem de extrato bancário, fatura ou comprovante financeiro.
                Extraia todos os lançamentos financeiros visíveis e responda OBRIGATORIAMENTE em formato JSON com uma lista de objetos.
                Cada objeto deve conter:
                - data: no formato AAAA-MM-DD (se não houver ano legível, use o ano atual).
                - descricao: nome do recebedor, estabelecimento ou operação.
                - valor: número positivo float (ex: 29.90).
                - tipo: "despesa" para pagamentos/saídas ou "receita" para recebimentos/entradas.
                - categoria: uma entre "Alimentação", "Transporte", "Moradia", "Lazer", "Serviços", "Saúde" ou "Outros".
                - metodo_pagamento: "Pix", "Crédito", "Débito" ou "Boleto".
                """
                try:
                    # Configuração para forçar resposta em JSON puro
                    config = types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                    
                 try:   
        response = gemini_client.models.generate_content(
        model='gemini-3.8-flash',
        contents=[img, prompt],
        config=config
    )
    except Exception:
    # Se o modelo principal estiver sobrecarregado (503), tenta o modelo estável alternativo
    response = gemini_client.models.generate_content(
        model='gemini-2.0-flash',
        contents=[img, prompt],
        config=config
    )
                    
                    
                    dados = json.loads(response.text)

                    # Garante que dados seja uma lista
                    if isinstance(dados, dict):
                        dados = [dados]

                    for item in dados:
                        supabase.table("transacoes").insert(item).execute()

                    st.success(f"Sucesso! {len(dados)} transação(ões) identificada(s) e salva(s) no Supabase.")
                    st.rerun()

                except Exception as e:
                    st.error(f"Erro ao processar: {e}")

# ----------------- ABA 3: LANÇAMENTO RÁPIDO -----------------
elif aba == "Lançamento Rápido":
    st.subheader("Novo Lançamento Manual")
    with st.form("form_transacao"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            desc = st.text_input("Descrição (Ex: Padaria, Salário)")
            valor = st.number_input("Valor (R$)", min_value=0.01, step=1.00)
            data_t = st.date_input("Data", datetime.today())
        with col_f2:
            tipo = st.selectbox("Tipo", ["despesa", "receita"])
            categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Moradia", "Lazer", "Saúde", "Serviços", "Outros"])
            metodo = st.selectbox("Método de Pagamento", ["Pix", "Crédito", "Débito", "Dinheiro"])
        
        submit = st.form_submit_button("Salvar Transação")
        if submit:
            payload = {
                "descricao": desc,
                "valor": valor,
                "data": str(data_t),
                "tipo": tipo,
                "categoria": categoria,
                "metodo_pagamento": metodo
            }
            supabase.table("transacoes").insert(payload).execute()
            st.success("Transação salva com sucesso!")
            st.rerun()
