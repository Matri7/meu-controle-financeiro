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

# Estilização CSS Cirúrgica e Totalmente Responsiva
st.markdown("""
<style>
    .stApp { background-color: #0b1118; color: #f1f5f9; font-family: 'Inter', sans-serif; overflow-x: hidden !important; }
    
    /* Previne vazamento horizontal no mobile */
    div[data-testid="stMainBlockContainer"] {
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        overflow-x: hidden !important;
    }

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
    
    /* Retângulo Ativo na Sidebar */
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

    /* BOTÃO PRIMÁRIO VERDE-MENTA */
    button[data-testid="baseButton-primary"],
    button[kind="primary"],
    div.stButton > button[kind="primary"],
    div.stButton > button[data-testid="baseButton-primary"] {
        background-color: #34d399 !important;
        background: #34d399 !important;
        color: #042614 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 8px rgba(52, 211, 153, 0.20) !important;
    }
    button[data-testid="baseButton-primary"] p,
    button[kind="primary"] p,
    button[data-testid="baseButton-primary"] span,
    button[kind="primary"] span {
        color: #042614 !important;
        font-weight: 700 !important;
    }
    button[data-testid="baseButton-primary"]:hover,
    button[kind="primary"]:hover {
        background-color: #10b981 !important;
        background: #10b981 !important;
        color: #ffffff !important;
    }

    /* Botão Secundário e Terciário */
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

    div.main div.stButton > button[kind="tertiary"] {
        background-color: transparent !important;
        color: #64748b !important;
        border: none !important;
        padding: 0 !important;
        min-height: 36px !important;
        border-radius: 6px !important;
    }
    div.main div.stButton > button[kind="tertiary"]:hover {
        background-color: rgba(255, 255, 255, 0.06) !important;
        color: #2dd4bf !important;
    }

    /* ESTILO FIXO DO SELETOR DE MÊS (DESKTOP E MOBILE SEMPRE EM LINHA) */
    .month-picker-row {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: flex-end !important;
        gap: 4px !important;
        width: 100% !important;
    }
    .month-picker-row > div[data-testid="column"]:nth-child(1),
    .month-picker-row > div[data-testid="column"]:nth-child(3) {
        flex: 0 0 36px !important;
        width: 36px !important;
        max-width: 36px !important;
        min-width: 36px !important;
    }
    .month-picker-row > div[data-testid="column"]:nth-child(2) {
        flex: 1 1 auto !important;
        min-width: 140px !important;
    }
    .month-picker-row > div[data-testid="column"] {
        padding-left: 2px !important;
        padding-right: 2px !important;
    }
    .month-picker-row div[data-baseweb="select"] {
        background-color: #101c27 !important;
        border: 1px solid #1e2f40 !important;
        border-radius: 10px !important;
        height: 38px !important;
        min-height: 38px !important;
    }

    /* ESTILO FIXO DA LINHA DE TRANSAÇÕES (DESKTOP E MOBILE SEMPRE EM LINHA) */
    .tx-item-row {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        padding: 8px 0 !important;
        border-bottom: 1px solid #14202c !important;
        gap: 6px !important;
    }
    .tx-item-row > div[data-testid="column"]:nth-child(1) {
        flex: 1 1 auto !important;
        min-width: 0 !important;
        overflow: hidden !important;
    }
    .tx-item-row > div[data-testid="column"]:nth-child(2) {
        flex: 0 0 auto !important;
        min-width: 80px !important;
        text-align: right !important;
        white-space: nowrap !important;
        padding-right: 4px !important;
    }
    .tx-item-row > div[data-testid="column"]:nth-child(3),
    .tx-item-row > div[data-testid="column"]:nth-child(4) {
        flex: 0 0 32px !important;
        width: 32px !important;
        min-width: 32px !important;
        max-width: 32px !important;
    }
    .tx-item-row button {
        width: 32px !important;
        height: 32px !important;
        min-height: 32px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* REGRAS ESPECÍFICAS PARA TELAS MOBILE (<= 768px) */
    @media (max-width: 768px) {
        /* O Streamlit empilha colunas no mobile por padrão. O seletor de mês
           precisa permanecer em uma única linha: seta, mês e seta. */
        div[data-testid="stHorizontalBlock"].month-picker-row,
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3) div[data-testid="stSelectbox"]):has(> div[data-testid="column"]:nth-child(3) button) {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 2px !important;
            width: 100% !important;
        }
        .month-picker-row > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3) div[data-testid="stSelectbox"]):has(> div[data-testid="column"]:nth-child(3) button) > div[data-testid="column"] {
            display: block !important;
            flex-direction: row !important;
            width: auto !important;
            min-width: 0 !important;
        }
        .month-picker-row > div[data-testid="column"]:nth-child(1),
        .month-picker-row > div[data-testid="column"]:nth-child(3),
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3) div[data-testid="stSelectbox"]):has(> div[data-testid="column"]:nth-child(3) button) > div[data-testid="column"]:nth-child(1),
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3) div[data-testid="stSelectbox"]):has(> div[data-testid="column"]:nth-child(3) button) > div[data-testid="column"]:nth-child(3) {
            flex: 0 0 38px !important;
            width: 38px !important;
            max-width: 38px !important;
        }
        .month-picker-row > div[data-testid="column"]:nth-child(2),
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3) div[data-testid="stSelectbox"]):has(> div[data-testid="column"]:nth-child(3) button) > div[data-testid="column"]:nth-child(2) {
            flex: 1 1 auto !important;
            width: auto !important;
            max-width: none !important;
        }
        .month-picker-row div[data-baseweb="select"],
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3) div[data-testid="stSelectbox"]):has(> div[data-testid="column"]:nth-child(3) button) div[data-baseweb="select"] {
            width: 100% !important;
        }
        .month-picker-row button,
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3) div[data-testid="stSelectbox"]):has(> div[data-testid="column"]:nth-child(3) button) button {
            min-width: 34px !important;
            width: 34px !important;
            padding: 0 !important;
        }

        /* Em vez de esconder a descrição e os metadados, a linha passa a
           ocupar duas linhas quando a largura do celular não é suficiente. */
        .tx-item-row {
            flex-wrap: wrap !important;
            align-items: flex-start !important;
            row-gap: 6px !important;
        }
        .tx-item-row > div[data-testid="column"]:nth-child(1) {
            flex: 1 1 100% !important;
            width: 100% !important;
            max-width: 100% !important;
            overflow: visible !important;
        }
        .tx-item-row > div[data-testid="column"]:nth-child(2) {
            flex: 1 1 auto !important;
            min-width: 0 !important;
            text-align: left !important;
            padding-right: 0 !important;
        }
        .tx-item-row > div[data-testid="column"]:nth-child(3),
        .tx-item-row > div[data-testid="column"]:nth-child(4) {
            flex: 0 0 34px !important;
            width: 34px !important;
            min-width: 34px !important;
            max-width: 34px !important;
        }
        .tx-desc,
        .tx-meta {
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
            overflow-wrap: anywhere !important;
        }
    }

    /* Badge de Contagem Verde */
    .count-badge {
        background-color: rgba(45, 212, 191, 0.12);
        color: #2dd4bf;
        border: 1px solid rgba(45, 212, 191, 0.3);
        padding: 2px 9px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-left: 8px;
        vertical-align: middle;
    }

    /* Cards e Métricas */
    .metric-card { 
        background: #101c27; 
        border: 1px solid #1c2e40; 
        border-radius: 16px; 
        padding: 20px; 
        margin-bottom: 16px; 
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25); 
    }
    .metric-title { color: #7b94a8; font-size: 0.80rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
    .metric-value { font-size: 1.80rem; font-weight: 700; color: #f8fafc; }
    .metric-highlight { color: #34d399; }

    /* Itens de Transação */
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
        font-size: 0.90rem;
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
        white-space: nowrap;
    }
    .tx-val-receita {
        font-size: 0.94rem;
        font-weight: 700;
        color: #34d399;
        white-space: nowrap;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #101c27;
        border: 1px solid #1c2e40 !important;
        border-radius: 16px !important;
        padding: 18px !important;
        margin-top: 12px;
        margin-bottom: 20px;
    }

    /* Base visual da V2: dashboard inspirada no PocketWise, mantendo a
       identidade escura e os acentos verde-menta do aplicativo atual. */
    .pw-dashboard-hero {
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, #132b2c 0%, #102027 58%, #101c27 100%);
        border: 1px solid rgba(94, 234, 212, 0.28);
        border-radius: 22px;
        padding: 28px 30px;
        margin: 8px 0 18px;
        box-shadow: 0 16px 36px rgba(0, 0, 0, 0.24);
    }
    .pw-dashboard-hero::after {
        content: "";
        position: absolute;
        width: 240px;
        height: 240px;
        right: -80px;
        top: -100px;
        border-radius: 50%;
        background: rgba(45, 212, 191, 0.12);
        pointer-events: none;
    }
    .pw-eyebrow,
    .pw-section-eyebrow {
        color: #5eead4;
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
    }
    .pw-hero-title {
        color: #e2e8f0;
        font-size: 0.88rem;
        margin-top: 6px;
    }
    .pw-hero-balance {
        color: #f8fafc;
        font-size: clamp(2rem, 5vw, 3.2rem);
        font-weight: 800;
        letter-spacing: -0.04em;
        line-height: 1.05;
        margin: 10px 0 4px;
    }
    .pw-hero-note {
        color: #94a3b8;
        font-size: 0.83rem;
    }
    .pw-progress {
        height: 7px;
        background: rgba(15, 23, 42, 0.72);
        border-radius: 999px;
        margin-top: 20px;
        overflow: hidden;
        max-width: 560px;
    }
    .pw-progress > div {
        height: 100%;
        background: linear-gradient(90deg, #2dd4bf, #34d399);
        border-radius: inherit;
    }
    .pw-card-label {
        color: #7b94a8;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .pw-card-value {
        color: #f8fafc;
        font-size: 1.55rem;
        font-weight: 750;
        margin-top: 7px;
    }
    .pw-card-note {
        color: #64748b;
        font-size: 0.76rem;
        margin-top: 4px;
    }
    .pw-section-heading {
        color: #f8fafc;
        font-size: 1.18rem;
        font-weight: 750;
        margin: 3px 0 0;
    }

    @media (max-width: 768px) {
        .pw-dashboard-hero {
            border-radius: 16px;
            padding: 22px 20px;
        }
        .pw-hero-balance {
            font-size: 2.25rem;
        }
        .pw-card-value {
            font-size: 1.25rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Injetor JS: Fecha a sidebar no mobile e aplica classes nas linhas horizontais
components.html("""
<script>
function setupMobileAndRowEnhancements() {
    try {
        const parentDoc = window.parent.document;
        if (!parentDoc) return;
        const isMobile = window.parent.innerWidth <= 768;

        // 1. Tagging de linhas para garantir flexbox horizontal em qualquer tela
        parentDoc.querySelectorAll('div[data-testid="stHorizontalBlock"]').forEach(block => {
            const hasSelect = block.querySelector('div[data-testid="stSelectbox"]');
            const buttons = block.querySelectorAll('button');
            if (hasSelect && buttons.length === 2 && !block.classList.contains('month-picker-row')) {
                block.classList.add('month-picker-row');
            }

            const icons = block.querySelectorAll('span[data-testid="stIconMaterial"]');
            let isTx = false;
            icons.forEach(ic => {
                if (ic.textContent.includes('edit') || ic.textContent.includes('delete')) isTx = true;
            });
            if (isTx && !block.classList.contains('tx-item-row')) {
                block.classList.add('tx-item-row');
            }
        });

        // 2. Fechamento automático da sidebar no mobile ao clicar em abas
        if (isMobile) {
            const navButtons = parentDoc.querySelectorAll('section[data-testid="stSidebar"] div.stButton > button');
            navButtons.forEach(btn => {
                if (!btn.dataset.autoCloseAttached) {
                    btn.dataset.autoCloseAttached = "true";
                    btn.addEventListener('click', () => {
                        sessionStorage.setItem('just_navigated_mobile', 'true');
                        closeSidebarMobile(parentDoc);
                    });
                }
            });

            if (sessionStorage.getItem('just_navigated_mobile') === 'true') {
                sessionStorage.removeItem('just_navigated_mobile');
                setTimeout(() => { closeSidebarMobile(parentDoc); }, 150);
            }
        }
    } catch(e) {}
}

function closeSidebarMobile(parentDoc) {
    try {
        const backdrop = parentDoc.querySelector('[data-testid="stSidebarBackdrop"]');
        if (backdrop && backdrop.offsetParent !== null) {
            backdrop.click();
            return;
        }
        const closeBtn = parentDoc.querySelector('section[data-testid="stSidebar"] button[data-testid="stBaseButton-header"]') ||
                         parentDoc.querySelector('[data-testid="stSidebarCollapseButton"] button') ||
                         parentDoc.querySelector('button[aria-label="Close sidebar"]') ||
                         parentDoc.querySelector('button[aria-label="Fechar barra lateral"]');
        if (closeBtn) closeBtn.click();
    } catch(e) {}
}

setInterval(setupMobileAndRowEnhancements, 200);
</script>
""", height=0, width=0)

# Parsing Flexível de Moeda e Tempo
def parse_moeda_flexivel(val):
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    txt = str(val).replace("R$", "").replace("r$", "").strip()
    if not txt:
        return 0.0
    if "." in txt and "," in txt:
        txt = txt.replace(".", "").replace(",", ".")
    elif "," in txt:
        txt = txt.replace(",", ".")
    try:
        return float(txt)
    except ValueError:
        digits = "".join(c for c in txt if c.isdigit())
        if digits:
            try:
                return float(digits)
            except ValueError:
                return 0.0
    return 0.0

def parse_hora_flexivel(texto_hora):
    if not texto_hora:
        return 0.0, "0:00 h"
    txt = str(texto_hora).replace("h", "").replace("H", "").strip()
    if ":" in txt:
        partes = txt.split(":")
        h = int(partes[0].strip()) if partes[0].strip().isdigit() else 0
        m = int(partes[1].strip()) if len(partes) > 1 and partes[1].strip().isdigit() else 0
    elif "." in txt:
        try:
            h_dec = float(txt)
            h = int(h_dec)
            m = int((h_dec - h) * 60)
        except ValueError:
            h, m = 0, 0
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

# Ícones Minimalistas em SVG
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

# Carregamento Geral de Dados
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

# Ordem Cronológica: Janeiro -> Dezembro
LISTA_MESES_ORDENADA = sorted(list(meses_disponiveis))

if "mes_selecionado_global" not in st.session_state:
    st.session_state["mes_selecionado_global"] = mes_atual_chave

def formatar_mes_extenso(chave_ym, caixa_alta=False):
    ano, mes = chave_ym.split('-')
    texto = f"{MESES_PT[int(mes)]} de {ano}"
    return texto.upper() if caixa_alta else texto

def trocar_mes_delta(delta):
    idx = LISTA_MESES_ORDENADA.index(st.session_state["mes_selecionado_global"])
    novo_idx = idx + delta
    if 0 <= novo_idx < len(LISTA_MESES_ORDENADA):
        st.session_state["mes_selecionado_global"] = LISTA_MESES_ORDENADA[novo_idx]

def on_select_mes(prefixo):
    st.session_state["mes_selecionado_global"] = st.session_state[f"sel_mes_{prefixo}"]

def renderizar_seletor_mes_Global(key_prefix):
    """Seletor de mês: setas laterais + dropdown no centro com todos os meses do ano"""
    mes_selecionado = st.session_state["mes_selecionado_global"]
    idx_atual = LISTA_MESES_ORDENADA.index(mes_selecionado)
    widget_key = f"sel_mes_{key_prefix}"

    # O selectbox mantém seu próprio valor quando recebe uma key. Sem esta
    # sincronização, clicar nas setas altera os dados exibidos, mas o texto do
    # campo continua mostrando o mês anterior.
    st.session_state[widget_key] = mes_selecionado
    
    col_p, col_sel, col_n = st.columns([1, 6, 1], vertical_alignment="center")
    with col_p:
        if st.button("", icon=":material/chevron_left:", key=f"prev_{key_prefix}", type="tertiary", help="Mês anterior", use_container_width=True):
            if idx_atual > 0:
                trocar_mes_delta(-1)
                st.rerun()
    with col_sel:
        st.selectbox(
            "Mês",
            options=LISTA_MESES_ORDENADA,
            format_func=lambda x: formatar_mes_extenso(x),
            index=idx_atual,
            key=widget_key,
            on_change=on_select_mes,
            args=(key_prefix,),
            label_visibility="collapsed"
        )
    with col_n:
        if st.button("", icon=":material/chevron_right:", key=f"next_{key_prefix}", type="tertiary", help="Próximo mês", use_container_width=True):
            if idx_atual < len(LISTA_MESES_ORDENADA) - 1:
                trocar_mes_delta(1)
                st.rerun()

# --- FUNÇÃO UNIFICADA DE CABEÇALHO PARA TODAS AS ABAS ---
def renderizar_cabecalho_pagina(breadcrumb_texto, titulo, subtitulo, acao_tipo=None, prefix=""):
    st.caption(breadcrumb_texto)
    col_title_box, col_actions_box = st.columns([1.6, 1.4], vertical_alignment="center")
    with col_title_box:
        st.markdown(f"<h2 style='margin:0 0 2px 0; font-size:1.75rem; font-weight:700; color:#fff;'>{titulo}</h2>", unsafe_allow_html=True)
        st.caption(subtitulo)
    with col_actions_box:
        if acao_tipo:
            c_month, c_act = st.columns([1.25, 0.95], vertical_alignment="center")
            with c_month:
                renderizar_seletor_mes_Global(prefix)
            with c_act:
                if acao_tipo == "adicionar":
                    if st.button("Adicionar", icon=":material/add:", type="primary", key=f"btn_add_{prefix}", use_container_width=True):
                        exibir_modal_adicionar_transacao()
                elif acao_tipo == "orcamentos":
                    if st.button("Configurar", icon=":material/tune:", type="primary", key=f"btn_cfg_{prefix}", use_container_width=True):
                        exibir_modal_orcamentos(df_orc)
        else:
            _, c_month = st.columns([0.4, 1.6], vertical_alignment="center")
            with c_month:
                renderizar_seletor_mes_Global(prefix)

# --- MODAIS E DIÁLOGOS ---
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
            tipos = ["despesa", "receita"]
            novo_tipo = st.selectbox("Tipo", tipos, index=tipos.index(row_data["tipo"]) if row_data["tipo"] in tipos else 0)
            nova_cat = st.selectbox("Categoria", CATEGORIAS_DISPONIVEIS, index=CATEGORIAS_DISPONIVEIS.index(row_data["categoria"]) if row_data["categoria"] in CATEGORIAS_DISPONIVEIS else 0)
            
        metodos = ["Pix", "Crédito", "Débito", "Dinheiro", "Boleto", "Conta Corrente"]
        metodo_atual = row_data.get("metodo_pagamento", "Pix")
        novo_metodo = st.selectbox("Método", metodos, index=metodos.index(metodo_atual) if metodo_atual in metodos else 0)
        
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
            st.success("Transação atualizada com sucesso!")
            st.rerun()

@st.dialog("Confirmar Exclusão", width="small")
def exibir_modal_confirmar_exclusao(tx_id, desc_tx):
    st.markdown("### Excluir transação?")
    st.warning("⚠️ Esta ação é definitiva e não poderá ser desfeita.")
    st.write(f"Deseja realmente apagar **'{desc_tx}'**?")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("Cancelar", key=f"cancel_del_{tx_id}", use_container_width=True):
            st.rerun()
    with col_c2:
        if st.button("Sim, Excluir", key=f"confirm_del_{tx_id}", type="primary", use_container_width=True):
            excluir_transacao(tx_id)
            st.success("Transação excluída com sucesso!")
            st.rerun()

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
                btn_lancar_txt = st.button("Lançar com IA", icon=":material/send:", key="frag_go_txt", use_container_width=True)
            
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
            if audio_gravado is not None and st.button("Processar Áudio com IA", icon=":material/graphic_eq:", key="frag_go_aud"):
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
                
            if st.button("Analisar e Extrair Transações", icon=":material/document_scanner:", key="frag_go_doc"):
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
                val_manual = st.text_input("Valor (R$)", placeholder="Ex: 35,50")
                data_m = st.date_input("Data", datetime.today(), format="DD/MM/YYYY")
            with col_m2:
                tipo = st.selectbox("Tipo", ["despesa", "receita"])
                categoria = st.selectbox("Categoria", CATEGORIAS_DISPONIVEIS)
                metodo = st.selectbox("Método", ["Pix", "Crédito", "Débito", "Dinheiro", "Boleto"])
            
            if st.form_submit_button("Salvar Transação", icon=":material/check:", type="primary"):
                num_val = parse_moeda_flexivel(val_manual)
                if num_val <= 0:
                    st.error("Informe um valor válido.")
                else:
                    payload = {"descricao": desc, "valor": num_val, "data": str(data_m), "tipo": tipo, "categoria": categoria, "metodo_pagamento": metodo}
                    salvar_no_banco(payload)
                    st.success("Transação salva com sucesso!")
                    st.rerun()

@st.dialog("Adicionar Transação", width="large")
def exibir_modal_adicionar_transacao():
    st.caption("Escolha a melhor forma para registrar seu lançamento financeiro:")
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    renderizar_conteudo_modal_transacao()

@st.dialog("Definir Tetos de Orçamento Mensal", width="medium")
def exibir_modal_orcamentos(df_orcamentos_atuais):
    st.caption("Estabeleça o valor máximo que você planeja gastar por categoria a cada mês.")
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

# Filtragem de Dados Globais
mes_ativo = st.session_state["mes_selecionado_global"]
df_mes_ativo = df[df['periodo_chave'] == mes_ativo].copy() if not df.empty else pd.DataFrame(columns=["id", "data", "descricao", "valor", "tipo", "categoria", "metodo_pagamento"])
df_uber_mes = df_uber[df_uber['periodo_chave'] == mes_ativo].copy() if not df_uber.empty else pd.DataFrame(columns=["id", "data", "ganho_bruto", "km_rodados", "horas_online", "custo_km_padrao", "outros_gastos"])

# ----------------- ABA 1: VISÃO GERAL -----------------
if aba == "Visão Geral":
    receitas_mes = df_mes_ativo[df_mes_ativo["tipo"] == "receita"]["valor"].sum() if not df_mes_ativo.empty else 0.0
    despesas_mes = df_mes_ativo[df_mes_ativo["tipo"] == "despesa"]["valor"].sum() if not df_mes_ativo.empty else 0.0
    saldo_mes = receitas_mes - despesas_mes
    orcamento_total = float(df_orc["valor_teto"].sum()) if not df_orc.empty else 0.0
    orcamento_restante = orcamento_total - despesas_mes
    percentual_orcamento = min(max((despesas_mes / orcamento_total) * 100, 0), 100) if orcamento_total else 0

    st.caption(f"SUA SITUAÇÃO FINANCEIRA  /  {formatar_mes_extenso(mes_ativo, True)}")
    st.markdown(f"""
    <div class="pw-dashboard-hero">
        <div class="pw-eyebrow">Saldo após despesas</div>
        <div class="pw-hero-title">Uma visão mais clara do seu dinheiro em {formatar_mes_extenso(mes_ativo).lower()}.</div>
        <div class="pw-hero-balance">R$ {saldo_mes:,.2f}</div>
        <div class="pw-hero-note">Receitas menos despesas no mês selecionado</div>
        <div class="pw-progress"><div style="width: {percentual_orcamento:.1f}%;"></div></div>
    </div>
    """, unsafe_allow_html=True)

    c_month, c_act = st.columns([1.25, 0.95], vertical_alignment="center")
    with c_month:
        renderizar_seletor_mes_Global("vg")
    with c_act:
        if st.button("Adicionar", icon=":material/add:", type="primary", key="btn_add_vg_v2", use_container_width=True):
            exibir_modal_adicionar_transacao()

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

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

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="pw-card-label">Receitas</div><div class="pw-card-value">R$ {receitas_mes:,.2f}</div><div class="pw-card-note">Entradas neste mês</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="pw-card-label">Despesas</div><div class="pw-card-value">R$ {despesas_mes:,.2f}</div><div class="pw-card-note">Em todas as categorias</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="pw-card-label">Orçamento restante</div><div class="pw-card-value">R$ {orcamento_restante:,.2f}</div><div class="pw-card-note">{percentual_orcamento:.0f}% do planejado utilizado</div></div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="pw-section-eyebrow">Visão geral</div>', unsafe_allow_html=True)
        st.markdown('<div class="pw-section-heading">Fluxo de caixa ao longo do tempo</div>', unsafe_allow_html=True)
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
            st.markdown('<div class="pw-section-eyebrow">Atividade recente</div>', unsafe_allow_html=True)
            st.markdown('<div class="pw-section-heading">Últimos lançamentos</div>', unsafe_allow_html=True)
            if not df_mes_ativo.empty:
                for _, r_vg in df_mes_ativo.head(5).iterrows():
                    cat_v = r_vg.get("categoria", "Outros")
                    svg_v = MAPA_SVGS_CAT.get(cat_v, MAPA_SVGS_CAT["Outros"])
                    sinal = "-" if r_vg["tipo"] == "despesa" else "+"
                    cor_v = "tx-val-despesa" if r_vg["tipo"] == "despesa" else "tx-val-receita"
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; align-items:center; padding: 6px 0; border-bottom: 1px solid #14202c;">
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
            st.markdown('<div class="pw-section-eyebrow">Para onde foi</div>', unsafe_allow_html=True)
            st.markdown('<div class="pw-section-heading">Distribuição dos gastos</div>', unsafe_allow_html=True)
            despesas_mes_df = df_mes_ativo[df_mes_ativo["tipo"] == "despesa"] if not df_mes_ativo.empty else pd.DataFrame()
            if not despesas_mes_df.empty:
                fig_pizza = renderizar_grafico_pizza(despesas_mes_df)
                st.plotly_chart(fig_pizza, use_container_width=True)
            else:
                st.info("Sem despesas para exibir a distribuição neste mês.")

# ----------------- ABA 2: TRANSAÇÕES (ALINHADA + LÁPIS E LIXEIRA) -----------------
elif aba == "Transações":
    if "limite_transacoes" not in st.session_state:
        st.session_state["limite_transacoes"] = 20

    renderizar_cabecalho_pagina(
        breadcrumb_texto=f"• SUA SITUAÇÃO FINANCEIRA  /  {formatar_mes_extenso(mes_ativo, True)}",
        titulo="Cada movimento, contabilizado.",
        subtitulo="Suas receitas e despesas, tudo em um só lugar.",
        acao_tipo="adicionar",
        prefix="tx"
    )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

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
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 4px; border-bottom: 1px solid #182838; margin-bottom: 4px;">
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

                val_formatado = f"- R$ {val:,.2f}" if tipo_mov == "despesa" else f"+ R$ {val:,.2f}"
                css_val = "tx-val-despesa" if tipo_mov == "despesa" else "tx-val-receita"

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
                    if st.button("", icon=":material/edit:", key=f"ed_tx_{tx_id}", type="tertiary", help="Editar", use_container_width=True):
                        exibir_modal_editar_unica(row)
                with c_del:
                    if st.button("", icon=":material/delete:", key=f"del_tx_{tx_id}", type="tertiary", help="Excluir", use_container_width=True):
                        exibir_modal_confirmar_exclusao(tx_id, desc)

            if total_filtradas > st.session_state["limite_transacoes"]:
                st.markdown("<br>", unsafe_allow_html=True)
                col_p1, col_p2, col_p3 = st.columns([2, 1.8, 2])
                with col_p2:
                    if st.button("Carregar mais 20 transações", icon=":material/expand_more:", type="secondary", use_container_width=True):
                        st.session_state["limite_transacoes"] += 20
                        st.rerun()
        else:
            st.info("Nenhuma transação encontrada neste mês com os filtros aplicados.")

# ----------------- ABA 3: CONTROLE UBER -----------------
elif aba == "Controle Uber":
    renderizar_cabecalho_pagina(
        breadcrumb_texto=f"• OPERAÇÃO RENDA EXTRA  /  {formatar_mes_extenso(mes_ativo, True)}",
        titulo="Painel de Desempenho Uber",
        subtitulo="Acompanhe sua renda líquida real e produtividade por hora no mês.",
        acao_tipo=None,
        prefix="uber"
    )

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
        st.caption("Preencha com os dados do aplicativo.")
        
        with st.form("form_diaria_uber"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                data_diaria = st.date_input("Data da Diária", datetime.today(), format="DD/MM/YYYY")
                bruto_txt = st.text_input("Ganhos Brutos (R$)", placeholder="Ex: 150,00 ou 150")
                km_txt = st.text_input("Quilômetros Rodados (Km)", placeholder="Ex: 52 ou 52.4")
            with col_f2:
                tempo_txt = st.text_input("Tempo Online", placeholder="Ex: 1:25 ou 125")
                custo_km_txt = st.text_input("Custo Estimado por KM (R$)", value="R$ 0,45")
                outros_txt = st.text_input("Outros Gastos (R$)", placeholder="Ex: 10,00 (opcional)")

            if st.form_submit_button("Salvar Diária e Sincronizar", icon=":material/check:", type="primary"):
                val_bruto = parse_moeda_flexivel(bruto_txt)
                val_km = parse_moeda_flexivel(km_txt)
                val_horas, hora_legivel = parse_hora_flexivel(tempo_txt)
                val_custo_km = parse_moeda_flexivel(custo_km_txt) if custo_km_txt.strip() else 0.45
                val_outros = parse_moeda_flexivel(outros_txt)

                if val_bruto <= 0:
                    st.error("Informe um ganho bruto superior a zero.")
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
    renderizar_cabecalho_pagina(
        breadcrumb_texto=f"• PLANEJAMENTO MENSAL  /  {formatar_mes_extenso(mes_ativo, True)}",
        titulo="Tetos de Orçamento",
        subtitulo="Acompanhe o limite e o consumo planejado por categoria.",
        acao_tipo="orcamentos",
        prefix="orc"
    )

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
            st.info("Nenhum orçamento cadastrado. Clique em 'Configurar' no topo para definir seus limites.")
