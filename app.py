import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from PIL import Image
from datetime import datetime, timedelta

from database import (
    supabase, formatar_data_br, carregar_transacoes, salvar_no_banco,
    atualizar_transacao, excluir_transacao,
    carregar_orcamentos, salvar_orcamento,
    obter_relatorio_semanal, salvar_relatorio_semanal,
    carregar_diarias_uber, salvar_diaria_uber,
    atualizar_diaria_uber, excluir_diaria_uber
)
from ai_service import (
    processar_comando_texto, processar_comando_audio, processar_arquivo_extrato,
    gerar_auditoria_semanal
)
from charts import renderizar_grafico_fluxo, renderizar_grafico_pizza

st.set_page_config(
    page_title="de bolso . | Cada movimento, contabilizado",
    page_icon=":material/account_balance_wallet:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Cirúrgica e Responsiva (Desktop & Mobile)
st.markdown("""
<style>
    .stApp { background-color: #0b1118; color: #f1f5f9; font-family: 'Inter', sans-serif; }
    
    /* Barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #080d13 !important;
        border-right: 1px solid #141f2b !important;
        padding-top: 1.2rem !important;
    }
    
    section[data-testid="stSidebar"] div[data-testid="stSidebarContent"] {
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:has(div.stButton) {
        margin-bottom: 4px !important;
    }

    section[data-testid="stSidebar"] div.stButton {
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    section[data-testid="stSidebar"] div.stButton > button {
        width: 100% !important;
        display: flex !important;
        flex-direction: row !important;
        justify-content: flex-start !important;
        align-items: center !important;
        text-align: left !important;
        background-color: transparent !important;
        color: #8fa0b5 !important;
        border: 1px solid transparent !important;
        border-radius: 12px !important;
        padding: 10px 16px !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        transition: all 0.15s ease-in-out !important;
        box-sizing: border-box !important;
    }

    section[data-testid="stSidebar"] div.stButton > button > div,
    section[data-testid="stSidebar"] div.stButton > button div[data-testid="stMarkdownContainer"],
    section[data-testid="stSidebar"] div.stButton > button p {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        text-align: left !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    section[data-testid="stSidebar"] div.stButton > button span[data-testid="stIconMaterial"] {
        margin-right: 12px !important;
        margin-left: 0 !important;
        font-size: 1.25rem !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 24px !important;
        flex-shrink: 0 !important;
    }
    
    section[data-testid="stSidebar"] div.stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.04) !important;
        color: #f1f5f9 !important;
    }
    
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background-color: #101c27 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border: 1px solid #1c2e40 !important;
        border-left: 3.5px solid #2dd4bf !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] span[data-testid="stIconMaterial"] {
        color: #2dd4bf !important;
    }

    /* FORÇA O BOTÃO ADICIONAR E DEMAIS PRIMÁRIOS NO VERDE PADRÃO DO APP */
    button[data-testid="stBaseButton-primary"],
    button[data-testid="baseButton-primary"],
    button[kind="primary"],
    .stButton > button[kind="primary"],
    div.stButton > button[kind="primary"] {
        background-color: #34d399 !important;
        background: #34d399 !important;
        color: #052e16 !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
    }
    button[data-testid="stBaseButton-primary"]:hover,
    button[data-testid="baseButton-primary"]:hover,
    button[kind="primary"]:hover,
    .stButton > button[kind="primary"]:hover {
        background-color: #10b981 !important;
        background: #10b981 !important;
        color: #ffffff !important;
    }
    button[data-testid="stBaseButton-primary"] span,
    button[kind="primary"] span {
        color: #052e16 !important;
    }

    div.main div.stButton > button[kind="secondary"] {
        background-color: #101c27 !important;
        color: #cbd5e1 !important;
        border: 1px solid #1e2f40 !important;
        border-radius: 10px !important;
        padding: 8px 14px !important;
        font-weight: 500 !important;
    }
    div.main div.stButton > button[kind="secondary"]:hover {
        background-color: #162635 !important;
        color: #ffffff !important;
        border-color: #2dd4bf !important;
    }

    /* BOTÕES TERCIÁRIOS (SETAS, LÁPIS E LIXEIRA) */
    button[data-testid="stBaseButton-tertiary"],
    button[data-testid="baseButton-tertiary"],
    button[kind="tertiary"],
    .stButton > button[kind="tertiary"] {
        background-color: transparent !important;
        color: #8fa0b5 !important;
        border: none !important;
        padding: 4px !important;
        min-height: 32px !important;
        height: 32px !important;
        border-radius: 6px !important;
    }
    button[data-testid="stBaseButton-tertiary"]:hover,
    button[kind="tertiary"]:hover {
        color: #34d399 !important;
        background-color: rgba(52, 211, 153, 0.08) !important;
    }

    /* SELETOR DE MÊS FIXO EM UMA LINHA HORIZONTAL (NUNCA QUEBRA EM COLUNAS NO MOBILE) */
    div[data-testid="stHorizontalBlock"]:has(.month-selector-marker) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: center !important;
        background: #101c27 !important;
        border: 1px solid #1e2f40 !important;
        border-radius: 12px !important;
        padding: 2px 4px !important;
        gap: 2px !important;
        width: 100% !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.month-selector-marker) > div[data-testid="column"] {
        width: auto !important;
        min-width: 0 !important;
        flex: 0 0 34px !important;
        padding: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.month-selector-marker) > div[data-testid="column"]:nth-child(2) {
        flex: 1 1 auto !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.month-selector-marker) div[data-baseweb="select"] > div {
        background-color: transparent !important;
        border: none !important;
        color: #f1f5f9 !important;
        font-weight: 600 !important;
        font-size: 0.86rem !important;
        padding: 0 4px !important;
        height: 36px !important;
    }

    /* LINHA DE TRANSAÇÃO SEMPRE HORIZONTAL (DESKTOP E MOBILE) */
    div[data-testid="stHorizontalBlock"]:has(.tx-row-anchor) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        padding: 6px 0 !important;
        gap: 6px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.tx-row-anchor) > div[data-testid="column"]:nth-child(1) {
        flex: 1 1 auto !important;
        min-width: 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.tx-row-anchor) > div[data-testid="column"]:nth-child(2) {
        flex: 0 0 auto !important;
        text-align: right !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-end !important;
        padding: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.tx-row-anchor) > div[data-testid="column"]:nth-child(3),
    div[data-testid="stHorizontalBlock"]:has(.tx-row-anchor) > div[data-testid="column"]:nth-child(4) {
        flex: 0 0 34px !important;
        width: 34px !important;
        min-width: 34px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
    }

    .tx-left {
        display: flex;
        align-items: center;
        gap: 12px;
        min-width: 0;
    }
    .tx-icon-box {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        background: #13202c;
        border: 1px solid #1e3244;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .tx-desc {
        font-size: 0.92rem;
        font-weight: 600;
        color: #f8fafc;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .tx-meta {
        font-size: 0.76rem;
        color: #64748b;
        margin-top: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .tx-val-despesa {
        font-size: 0.94rem;
        font-weight: 700;
        color: #f1f5f9;
        margin: 0 !important;
        padding: 0 !important;
        white-space: nowrap;
    }
    .tx-val-receita {
        font-size: 0.94rem;
        font-weight: 700;
        color: #34d399;
        margin: 0 !important;
        padding: 0 !important;
        white-space: nowrap;
    }
    .tx-divider {
        border-bottom: 1px solid #14202c;
        margin: 2px 0;
    }

    .metric-card { 
        background: #101c27; 
        border: 1px solid #1c2e40; 
        border-radius: 16px; 
        padding: 22px; 
        margin-bottom: 16px; 
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25); 
    }
    .metric-title { color: #7b94a8; font-size: 0.82rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
    .metric-value { font-size: 1.85rem; font-weight: 700; color: #f8fafc; }
    .metric-highlight { color: #34d399; }

    .count-badge {
        background-color: rgba(45, 212, 191, 0.12);
        color: #2dd4bf;
        border: 1px solid rgba(45, 212, 191, 0.3);
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-left: 8px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #101c27;
        border: 1px solid #1c2e40 !important;
        border-radius: 16px !important;
        padding: 18px !important;
        margin-top: 12px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Script JS Inteligente para Fechamento Automático da Sidebar no Mobile ao Clicar
components.html("""
<script>
function setupMobileAutoClose() {
    try {
        const parentDoc = window.parent.document;
        if (!parentDoc) return;
        
        const isMobile = window.parent.innerWidth <= 768;
        if (isMobile) {
            const sidebar = parentDoc.querySelector('section[data-testid="stSidebar"]');
            if (sidebar) {
                const buttons = sidebar.querySelectorAll('div.stButton > button');
                buttons.forEach(btn => {
                    if (!btn.dataset.closeListenerAttached) {
                        btn.dataset.closeListenerAttached = "true";
                        btn.addEventListener('click', () => {
                            setTimeout(() => {
                                // Tenta o botão de recolher (o '<<')
                                const closeBtn = sidebar.querySelector('button[data-testid="stSidebarCollapseButton"]')
                                              || parentDoc.querySelector('button[data-testid="stSidebarCollapseButton"]')
                                              || sidebar.querySelector('button[aria-label*="Close"]')
                                              || sidebar.querySelector('button[aria-label*="Fechar"]');
                                if (closeBtn) {
                                    closeBtn.click();
                                } else {
                                    const backdrop = parentDoc.querySelector('[data-testid="stSidebarBackdrop"]');
                                    if (backdrop) backdrop.click();
                                }
                            }, 100);
                        });
                    }
                });
            }
        }
    } catch(e) {}
}
setInterval(setupMobileAutoClose, 300);
</script>
""", height=0, width=0)

# Parsing de Moeda Seguro (Sem falhas se o usuário digitar sem máscara)
def parse_moeda_automatica(texto_val):
    if not texto_val:
        return 0.0
    txt = str(texto_val).replace("R$", "").replace("r$", "").strip()
    if not txt:
        return 0.0
    if "," in txt:
        txt_limpo = txt.replace(".", "").replace(",", ".")
        try:
            return float(txt_limpo)
        except ValueError:
            return 0.0
    elif "." in txt:
        try:
            return float(txt)
        except ValueError:
            return 0.0
    else:
        digitos = "".join([c for c in txt if c.isdigit()])
        if not digitos:
            return 0.0
        return float(digitos) / 100.0

def parse_hora_automatica(texto_hora):
    if not texto_hora:
        return 0.0, "0:00 h"
    txt = str(texto_hora).replace("h", "").replace("H", "").strip()
    if ":" in txt:
        partes = txt.split(":")
        h = int(partes[0].strip()) if partes[0].strip().isdigit() else 0
        m = int(partes[1].strip()) if len(partes) > 1 and partes[1].strip().isdigit() else 0
    else:
        digitos = "".join([c for c in txt if c.isdigit()])
        if not digitos:
            return 0.0, "0:00 h"
        if len(digitos) <= 2:
            h = 0
            m = int(digitos)
        else:
            h = int(digitos[:-2])
            m = int(digitos[-2:])
            
    h += m // 60
    m = m % 60
    hora_decimal = round(h + (m / 60.0), 3)
    hora_formatada = f"{h}:{m:02d} h"
    return hora_decimal, hora_formatada

MAPA_SVGS_CAT = {
    "Alimentação": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/><path d="M7 2v20"/><path d="M21 15V2v0a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/></svg>',
    "Transporte": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><path d="M9 17h6"/><circle cx="17" cy="17" r="2"/></svg>',
    "Moradia": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2dd4bf" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    "Lazer": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f472b6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 3v18"/><path d="M3 7.5h4"/><path d="M3 12h18"/><path d="M3 16.5h4"/><path d="M17 3v18"/><path d="M17 7.5h4"/><path d="M17 16.5h4"/></svg>',
    "Saúde": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4ade80" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/><path d="M12 5 9.04 7.96a2.17 2.17 0 0 0 0 3.08c.82.82 2.13.85 3 .07l2.07-1.9a2.82 2.82 0 0 1 3.79 0l2.96 2.66"/></svg>',
    "Serviços": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "Outros": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>'
}

CATEGORIAS_DISPONIVEIS = ["Alimentação", "Transporte", "Moradia", "Lazer", "Saúde", "Serviços", "Outros"]

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# --- BARRA LATERAL ---
st.sidebar.markdown("""
<div style="display: flex; align-items: center; gap: 12px; padding: 0 4px 22px 4px;">
    <div style="background: rgba(45, 212, 191, 0.08); border: 1.5px solid rgba(45, 212, 191, 0.4); border-radius: 12px; width: 42px; height: 42px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2dd4bf" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 5H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2z"></path>
            <path d="m3 7 9 6 9-6"></path>
            <circle cx="12" cy="13" r="1" fill="#2dd4bf"></circle>
        </svg>
    </div>
    <div style="font-size: 1.3rem; font-weight: 800; color: #ffffff; letter-spacing: -0.02em;">
        de bolso <span style="color: #2dd4bf;">.</span>
    </div>
</div>

<div style="font-size: 0.68rem; font-weight: 700; color: #4e6173; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 12px; padding-left: 6px;">
    Espaço de trabalho
</div>
""", unsafe_allow_html=True)

if "aba_ativa" not in st.session_state:
    st.session_state["aba_ativa"] = "Visão Geral"

btn_vg = st.sidebar.button(
    "Visão geral",
    icon=":material/home:",
    key="nav_vg",
    type="primary" if st.session_state["aba_ativa"] == "Visão Geral" else "secondary",
    use_container_width=True
)
if btn_vg:
    st.session_state["aba_ativa"] = "Visão Geral"
    st.rerun()

btn_tx = st.sidebar.button(
    "Transações",
    icon=":material/sync_alt:",
    key="nav_tx",
    type="primary" if st.session_state["aba_ativa"] == "Transações" else "secondary",
    use_container_width=True
)
if btn_tx:
    st.session_state["aba_ativa"] = "Transações"
    st.rerun()

btn_ub = st.sidebar.button(
    "Controle Uber",
    icon=":material/directions_car:",
    key="nav_ub",
    type="primary" if st.session_state["aba_ativa"] == "Controle Uber" else "secondary",
    use_container_width=True
)
if btn_ub:
    st.session_state["aba_ativa"] = "Controle Uber"
    st.rerun()

btn_orc = st.sidebar.button(
    "Orçamentos",
    icon=":material/layers:",
    key="nav_orc",
    type="primary" if st.session_state["aba_ativa"] == "Orçamentos" else "secondary",
    use_container_width=True
)
if btn_orc:
    st.session_state["aba_ativa"] = "Orçamentos"
    st.rerun()

aba = st.session_state["aba_ativa"]

# Dados globais e Lista de Meses
df = carregar_transacoes()
df_orc = carregar_orcamentos()
df_uber = carregar_diarias_uber()

mes_atual_chave = datetime.today().strftime('%Y-%m')
meses_disponiveis = set([mes_atual_chave])

if not df.empty:
    df['data_dt'] = pd.to_datetime(df['data'])
    df['periodo_chave'] = df['data_dt'].dt.strftime('%Y-%m')
    meses_disponiveis.update(df['periodo_chave'].dropna().tolist())

if not df_uber.empty:
    df_uber['data_dt'] = pd.to_datetime(df_uber['data'])
    df_uber['periodo_chave'] = df_uber['data_dt'].dt.strftime('%Y-%m')
    meses_disponiveis.update(df_uber['periodo_chave'].dropna().tolist())

ano_hoje = datetime.today().year
for m_idx in range(1, 13):
    meses_disponiveis.add(f"{ano_hoje}-{m_idx:02d}")

# Lista em ordem decrescente (ex: Dezembro de 2026 até Janeiro)
LISTA_MESES_ORDENADA = sorted(list(meses_disponiveis), reverse=True)

if "mes_selecionado_global" not in st.session_state:
    st.session_state["mes_selecionado_global"] = mes_atual_chave

def formatar_mes_extenso(chave_ym, caixa_alta=False):
    ano, mes = chave_ym.split('-')
    texto = f"{MESES_PT[int(mes)]} de {ano}"
    return texto.upper() if caixa_alta else texto

# Callbacks Oficiais do Streamlit para o Seletor de Mês (Garante funcionamento imediato)
def ir_mes_anterior(key_prefix):
    idx = LISTA_MESES_ORDENADA.index(st.session_state["mes_selecionado_global"])
    if idx < len(LISTA_MESES_ORDENADA) - 1:
        novo_mes = LISTA_MESES_ORDENADA[idx + 1]
        st.session_state["mes_selecionado_global"] = novo_mes
        st.session_state[f"sel_mes_{key_prefix}"] = novo_mes

def ir_mes_proximo(key_prefix):
    idx = LISTA_MESES_ORDENADA.index(st.session_state["mes_selecionado_global"])
    if idx > 0:
        novo_mes = LISTA_MESES_ORDENADA[idx - 1]
        st.session_state["mes_selecionado_global"] = novo_mes
        st.session_state[f"sel_mes_{key_prefix}"] = novo_mes

def ao_mudar_select_mes(key_prefix):
    st.session_state["mes_selecionado_global"] = st.session_state[f"sel_mes_{key_prefix}"]

def renderizar_seletor_mes_Global(key_prefix):
    if f"sel_mes_{key_prefix}" not in st.session_state:
        st.session_state[f"sel_mes_{key_prefix}"] = st.session_state["mes_selecionado_global"]
        
    c_prev, c_label, c_next = st.columns([1, 4.8, 1], vertical_alignment="center")
    with c_prev:
        st.button("", icon=":material/chevron_left:", key=f"btn_prev_{key_prefix}", on_click=ir_mes_anterior, args=(key_prefix,), type="tertiary", use_container_width=True)
    with c_label:
        st.markdown('<span class="month-selector-marker"></span>', unsafe_allow_html=True)
        st.selectbox(
            "Mês",
            options=LISTA_MESES_ORDENADA,
            format_func=lambda x: formatar_mes_extenso(x),
            key=f"sel_mes_{key_prefix}",
            on_change=ao_mudar_select_mes,
            args=(key_prefix,),
            label_visibility="collapsed"
        )
    with c_next:
        st.button("", icon=":material/chevron_right:", key=f"btn_next_{key_prefix}", on_click=ir_mes_proximo, args=(key_prefix,), type="tertiary", use_container_width=True)

# --- POPUP DE CONFIRMAÇÃO DE EXCLUSÃO (ACIONADO PELA LIXEIRA) ---
@st.dialog("Confirmar Exclusão", width="small")
def modal_confirmar_exclusao(tx_id, desc_tx, val_tx, tipo_tx):
    st.markdown("### Excluir Lançamento?")
    sinal = "-" if tipo_tx == "despesa" else "+"
    st.write(f"Tem certeza que deseja apagar **\"{desc_tx}\"** ({sinal} R$ {float(val_tx):,.2f})?")
    st.caption("⚠️ Esta ação não pode ser desfeita.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("Cancelar", key=f"btn_cancel_{tx_id}", use_container_width=True):
            st.rerun()
    with col_c2:
        if st.button("Sim, Excluir", key=f"btn_del_conf_{tx_id}", type="primary", use_container_width=True):
            excluir_transacao(tx_id)
            st.toast("Transação excluída com sucesso!", icon=":material/delete:")
            st.rerun()

# --- MODAL DE EDIÇÃO INDIVIDUAL (ACIONADO PELO LÁPIS) ---
@st.dialog("Editar Transação", width="medium")
def exibir_modal_editar_unica(row_data):
    st.caption(f"Editando lançamento #{row_data['id']}")
    with st.form(f"form_edit_tx_{row_data['id']}"):
        nova_desc = st.text_input("Descrição", value=row_data["descricao"])
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            novo_val = st.number_input("Valor (R$)", min_value=0.01, value=float(row_data["valor"]), step=1.0)
            nova_data = st.date_input("Data", pd.to_datetime(row_data["data"]).date(), format="DD/MM/YYYY")
        with col_e2:
            tipos_lista = ["despesa", "receita"]
            idx_tipo = tipos_lista.index(row_data["tipo"]) if row_data["tipo"] in tipos_lista else 0
            novo_tipo = st.selectbox("Tipo", tipos_lista, index=idx_tipo)
            
            idx_cat = CATEGORIAS_DISPONIVEIS.index(row_data["categoria"]) if row_data["categoria"] in CATEGORIAS_DISPONIVEIS else 0
            nova_cat = st.selectbox("Categoria", CATEGORIAS_DISPONIVEIS, index=idx_cat)
            
        metodos_lista = ["Pix", "Crédito", "Débito", "Dinheiro", "Boleto", "Conta Corrente"]
        metodo_atual = row_data.get("metodo_pagamento", "Pix")
        idx_met = metodos_lista.index(metodo_atual) if metodo_atual in metodos_lista else 0
        novo_metodo = st.selectbox("Método de Pagamento", metodos_lista, index=idx_met)
        
        if st.form_submit_button("Salvar Alterações", icon=":material/check:", type="primary"):
            payload_up = {
                "descricao": nova_desc,
                "valor": float(novo_val),
                "data": str(nova_data),
                "tipo": novo_tipo,
                "categoria": nova_cat,
                "metodo_pagamento": novo_metodo
            }
            atualizar_transacao(int(row_data["id"]), payload_up)
            st.success("Lançamento atualizado com sucesso!")
            st.rerun()

# --- MODAL ESTÁVEL DE ADICIONAR TRANSAÇÃO ---
@st.fragment
def renderizar_conteudo_modal_transacao():
    if "modal_modo_entrada" not in st.session_state:
        st.session_state["modal_modo_entrada"] = "Comando Rápido"
    if "modal_sub_comando" not in st.session_state:
        st.session_state["modal_sub_comando"] = "Texto"

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        if st.button("Comando Rápido", icon=":material/bolt:", key="frag_btn_rapido", type="primary" if st.session_state["modal_modo_entrada"] == "Comando Rápido" else "secondary", use_container_width=True):
            st.session_state["modal_modo_entrada"] = "Comando Rápido"
            st.rerun(scope="fragment")
    with col_m2:
        if st.button("Escanear Extrato", icon=":material/description:", key="frag_btn_extrato", type="primary" if st.session_state["modal_modo_entrada"] == "Escanear Extrato" else "secondary", use_container_width=True):
            st.session_state["modal_modo_entrada"] = "Escanear Extrato"
            st.rerun(scope="fragment")
    with col_m3:
        if st.button("Lançamento Manual", icon=":material/edit:", key="frag_btn_manual", type="primary" if st.session_state["modal_modo_entrada"] == "Lançamento Manual" else "secondary", use_container_width=True):
            st.session_state["modal_modo_entrada"] = "Lançamento Manual"
            st.rerun(scope="fragment")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    if st.session_state["modal_modo_entrada"] == "Comando Rápido":
        col_s1, col_s2, _ = st.columns([1.4, 1.4, 3.2])
        with col_s1:
            if st.button("Digitar Frase", icon=":material/chat_bubble:", key="frag_sub_txt", type="primary" if st.session_state["modal_sub_comando"] == "Texto" else "secondary", use_container_width=True):
                st.session_state["modal_sub_comando"] = "Texto"
                st.rerun(scope="fragment")
        with col_s2:
            if st.button("Gravar Voz", icon=":material/mic:", key="frag_sub_aud", type="primary" if st.session_state["modal_sub_comando"] == "Áudio" else "secondary", use_container_width=True):
                st.session_state["modal_sub_comando"] = "Áudio"
                st.rerun(scope="fragment")

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        if st.session_state["modal_sub_comando"] == "Texto":
            st.caption("Dite ou digite:")
            col_t1, col_t2 = st.columns([4, 1.2])
            with col_t1:
                frase_dig = st.text_input("Comando de texto", placeholder="Ex: Paguei 35 reais no almoço no débito hoje...", label_visibility="collapsed", key="frag_in_txt")
            with col_t2:
                btn_lancar_txt = st.button("Lançar com IA", icon=":material/send:", key="frag_go_txt", type="primary", use_container_width=True)
            
            if btn_lancar_txt and frase_dig.strip():
                with st.spinner("Processando..."):
                    ok, msg = processar_comando_texto(frase_dig)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.warning(msg)

        elif st.session_state["modal_sub_comando"] == "Áudio":
            st.caption("Grave sua mensagem de voz:")
            audio_gravado = st.audio_input("Áudio", label_visibility="collapsed", key="frag_in_aud")
            if audio_gravado is not None and st.button("Processar Áudio com IA", icon=":material/graphic_eq:", key="frag_go_aud", type="primary"):
                with st.spinner("Processando áudio com IA..."):
                    ok, msg = processar_comando_audio(audio_gravado.read(), mime_type="audio/wav")
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.warning(msg)

    elif st.session_state["modal_modo_entrada"] == "Escanear Extrato":
        st.caption("Suba o extrato bancário em PDF ou comprovantes/prints:")
        uploaded_file = st.file_uploader("Arquivo", type=["png", "jpg", "jpeg", "pdf"], label_visibility="collapsed", key="frag_in_file")
        if uploaded_file:
            is_pdf = uploaded_file.name.lower().endswith(".pdf")
            if not is_pdf:
                img_prev = Image.open(uploaded_file)
                st.image(img_prev, width=140)
            else:
                st.info(f"Arquivo PDF carregado: {uploaded_file.name}")
                
            if st.button("Analisar e Extrair Transações", icon=":material/document_scanner:", key="frag_go_doc", type="primary"):
                with st.spinner("IA analisando linhas do documento..."):
                    arquivo_in = uploaded_file.read() if is_pdf else img_prev
                    try:
                        dados = processar_arquivo_extrato(arquivo_in, is_pdf=is_pdf)
                        itens_salvos = 0
                        for it in dados:
                            ok, _ = salvar_no_banco(it)
                            if ok: itens_salvos += 1
                        st.success(f"{itens_salvos} transação(ões) adicionada(s) com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao processar documento: {e}")

    elif st.session_state["modal_modo_entrada"] == "Lançamento Manual":
        with st.form("form_modal_manual_frag"):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                desc = st.text_input("Descrição", placeholder="Ex: Farmácia, Supermercado")
                val_manual = st.text_input("Valor (R$)", value="R$ 0,00", help="Ex: digite 3550 para R$ 35,50")
                data_m = st.date_input("Data", datetime.today(), format="DD/MM/YYYY")
            with col_m2:
                tipo = st.selectbox("Tipo", ["despesa", "receita"])
                categoria = st.selectbox("Categoria", CATEGORIAS_DISPONIVEIS)
                metodo = st.selectbox("Método", ["Pix", "Crédito", "Débito", "Dinheiro", "Boleto"])
            
            if st.form_submit_button("Salvar Transação", icon=":material/check:", type="primary"):
                num_val = parse_moeda_automatica(val_manual)
                if num_val <= 0:
                    st.error("Informe um valor válido.")
                else:
                    payload = {"descricao": desc, "valor": num_val, "data": str(data_m), "tipo": tipo, "categoria": categoria, "metodo_pagamento": metodo}
                    salvar_no_banco(payload)
                    st.success("Transação salva com sucesso!")
                    st.rerun()

@st.dialog("Adicionar Transação", width="large")
def exibir_modal_adicionar_transacao():
    st.caption("Escolha a forma de lançamento:")
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    renderizar_conteudo_modal_transacao()

@st.dialog("Definir Tetos de Orçamento Mensal", width="medium")
def exibir_modal_orcamentos(df_orcamentos_atuais):
    st.caption("Estabeleça o valor máximo que você planeja gastar por categoria no mês.")
    mapa_orcamentos = {row["categoria"]: float(row["valor_teto"]) for _, row in df_orcamentos_atuais.iterrows()} if not df_orcamentos_atuais.empty else {}

    novos_valores = {}
    with st.form("form_orcamentos"):
        for cat in CATEGORIAS_DISPONIVEIS:
            val_atual = mapa_orcamentos.get(cat, 0.0)
            novos_valores[cat] = st.number_input(f"{cat} (R$)", min_value=0.0, value=val_atual, step=50.0)
        
        if st.form_submit_button("Salvar Tetos", icon=":material/save:", type="primary"):
            for cat, val in novos_valores.items():
                if val > 0:
                    salvar_orcamento(cat, val)
            st.success("Orçamentos salvos com sucesso!")
            st.rerun()

@st.dialog("Auditoria Semanal da IA", width="large")
def exibir_modal_auditoria(texto_analise):
    st.markdown(texto_analise)

# Filtragem de Data Global
mes_ativo = st.session_state["mes_selecionado_global"]
df_mes_ativo = df[df['periodo_chave'] == mes_ativo].copy() if not df.empty else pd.DataFrame(columns=["id", "data", "descricao", "valor", "tipo", "categoria", "metodo_pagamento"])
df_uber_mes = df_uber[df_uber['periodo_chave'] == mes_ativo].copy() if not df_uber.empty else pd.DataFrame(columns=["id", "data", "ganho_bruto", "km_rodados", "horas_online", "custo_km_padrao", "outros_gastos"])

# ----------------- ABA 1: VISÃO GERAL -----------------
if aba == "Visão Geral":
    col_t_left, col_t_month, col_t_add = st.columns([2.4, 1.4, 1.2], vertical_alignment="center")
    with col_t_left:
        st.caption(f"• SUA SITUAÇÃO FINANCEIRA  /  {formatar_mes_extenso(mes_ativo, True)}")
        st.markdown("## Seu dinheiro, em foco.")
        st.caption("Visão em tempo real das suas receitas, despesas e distribuição de gastos.")
    with col_t_month:
        renderizar_seletor_mes_Global("vg")
    with col_t_add:
        if st.button("Adicionar transação", icon=":material/add:", type="primary", key="add_vg", use_container_width=True):
            exibir_modal_adicionar_transacao()

    st.markdown("<br>", unsafe_allow_html=True)

    if not df.empty:
        hoje = datetime.today().date()
        semana_atual_chave = f"{hoje.year}-W{hoje.isocalendar()[1]}"
        relatorio_cache = obter_relatorio_semanal(semana_atual_chave)

        if not relatorio_cache:
            sete_dias_atras = hoje - timedelta(days=7)
            df_semana = df[df['data_dt'].dt.date >= sete_dias_atras]
            
            if not df_semana.empty:
                rec_sem = df_semana[df_semana['tipo'] == 'receita']['valor'].sum()
                desp_sem = df_semana[df_semana['tipo'] == 'despesa']['valor'].sum()
                orc_info = f"Tetos orçados: {dict(zip(df_orc['categoria'], df_orc['valor_teto']))}." if not df_orc.empty else ""
                resumo_texto = f"Período: Últimos 7 dias. Receitas: R$ {rec_sem:.2f}. Despesas: R$ {desp_sem:.2f}. {orc_info}"
                resultado_ia = gerar_auditoria_semanal(resumo_texto)
                salvar_relatorio_semanal(semana_atual_chave, resultado_ia["resumo_curto"], resultado_ia["analise_completa"])
                relatorio_cache = resultado_ia

        if relatorio_cache:
            col_ins_txt, col_ins_btn = st.columns([4, 1.2], vertical_alignment="center")
            with col_ins_txt:
                st.markdown(f"""
                <div class="insight-card" style="margin-bottom:0;">
                    <div class="insight-tag">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#5eead4" stroke-width="2"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>
                        INSIGHT SEMANAL DA IA
                    </div>
                    <div class="insight-text">{relatorio_cache['resumo_curto']}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_ins_btn:
                if st.button("Ver diagnóstico", icon=":material/analytics:", key="btn_ver_auditoria", type="secondary", use_container_width=True):
                    exibir_modal_auditoria(relatorio_cache['analise_completa'])

    st.markdown("<br>", unsafe_allow_html=True)

    receitas_mes = df_mes_ativo[df_mes_ativo["tipo"] == "receita"]["valor"].sum() if not df_mes_ativo.empty else 0.0
    despesas_mes = df_mes_ativo[df_mes_ativo["tipo"] == "despesa"]["valor"].sum() if not df_mes_ativo.empty else 0.0
    saldo_mes = receitas_mes - despesas_mes

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Saldo Líquido ({formatar_mes_extenso(mes_ativo)})</div><div class="metric-value metric-highlight">R$ {saldo_mes:,.2f}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Receitas do Mês</div><div class="metric-value">R$ {receitas_mes:,.2f}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Gastos Totais</div><div class="metric-value">R$ {despesas_mes:,.2f}</div></div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.caption("FLUXO DE CAIXA")
        st.markdown("#### Evolução no tempo")
        if not df.empty:
            df_temp = df.copy()
            col_filtro1, col_filtro2 = st.columns([2, 1.2])
            with col_filtro1:
                opcao_periodo = st.selectbox("Período de análise", ["Mês Selecionado", "Últimos 30 dias", "Últimos 7 dias", "Todo o período"], key="filtro_periodo")
            with col_filtro2:
                granularidade = st.selectbox("Intervalo (Escala)", ["Dia", "Semana", "Mês"], index=0, key="filtro_granularidade")

            hoje = datetime.today().date()
            if opcao_periodo == "Mês Selecionado":
                df_filtrado = df_mes_ativo.copy()
            elif opcao_periodo == "Últimos 7 dias":
                df_filtrado = df_temp[df_temp['data_dt'].dt.date >= (hoje - timedelta(days=7))].copy()
            elif opcao_periodo == "Últimos 30 dias":
                df_filtrado = df_temp[df_temp['data_dt'].dt.date >= (hoje - timedelta(days=30))].copy()
            else:
                df_filtrado = df_temp.copy()

            if not df_filtrado.empty:
                if granularidade == "Dia":
                    df_filtrado['periodo_agrupado'] = df_filtrado['data_dt'].dt.strftime('%Y-%m-%d')
                elif granularidade == "Semana":
                    df_filtrado['periodo_agrupado'] = df_filtrado['data_dt'].dt.to_period('W').apply(lambda r: r.start_time.strftime('%Y-%m-%d'))
                else:
                    df_filtrado['periodo_agrupado'] = df_filtrado['data_dt'].dt.strftime('%Y-%m')

                df_fluxo = df_filtrado.groupby(['periodo_agrupado', 'tipo'])['valor'].sum().unstack(fill_value=0).reset_index().sort_values('periodo_agrupado')
                if 'receita' not in df_fluxo.columns: df_fluxo['receita'] = 0.0
                if 'despesa' not in df_fluxo.columns: df_fluxo['despesa'] = 0.0

                fig_fluxo = renderizar_grafico_fluxo(df_fluxo, granularidade)
                st.plotly_chart(fig_fluxo, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Nenhuma transação registrada no período selecionado.")
        else:
            st.info("Insira lançamentos para visualizar o gráfico.")

    col_g1, col_g2 = st.columns([1.2, 1])
    with col_g1:
        with st.container(border=True):
            st.markdown("#### Últimos Lançamentos do Mês")
            if not df_mes_ativo.empty:
                for _, r_vg in df_mes_ativo.head(5).iterrows():
                    cat_v = r_vg.get("categoria", "Outros")
                    svg_v = MAPA_SVGS_CAT.get(cat_v, MAPA_SVGS_CAT["Outros"])
                    sinal = "-" if r_vg["tipo"] == "despesa" else "+"
                    cor_v = "tx-val-despesa" if r_vg["tipo"] == "despesa" else "tx-val-receita"
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; align-items:center; padding: 8px 0; border-bottom: 1px solid #14202c;">
                        <div class="tx-left">
                            <div class="tx-icon-box">{svg_v}</div>
                            <div>
                                <div class="tx-desc">{r_vg['descricao']}</div>
                                <div class="tx-meta">{cat_v} • {formatar_data_br(r_vg['data'])}</div>
                            </div>
                        </div>
                        <div class="{cor_v}">{sinal} R$ {float(r_vg['valor']):,.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Nenhuma transação cadastrada para este mês.")

    with col_g2:
        with st.container(border=True):
            st.markdown("#### Categorias do Mês")
            despesas_mes_df = df_mes_ativo[df_mes_ativo["tipo"] == "despesa"] if not df_mes_ativo.empty else pd.DataFrame()
            if not despesas_mes_df.empty:
                fig_pizza = renderizar_grafico_pizza(despesas_mes_df)
                st.plotly_chart(fig_pizza, use_container_width=True)
            else:
                st.info("Sem despesas para exibir a distribuição neste mês.")

# ----------------- ABA 2: TRANSAÇÕES (ALINHAMENTO RIGOROSO) -----------------
elif aba == "Transações":
    if "limite_transacoes" not in st.session_state:
        st.session_state["limite_transacoes"] = 20

    col_t_left, col_t_month, col_t_add = st.columns([2.4, 1.4, 1.2], vertical_alignment="center")
    with col_t_left:
        st.caption(f"• SUA SITUAÇÃO FINANCEIRA  /  {formatar_mes_extenso(mes_ativo, True)}")
        st.markdown("## Cada movimento, contabilizado.")
        st.caption("Suas receitas e despesas, tudo em um só lugar.")
    with col_t_month:
        renderizar_seletor_mes_Global("tx")
    with col_t_add:
        if st.button("Adicionar transação", icon=":material/add:", type="primary", key="add_tx", use_container_width=True):
            exibir_modal_adicionar_transacao()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    df_tx = df_mes_ativo.copy()
    total_mes = len(df_tx)

    st.markdown(f"""
    <div style="margin-bottom: 6px;">
        <div style="font-size: 0.70rem; font-weight: 700; color: #5eead4; text-transform: uppercase; letter-spacing: 0.1em;">
            REGISTRO DE ATIVIDADES
        </div>
        <div style="font-size: 1.35rem; font-weight: 700; color: #ffffff; display: flex; align-items: center;">
            Transações de {formatar_mes_extenso(mes_ativo).lower()} <span class="count-badge">{total_mes}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        col_f_busca, col_f_tipo, col_f_cat = st.columns([2.6, 1.1, 1.3])
        with col_f_busca:
            busca_termo = st.text_input("Pesquisar", placeholder="Pesquisar transações...", label_visibility="collapsed")
        with col_f_tipo:
            filtro_tipo = st.selectbox("Tipo", ["Todos os tipos", "Apenas Despesas", "Apenas Receitas"], label_visibility="collapsed")
        with col_f_cat:
            filtro_cat = st.selectbox("Categoria", ["Todas as categorias"] + CATEGORIAS_DISPONIVEIS, label_visibility="collapsed")

        if not df_tx.empty:
            if busca_termo.strip():
                df_tx = df_tx[df_tx["descricao"].str.contains(busca_termo.strip(), case=False, na=False)]
            if filtro_tipo == "Apenas Despesas":
                df_tx = df_tx[df_tx["tipo"] == "despesa"]
            elif filtro_tipo == "Apenas Receitas":
                df_tx = df_tx[df_tx["tipo"] == "receita"]
            if filtro_cat != "Todas as categorias":
                df_tx = df_tx[df_tx["categoria"] == filtro_cat]

        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 4px 6px 4px; border-bottom: 1px solid #182838; margin-bottom: 4px;">
            <div style="font-size: 0.72rem; font-weight: 700; color: #52667a; text-transform: uppercase; letter-spacing: 0.1em;">
                TRANSAÇÃO
            </div>
            <div style="font-size: 0.72rem; font-weight: 700; color: #52667a; text-transform: uppercase; letter-spacing: 0.1em; padding-right: 76px;">
                QUANTIA
            </div>
        </div>
        """, unsafe_allow_html=True)

        total_filtradas = len(df_tx)

        if not df_tx.empty:
            df_exibicao = df_tx.head(st.session_state["limite_transacoes"]).copy()
            
            for _, row in df_exibicao.iterrows():
                tx_id = int(row["id"])
                cat = row.get("categoria", "Outros")
                svg_icone = MAPA_SVGS_CAT.get(cat, MAPA_SVGS_CAT["Outros"])
                data_str = formatar_data_br(row["data"])
                desc = row["descricao"]
                val = float(row["valor"])
                tipo_mov = row["tipo"]
                metodo = row.get("metodo_pagamento", "Pix")

                sinal = "-" if tipo_mov == "despesa" else "+"
                css_val = "tx-val-despesa" if tipo_mov == "despesa" else "tx-val-receita"
                val_formatado = f"{sinal} R$ {val:,.2f}"

                # Linha com alinhamento rigoroso
                st.markdown('<span class="tx-row-anchor"></span>', unsafe_allow_html=True)
                c_info, c_val, c_edit, c_del = st.columns([5.8, 2.0, 0.45, 0.45], vertical_alignment="center")
                with c_info:
                    st.markdown(f"""
                    <div class="tx-left">
                        <div class="tx-icon-box">{svg_icone}</div>
                        <div style="min-width: 0;">
                            <div class="tx-desc">{desc}</div>
                            <div class="tx-meta">{cat} • {data_str} • {metodo}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with c_val:
                    st.markdown(f'<div class="{css_val}">{val_formatado}</div>', unsafe_allow_html=True)
                with c_edit:
                    if st.button("", icon=":material/edit:", key=f"ed_tx_{tx_id}", type="tertiary", help="Editar transação", use_container_width=True):
                        exibir_modal_editar_unica(row)
                with c_del:
                    if st.button("", icon=":material/delete:", key=f"del_tx_{tx_id}", type="tertiary", help="Excluir transação", use_container_width=True):
                        modal_confirmar_exclusao(tx_id, desc, val, tipo_mov)

                st.markdown('<div class="tx-divider"></div>', unsafe_allow_html=True)

            if total_filtradas > st.session_state["limite_transacoes"]:
                st.markdown("<br>", unsafe_allow_html=True)
                col_p1, col_p2, col_p3 = st.columns([2, 1.8, 2])
                with col_p2:
                    if st.button("Carregar mais 20 transações", icon=":material/expand_more:", type="secondary", use_container_width=True):
                        st.session_state["limite_transacoes"] += 20
                        st.rerun()
        else:
            st.info("Nenhuma transação encontrada neste mês com os filtros aplicados.")

# ----------------- ABA 3: CONTROLE UBER (GRAVAÇÃO CORRIGIDA) -----------------
elif aba == "Controle Uber":
    col_u_left, col_u_month = st.columns([3.2, 1.8], vertical_alignment="center")
    with col_u_left:
        st.caption(f"• OPERAÇÃO RENDA EXTRA  /  {formatar_mes_extenso(mes_ativo, True)}")
        st.markdown("## Painel de Desempenho Uber")
        st.caption("Acompanhe sua renda líquida real e produtividade por hora no mês.")
    with col_u_month:
        renderizar_seletor_mes_Global("uber")

    st.markdown("<br>", unsafe_allow_html=True)

    total_bruto = df_uber_mes["ganho_bruto"].sum() if not df_uber_mes.empty else 0.0
    total_km = df_uber_mes["km_rodados"].sum() if not df_uber_mes.empty else 0.0
    total_horas = df_uber_mes["horas_online"].sum() if not df_uber_mes.empty else 0.0
    
    custos_totais = ((df_uber_mes["km_rodados"] * df_uber_mes["custo_km_padrao"]).sum() + df_uber_mes["outros_gastos"].sum()) if not df_uber_mes.empty else 0.0
    lucro_liquido_real = total_bruto - custos_totais
    
    lucro_por_hora = (lucro_liquido_real / total_horas) if total_horas > 0 else 0.0
    lucro_por_km = (lucro_liquido_real / total_km) if total_km > 0 else 0.0

    col_u1, col_u2, col_u3, col_u4 = st.columns(4)
    with col_u1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Faturamento Bruto</div><div class="metric-value">R$ {total_bruto:,.2f}</div></div>', unsafe_allow_html=True)
    with col_u2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Lucro Líquido Real</div><div class="metric-value metric-highlight">R$ {lucro_liquido_real:,.2f}</div></div>', unsafe_allow_html=True)
    with col_u3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Rendimento / Hora</div><div class="metric-value">R$ {lucro_por_hora:,.2f}</div></div>', unsafe_allow_html=True)
    with col_u4:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Lucro Líquido / KM</div><div class="metric-value">R$ {lucro_por_km:,.2f}</div></div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### Registrar Diária de Corridas")
        st.caption("Preencha os valores do resumo diário da Uber.")
        
        with st.form("form_diaria_uber"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                data_diaria = st.date_input("Data da Diária", datetime.today(), format="DD/MM/YYYY")
                bruto_txt = st.text_input("Ganhos Brutos (R$)", value="R$ 0,00", help="Ex: digite 12523 para virar R$ 125,23")
                km_txt = st.text_input("Quilômetros Rodados (Km)", placeholder="Ex: 52 ou 52.4")
            with col_f2:
                tempo_txt = st.text_input("Tempo Online", value="0:00 h", help="Ex: digite 110 para virar 1:10 h")
                custo_km_txt = st.text_input("Custo Estimado por KM (R$)", value="R$ 0,45")
                outros_txt = st.text_input("Outros Gastos (R$)", value="R$ 0,00")

            if st.form_submit_button("Salvar Diária e Sincronizar", icon=":material/check:", type="primary"):
                val_bruto = parse_moeda_automatica(bruto_txt)
                km_limpo = "".join([c for c in str(km_txt) if c.isdigit() or c in ",."]).replace(",", ".")
                val_km = float(km_limpo) if km_limpo else 0.0
                val_horas, hora_legivel = parse_hora_automatica(tempo_txt)
                val_custo_km = parse_moeda_automatica(custo_km_txt)
                val_outros = parse_moeda_automatica(outros_txt)

                if val_bruto <= 0:
                    st.error("Informe um ganho bruto válido superior a zero.")
                else:
                    payload_uber = {
                        "data": str(data_diaria),
                        "ganho_bruto": float(val_bruto),
                        "km_rodados": float(val_km),
                        "horas_online": float(val_horas),
                        "custo_km_padrao": float(val_custo_km),
                        "outros_gastos": float(val_outros)
                    }
                    try:
                        salvar_diaria_uber(payload_uber)
                        st.success(f"Diária registrada com sucesso: {hora_legivel} | R$ {val_bruto:,.2f}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar diária no banco: {e}")

    with st.container(border=True):
        st.markdown(f"#### Histórico de Diárias ({formatar_mes_extenso(mes_ativo)})")
        st.caption("Dê um duplo clique nas células para alterar valores ou selecione a linha para excluir.")
        
        if not df_uber_mes.empty:
            df_uber_editavel = df_uber_mes[["id", "data", "ganho_bruto", "km_rodados", "horas_online", "custo_km_padrao", "outros_gastos"]].copy()
            df_uber_editavel["data"] = pd.to_datetime(df_uber_editavel["data"]).dt.date
            df_uber_editavel["ganho_bruto"] = df_uber_editavel["ganho_bruto"].astype(float)
            df_uber_editavel["km_rodados"] = df_uber_editavel["km_rodados"].astype(float)
            df_uber_editavel["horas_online"] = df_uber_editavel["horas_online"].astype(float)
            df_uber_editavel["custo_km_padrao"] = df_uber_editavel["custo_km_padrao"].astype(float)
            df_uber_editavel["outros_gastos"] = df_uber_editavel["outros_gastos"].astype(float)

            st.data_editor(
                df_uber_editavel,
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY", required=True),
                    "ganho_bruto": st.column_config.NumberColumn("Bruto (R$)", format="R$ %.2f", min_value=0.01, required=True),
                    "km_rodados": st.column_config.NumberColumn("Km", format="%.1f km", min_value=0.1, required=True),
                    "horas_online": st.column_config.NumberColumn("Horas", format="%.2f h", min_value=0.1, required=True),
                    "custo_km_padrao": st.column_config.NumberColumn("Custo/Km (R$)", format="R$ %.2f", min_value=0.01, required=True),
                    "outros_gastos": st.column_config.NumberColumn("Outros (R$)", format="R$ %.2f", min_value=0.0, required=True)
                },
                key="editor_diarias_uber"
            )

            if st.button("Salvar Alterações nas Diárias", icon=":material/save:", type="secondary"):
                alteracoes_uber = st.session_state.get("editor_diarias_uber", {})
                for idx in alteracoes_uber.get("deleted_rows", []):
                    excluir_diaria_uber(int(df_uber_editavel.iloc[idx]["id"]))

                for idx, campos in alteracoes_uber.get("edited_rows", {}).items():
                    id_edit = int(df_uber_editavel.iloc[idx]["id"])
                    payload_edit = {k: (str(v) if k == "data" else float(v)) for k, v in campos.items()}
                    atualizar_diaria_uber(id_edit, payload_edit)

                st.success("Histórico atualizado com sucesso!")
                st.rerun()
        else:
            st.info("Nenhuma diária cadastrada neste mês.")

# ----------------- ABA 4: ORÇAMENTOS -----------------
elif aba == "Orçamentos":
    col_o_left, col_o_month, col_o_cfg = st.columns([2.4, 1.4, 1.2], vertical_alignment="center")
    with col_o_left:
        st.caption(f"• PLANEJAMENTO MENSAL  /  {formatar_mes_extenso(mes_ativo, True)}")
        st.markdown("## Tetos de Orçamento")
        st.caption("Acompanhe o limite e o consumo planejado para cada categoria.")
    with col_o_month:
        renderizar_seletor_mes_Global("orc")
    with col_o_cfg:
        if st.button("Configurar Tetos", icon=":material/tune:", type="primary", use_container_width=True):
            exibir_modal_orcamentos(df_orc)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        if not df_orc.empty:
            if not df_mes_ativo.empty:
                gastos_categoria = df_mes_ativo[df_mes_ativo['tipo'] == 'despesa'].groupby('categoria')['valor'].sum().to_dict()
            else:
                gastos_categoria = {}

            for _, orc in df_orc.iterrows():
                cat_nome = orc['categoria']
                svg_cat = MAPA_SVGS_CAT.get(cat_nome, MAPA_SVGS_CAT["Outros"])
                teto = float(orc['valor_teto'])
                gasto_atual = float(gastos_categoria.get(cat_nome, 0.0))
                percentual = min(gasto_atual / teto, 1.0) if teto > 0 else 0.0
                
                cor_barra = "#ef4444" if percentual >= 0.90 else ("#f59e0b" if percentual >= 0.70 else "#34d399")

                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top: 12px; margin-bottom: 6px;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <div class="tx-icon-box" style="width:32px; height:32px;">{svg_cat}</div>
                        <span style="font-weight:600; color:#f8fafc;">{cat_nome}</span>
                    </div>
                    <div style="font-size:0.9rem; color:#94a3b8;">
                        <strong style="color:{cor_barra};">R$ {gasto_atual:,.2f}</strong> de R$ {teto:,.2f} ({int(percentual * 100)}%)
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(percentual)
        else:
            st.info("Nenhum orçamento cadastrado. Clique em 'Configurar Tetos' no topo para definir seus limites.")
