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
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Cirúrgica e Fiel ao Layout "de bolso ."
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
        margin-left: 0 !important;
        margin-right: auto !important;
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
    
    /* Retângulo da Aba Ativa */
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

    /* Cards e Métricas */
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
    .metric-highlight { color: #10b981; }
    
    .insight-card {
        background: linear-gradient(135deg, #10212f 0%, #0d1822 100%);
        border: 1px solid #1e3a4f;
        border-radius: 16px;
        padding: 16px 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .insight-tag {
        color: #5eead4;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 4px;
    }
    .insight-text {
        font-size: 0.95rem;
        color: #e2e8f0;
        line-height: 1.4;
    }

    /* Item de Transação Estilo Lista Luxo (print de referência) */
    .tx-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 16px;
        border-bottom: 1px solid #14202c;
        transition: background 0.15s ease;
    }
    .tx-row:hover {
        background: #0f1922;
        border-radius: 12px;
    }
    .tx-left {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .tx-icon-box {
        width: 42px;
        height: 42px;
        border-radius: 12px;
        background: #15222e;
        border: 1px solid #1f3347;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.15rem;
    }
    .tx-desc {
        font-size: 0.95rem;
        font-weight: 600;
        color: #f8fafc;
    }
    .tx-meta {
        font-size: 0.78rem;
        color: #64748b;
        margin-top: 2px;
    }
    .tx-val-despesa {
        font-size: 1rem;
        font-weight: 700;
        color: #f1f5f9;
    }
    .tx-val-receita {
        font-size: 1rem;
        font-weight: 700;
        color: #10b981;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #101c27;
        border: 1px solid #1c2e40 !important;
        border-radius: 16px !important;
        padding: 18px !important;
        margin-top: 16px;
        margin-bottom: 20px;
    }

    div.main div.stButton > button:first-child { 
        background-color: #10b981; 
        color: #062419; 
        font-weight: 600; 
        border: none; 
        border-radius: 10px; 
        padding: 10px 22px; 
        transition: all 0.2s ease-in-out; 
    }
    div.main div.stButton > button:first-child:hover { background-color: #059669; color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# Injetor global de máscara de maquininha de cartão
components.html("""
<script>
function attachMasks() {
    try {
        const parentDoc = window.parent.document;
        if (!parentDoc) return;

        const moneyInputs = parentDoc.querySelectorAll('input[aria-label*="Ganhos Brutos"], input[aria-label*="Outros Gastos"], input[aria-label*="Valor (R$)"], input[aria-label*="Custo Estimado"]');
        
        moneyInputs.forEach(input => {
            if (input.dataset.posMask === "true") return;
            input.dataset.posMask = "true";

            input.addEventListener('focus', function() {
                if (!this.value || this.value.trim() === '') {
                    this.value = 'R$ 0,00';
                }
            });

            input.addEventListener('input', function(e) {
                let digitos = this.value.replace(/\\D/g, '');
                if (!digitos) {
                    this.value = 'R$ 0,00';
                } else {
                    let num = (parseInt(digitos, 10) / 100).toFixed(2);
                    let partes = num.split('.');
                    partes[0] = partes[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, '.');
                    this.value = 'R$ ' + partes[0] + ',' + partes[1];
                }
                this.dispatchEvent(new Event('change', { bubbles: true }));
            });
        });

        const timeInputs = parentDoc.querySelectorAll('input[aria-label*="Tempo Online"]');
        timeInputs.forEach(input => {
            if (input.dataset.timeMask === "true") return;
            input.dataset.timeMask = "true";

            input.addEventListener('focus', function() {
                if (!this.value || this.value.trim() === '') {
                    this.value = '0:00 h';
                }
            });

            input.addEventListener('input', function(e) {
                let digitos = this.value.replace(/\\D/g, '');
                if (!digitos) {
                    this.value = '0:00 h';
                } else {
                    let h = 0, m = 0;
                    if (digitos.length <= 2) {
                        m = parseInt(digitos, 10);
                    } else {
                        h = parseInt(digitos.slice(0, -2), 10);
                        m = parseInt(digitos.slice(-2), 10);
                    }
                    h += Math.floor(m / 60);
                    m = m % 60;
                    this.value = h + ':' + (m < 10 ? '0' : '') + m + ' h';
                }
                this.dispatchEvent(new Event('change', { bubbles: true }));
            });
        });

    } catch (e) {
        console.error(e);
    }
}
setInterval(attachMasks, 200);
</script>
""", height=0, width=0)

# Parsing Backend do Python
def parse_moeda_automatica(texto_val):
    if not texto_val:
        return 0.0
    txt = str(texto_val).strip()
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

# Mapa de Ícones para Cada Categoria (Visual E-commerce / Pocketwise)
MAPA_ICONES_CAT = {
    "Alimentação": "🍔",
    "Transporte": "🚗",
    "Moradia": "🏠",
    "Lazer": "🍿",
    "Saúde": "💊",
    "Serviços": "⚡",
    "Outros": "📦"
}

# --- BARRA LATERAL ESTILO "DE BOLSO ." ---
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

# Botões Oficiais da Barra Lateral com Ícones Material Design
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

CATEGORIAS_DISPONIVEIS = ["Alimentação", "Transporte", "Moradia", "Lazer", "Saúde", "Serviços", "Outros"]

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# --- Janela Modal de Nova Transação (Texto, Voz, Extrato ou Manual) ---
@st.dialog("Adicionar Transação", width="large")
def exibir_modal_adicionar_transacao():
    st.caption("Escolha a melhor forma para registrar seu lançamento financeiro:")
    
    metodo_add = st.radio(
        "Forma de entrada:",
        ["Comando Rápido (Texto / Voz)", "Escanear Extrato (IA)", "Lançamento Manual"],
        horizontal=True
    )
    
    if metodo_add == "Comando Rápido (Texto / Voz)":
        st.markdown("<br>", unsafe_allow_html=True)
        sub_tipo = st.radio("Escolha:", ["Digitar Frase", "Gravar Voz"], horizontal=True, label_visibility="collapsed")
        
        if sub_tipo == "Digitar Frase":
            col_t1, col_t2 = st.columns([4, 1.2])
            with col_t1:
                frase_dig = st.text_input("Dite ou digite:", placeholder="Ex: Paguei 35 reais no almoço no débito hoje...")
            with col_t2:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                btn_lancar_txt = st.button("Lançar com IA")
            
            if btn_lancar_txt and frase_dig.strip():
                with st.spinner("Processando..."):
                    ok, msg = processar_comando_texto(frase_dig)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.warning(msg)
                        
        elif sub_tipo == "Gravar Voz":
            audio_gravado = st.audio_input("Grave sua mensagem de voz:")
            if audio_gravado is not None and st.button("Processar Áudio com IA"):
                with st.spinner("Processando áudio..."):
                    ok, msg = processar_comando_audio(audio_gravado.read(), mime_type="audio/wav")
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.warning(msg)

    elif metodo_add == "Escanear Extrato (IA)":
        st.markdown("<br>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Arquivo de fatura ou extrato (PDF, PNG ou JPG)", type=["png", "jpg", "jpeg", "pdf"])
        if uploaded_file:
            is_pdf = uploaded_file.name.lower().endswith(".pdf")
            if not is_pdf:
                img_prev = Image.open(uploaded_file)
                st.image(img_prev, width=140)
            else:
                st.info(f"📄 Arquivo PDF carregado: {uploaded_file.name}")
                
            if st.button("Analisar e Extrair Transações"):
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

    elif metodo_add == "Lançamento Manual":
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("form_modal_manual"):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                desc = st.text_input("Descrição", placeholder="Ex: Farmácia, Supermercado")
                val_manual = st.text_input("Valor (R$)", value="R$ 0,00")
                data_m = st.date_input("Data", datetime.today(), format="DD/MM/YYYY")
            with col_m2:
                tipo = st.selectbox("Tipo", ["despesa", "receita"])
                categoria = st.selectbox("Categoria", CATEGORIAS_DISPONIVEIS)
                metodo = st.selectbox("Método", ["Pix", "Crédito", "Débito", "Dinheiro", "Boleto"])
            
            if st.form_submit_button("Salvar Transação"):
                num_val = parse_moeda_automatica(val_manual)
                if num_val <= 0:
                    st.error("Informe um valor válido.")
                else:
                    payload = {"descricao": desc, "valor": num_val, "data": str(data_m), "tipo": tipo, "categoria": categoria, "metodo_pagamento": metodo}
                    salvar_no_banco(payload)
                    st.success("Transação salva com sucesso!")
                    st.rerun()

@st.dialog("Definir Tetos de Orçamento Mensal", width="medium")
def exibir_modal_orcamentos(df_orcamentos_atuais):
    st.caption("Estabeleça o valor máximo que você planeja gastar por categoria a cada mês.")
    
    mapa_orcamentos = {}
    if not df_orcamentos_atuais.empty:
        for _, row in df_orcamentos_atuais.iterrows():
            mapa_orcamentos[row["categoria"]] = float(row["valor_teto"])

    novos_valores = {}
    with st.form("form_orcamentos"):
        for cat in CATEGORIAS_DISPONIVEIS:
            val_atual = mapa_orcamentos.get(cat, 0.0)
            novos_valores[cat] = st.number_input(f"{cat} (R$)", min_value=0.0, value=val_atual, step=50.0)
        
        btn_salvar_orc = st.form_submit_button("💾 Salvar Tetos")
        if btn_salvar_orc:
            for cat, val in novos_valores.items():
                if val > 0:
                    salvar_orcamento(cat, val)
            st.success("Orçamentos salvos com sucesso!")
            st.rerun()

@st.dialog("Gerenciar e Editar Transações", width="large")
def exibir_modal_historico(dados_completos):
    st.caption("Pode alterar os campos diretamente nas células e carregar no botão abaixo para guardar as alterações.")

    df_editavel = dados_completos[["id", "data", "descricao", "valor", "tipo", "categoria", "metodo_pagamento"]].copy()
    df_editavel["data"] = pd.to_datetime(df_editavel["data"]).dt.date
    df_editavel["valor"] = df_editavel["valor"].astype(float)

    editor_output = st.data_editor(
        df_editavel,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY", required=True),
            "descricao": st.column_config.TextColumn("Descrição", required=True),
            "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0.01, required=True),
            "tipo": st.column_config.SelectboxColumn("Tipo", options=["despesa", "receita"], required=True),
            "categoria": st.column_config.SelectboxColumn("Categoria", options=CATEGORIAS_DISPONIVEIS, required=True),
            "metodo_pagamento": st.column_config.SelectboxColumn("Método", options=["Pix", "Crédito", "Débito", "Dinheiro", "Boleto"], required=True)
        },
        key="editor_transacoes_full"
    )

    if st.button("💾 Salvar Alterações"):
        alteracoes = st.session_state.get("editor_transacoes_full", {})
        linhas_removidas = alteracoes.get("deleted_rows", [])
        for idx in linhas_removidas:
            id_para_excluir = int(df_editavel.iloc[idx]["id"])
            excluir_transacao(id_para_excluir)

        linhas_editadas = alteracoes.get("edited_rows", {})
        if linhas_editadas:
            for idx, campos in linhas_editadas.items():
                id_para_atualizar = int(df_editavel.iloc[idx]["id"])
                dados_novos = {}
                for col, val in campos.items():
                    if col == "data":
                        dados_novos[col] = str(val)
                    elif col == "valor":
                        dados_novos[col] = float(val)
                    else:
                        dados_novos[col] = val
                atualizar_transacao(id_para_atualizar, dados_novos)

            st.success("Transações atualizadas!")
            st.rerun()

@st.dialog("Auditoria Semanal da IA", width="large")
def exibir_modal_auditoria(texto_analise):
    st.markdown(texto_analise)

df = carregar_transacoes()
df_orc = carregar_orcamentos()

# ----------------- ABA 1: VISÃO GERAL -----------------
if aba == "Visão Geral":
    col_titulo, col_mes_filtro = st.columns([3, 1.5])
    with col_titulo:
        st.markdown("## Seu dinheiro, em foco.")
        st.caption("Visão em tempo real das suas receitas, despesas e distribuição de gastos.")
    
    if not df.empty:
        df['data_dt'] = pd.to_datetime(df['data'])
        df['periodo_chave'] = df['data_dt'].dt.strftime('%Y-%m')
        
        mes_atual_chave = datetime.today().strftime('%Y-%m')
        meses_unicos = sorted(list(set(df['periodo_chave'].tolist() + [mes_atual_chave])), reverse=True)
        
        opcoes_meses = {}
        for m in meses_unicos:
            ano, mes_num = m.split('-')
            opcoes_meses[m] = f"{MESES_PT[int(mes_num)]} / {ano}"
        
        with col_mes_filtro:
            st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
            mes_selecionado = st.selectbox(
                "Mês de referência:",
                options=meses_unicos,
                format_func=lambda x: opcoes_meses[x],
                index=meses_unicos.index(mes_atual_chave) if mes_atual_chave in meses_unicos else 0,
                key="filtro_mes_visao_geral"
            )
            
        df_mes_ativo = df[df['periodo_chave'] == mes_selecionado].copy()
    else:
        df_mes_ativo = pd.DataFrame(columns=["id", "data", "descricao", "valor", "tipo", "categoria", "metodo_pagamento"])
        mes_selecionado = datetime.today().strftime('%Y-%m')

    st.markdown("<br>", unsafe_allow_html=True)

    # Auditoria Semanal
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
                cat_top = df_semana[df_semana['tipo'] == 'despesa'].groupby('categoria')['valor'].sum().to_dict()
                
                orc_info = ""
                if not df_orc.empty:
                    orc_map = dict(zip(df_orc['categoria'], df_orc['valor_teto']))
                    orc_info = f"Tetos orçados por categoria: {orc_map}."

                resumo_texto = f"Período: Últimos 7 dias. Receitas: R$ {rec_sem:.2f}. Despesas: R$ {desp_sem:.2f}. Gastos por categoria na semana: {cat_top}. {orc_info}"
                resultado_ia = gerar_auditoria_semanal(resumo_texto)
                salvar_relatorio_semanal(semana_atual_chave, resultado_ia["resumo_curto"], resultado_ia["analise_completa"])
                relatorio_cache = resultado_ia

        if relatorio_cache:
            col_ins_txt, col_ins_btn = st.columns([4, 1.2])
            with col_ins_txt:
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-tag">💡 Insight Semanal da IA</div>
                    <div class="insight-text">{relatorio_cache['resumo_curto']}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_ins_btn:
                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                if st.button("Ver diagnóstico completo", key="btn_ver_auditoria"):
                    exibir_modal_auditoria(relatorio_cache['analise_completa'])

    st.markdown("<br>", unsafe_allow_html=True)

    # Cards de Totais
    receitas_mes = df_mes_ativo[df_mes_ativo["tipo"] == "receita"]["valor"].sum() if not df_mes_ativo.empty else 0.0
    despesas_mes = df_mes_ativo[df_mes_ativo["tipo"] == "despesa"]["valor"].sum() if not df_mes_ativo.empty else 0.0
    saldo_mes = receitas_mes - despesas_mes

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Saldo Líquido ({opcoes_meses.get(mes_selecionado, "")})</div><div class="metric-value metric-highlight">R$ {saldo_mes:,.2f}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Receitas</div><div class="metric-value">R$ {receitas_mes:,.2f}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Gastos Totais</div><div class="metric-value">R$ {despesas_mes:,.2f}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráfico Histórico
    st.markdown('<div class="chart-box"><div class="chart-pre-header">A VISÃO GERAL</div><div class="chart-header">Fluxo de caixa ao longo do tempo</div><div class="chart-sub">Personalize o intervalo e a escala de visualização.</div>', unsafe_allow_html=True)
    if not df.empty:
        df_temp = df.copy()
        col_filtro1, col_filtro2 = st.columns([2, 1.2])
        with col_filtro1:
            opcao_periodo = st.selectbox("Período de análise", ["Últimos 30 dias", "Últimos 7 dias", "Este Mês", "Todo o período", "Personalizado"], key="filtro_periodo")
        with col_filtro2:
            granularidade = st.selectbox("Intervalo (Escala)", ["Dia", "Semana", "Mês"], index=0, key="filtro_granularidade")

        hoje = datetime.today().date()
        if opcao_periodo == "Últimos 7 dias":
            data_inicio, data_fim = hoje - timedelta(days=7), hoje
        elif opcao_periodo == "Últimos 30 dias":
            data_inicio, data_fim = hoje - timedelta(days=30), hoje
        elif opcao_periodo == "Este Mês":
            data_inicio, data_fim = hoje.replace(day=1), hoje
        elif opcao_periodo == "Todo o período":
            data_inicio, data_fim = df_temp['data_dt'].min().date(), df_temp['data_dt'].max().date()
        else:
            col_d1, col_d2 = st.columns(2)
            with col_d1: data_inicio = st.date_input("Início", hoje - timedelta(days=30), format="DD/MM/YYYY")
            with col_d2: data_fim = st.date_input("Fim", hoje, format="DD/MM/YYYY")

        df_filtrado = df_temp[(df_temp['data_dt'].dt.date >= data_inicio) & (df_temp['data_dt'].dt.date <= data_fim)].copy()

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
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_g1, col_g2 = st.columns([1.2, 1])
    with col_g1:
        st.subheader("Extrato do Mês")
        if not df_mes_ativo.empty:
            df_exibicao = df_mes_ativo[["data", "descricao", "categoria", "tipo", "valor"]].head(5).copy()
            df_exibicao["data"] = df_exibicao["data"].apply(formatar_data_br)
            df_exibicao.rename(columns={"data": "Data", "descricao": "Descrição", "categoria": "Categoria", "tipo": "Tipo", "valor": "Valor (R$)"}, inplace=True)
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma transação cadastrada para este mês.")

    with col_g2:
        st.subheader("Categorias do Mês")
        despesas_mes_df = df_mes_ativo[df_mes_ativo["tipo"] == "despesa"] if not df_mes_ativo.empty else pd.DataFrame()
        if not despesas_mes_df.empty:
            fig_pizza = renderizar_grafico_pizza(despesas_mes_df)
            st.plotly_chart(fig_pizza, use_container_width=True)
        else:
            st.info("Sem despesas para exibir a distribuição neste mês.")

# ----------------- ABA 2: TRANSAÇÕES (DESIGN E-COMMERCE / POCKETWISE) -----------------
elif aba == "Transações":
    # Inicializa limite da paginação
    if "limite_transacoes" not in st.session_state:
        st.session_state["limite_transacoes"] = 20

    # Topo idêntico ao print
    col_t_title, col_t_btn = st.columns([3.5, 1.5])
    with col_t_title:
        st.caption("• SUA SITUAÇÃO FINANCEIRA  /  MOVIMENTAÇÕES")
        st.markdown("## Cada movimento, contabilizado.")
        st.caption("Suas receitas e despesas, tudo em um só lugar.")
    with col_t_btn:
        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
        if st.button("➕ Adicionar transação", type="primary", use_container_width=True):
            exibir_modal_adicionar_transacao()

    st.markdown("<br>", unsafe_allow_html=True)

    # Barra de Filtros no estilo do print (Busca + Tipo + Categoria)
    col_f_busca, col_f_tipo, col_f_cat = st.columns([2.5, 1.2, 1.2])
    with col_f_busca:
        busca_termo = st.text_input("Pesquisar", placeholder="🔍 Pesquisar transações...", label_visibility="collapsed")
    with col_f_tipo:
        filtro_tipo = st.selectbox("Tipo", ["Todos os tipos", "Apenas Despesas", "Apenas Receitas"], label_visibility="collapsed")
    with col_f_cat:
        filtro_cat = st.selectbox("Categoria", ["Todas as categorias"] + CATEGORIAS_DISPONIVEIS, label_visibility="collapsed")

    # Aplicação dos Filtros
    df_tx = df.copy()
    if not df_tx.empty:
        if busca_termo.strip():
            df_tx = df_tx[df_tx["descricao"].str.contains(busca_termo.strip(), case=False, na=False)]
        if filtro_tipo == "Apenas Despesas":
            df_tx = df_tx[df_tx["tipo"] == "despesa"]
        elif filtro_tipo == "Apenas Receitas":
            df_tx = df_tx[df_tx["tipo"] == "receita"]
        if filtro_cat != "Todas as categorias":
            df_tx = df_tx[df_tx["categoria"] == filtro_cat]

    st.markdown("<br>", unsafe_allow_html=True)

    # Subcabeçalho de Contagem de Atividades
    total_encontradas = len(df_tx)
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 8px; border-bottom: 1px solid #14202c; margin-bottom: 12px;">
        <div style="font-size: 0.72rem; font-weight: 700; color: #52667a; text-transform: uppercase; letter-spacing: 0.1em;">
            REGISTRO DE ATIVIDADES ({total_encontradas} Lançamentos)
        </div>
        <div style="font-size: 0.75rem; color: #52667a; text-transform: uppercase; letter-spacing: 0.08em;">
            QUANTIA
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not df_tx.empty:
        # Fatiamento no limite atual (Inicia com 20)
        df_exibicao = df_tx.head(st.session_state["limite_transacoes"]).copy()
        
        for _, row in df_exibicao.iterrows():
            cat = row.get("categoria", "Outros")
            icone = MAPA_ICONES_CAT.get(cat, "💳")
            data_str = formatar_data_br(row["data"])
            desc = row["descricao"]
            val = float(row["valor"])
            tipo_mov = row["tipo"]
            metodo = row.get("metodo_pagamento", "Pix")

            # Formatação monetária com sinal
            if tipo_mov == "despesa":
                val_formatado = f"- R$ {val:,.2f}"
                css_val = "tx-val-despesa"
            else:
                val_formatado = f"+ R$ {val:,.2f}"
                css_val = "tx-val-receita"

            st.markdown(f"""
            <div class="tx-row">
                <div class="tx-left">
                    <div class="tx-icon-box">{icone}</div>
                    <div>
                        <div class="tx-desc">{desc}</div>
                        <div class="tx-meta">{cat} • {data_str} • {metodo}</div>
                    </div>
                </div>
                <div class="{css_val}">{val_formatado}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Botão de Paginação E-commerce: Carregar mais 20
        col_p1, col_p2, col_p3 = st.columns([2, 1.5, 2])
        with col_p2:
            if total_encontradas > st.session_state["limite_transacoes"]:
                if st.button(f"⬇️ Carregar mais 20 transações", use_container_width=True):
                    st.session_state["limite_transacoes"] += 20
                    st.rerun()
            else:
                st.caption(f"Mostrando todas as {total_encontradas} transações.")
                
        # Ação para gerenciar/editar linhas
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✏️ Abrir editor de planilhas para alterações em massa"):
            exibir_modal_historico(df)
    else:
        st.info("Nenhuma transação encontrada com os filtros aplicados.")

# ----------------- ABA 3: CONTROLE UBER (RENDA EXTRA) -----------------
elif aba == "Controle Uber":
    st.markdown("## 🚗 Painel de Desempenho Uber")
    st.caption("Acompanhe sua renda líquida real, eficiência por km e produtividade por hora.")
    st.markdown("<br>", unsafe_allow_html=True)

    df_uber = carregar_diarias_uber()

    # Métricas Consolidadas
    if not df_uber.empty:
        total_bruto = df_uber["ganho_bruto"].sum()
        total_km = df_uber["km_rodados"].sum()
        total_horas = df_uber["horas_online"].sum()
        
        custos_totais = (df_uber["km_rodados"] * df_uber["custo_km_padrao"]).sum() + df_uber["outros_gastos"].sum()
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

    # Formulário com Máscara Estilo Maquininha
    with st.container(border=True):
        st.markdown("### 📝 Registrar Diária de Corridas")
        st.caption("Digite apenas os números. O campo formata automaticamente como uma maquininha de cartão.")
        
        with st.form("form_diaria_uber"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                data_diaria = st.date_input("Data da Diária", datetime.today(), format="DD/MM/YYYY")
                bruto_txt = st.text_input("Ganhos Brutos (R$)", value="R$ 0,00", help="Ex: digite 12523 para virar R$ 125,23.")
                km_txt = st.text_input("Quilômetros Rodados (Km)", placeholder="Ex: 52 ou 52.4")
            with col_f2:
                tempo_txt = st.text_input("Tempo Online", value="0:00 h", help="Ex: digite 110 para virar 1:10 h.")
                custo_km_txt = st.text_input("Custo Estimado por KM (R$)", value="R$ 0,45")
                outros_txt = st.text_input("Outros Gastos (R$)", value="R$ 0,00")

            btn_salvar_diaria = st.form_submit_button("💾 Salvar Diária e Sincronizar com FinSmart")
            if btn_salvar_diaria:
                val_bruto = parse_moeda_automatica(bruto_txt)
                val_km = float(km_txt.replace(",", ".")) if km_txt.strip() else 0.0
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
                        "outros_gastos": float(val_outros),
                        "observacao": f"Tempo: {hora_legivel}"
                    }
                    salvar_diaria_uber(payload_uber)
                    st.success(f"Diária registrada com sucesso: {hora_legivel} | R$ {val_bruto:,.2f}")
                    st.rerun()

    # Histórico de Diárias
    st.markdown("### 📋 Histórico e Edição de Diárias")
    st.caption("Dê um duplo clique para alterar qualquer número ou selecione a linha para excluir.")
    
    if not df_uber.empty:
        df_uber_editavel = df_uber[["id", "data", "ganho_bruto", "km_rodados", "horas_online", "custo_km_padrao", "outros_gastos"]].copy()
        df_uber_editavel["data"] = pd.to_datetime(df_uber_editavel["data"]).dt.date
        df_uber_editavel["ganho_bruto"] = df_uber_editavel["ganho_bruto"].astype(float)
        df_uber_editavel["km_rodados"] = df_uber_editavel["km_rodados"].astype(float)
        df_uber_editavel["horas_online"] = df_uber_editavel["horas_online"].astype(float)
        df_uber_editavel["custo_km_padrao"] = df_uber_editavel["custo_km_padrao"].astype(float)
        df_uber_editavel["outros_gastos"] = df_uber_editavel["outros_gastos"].astype(float)

        editor_uber = st.data_editor(
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

        col_uber_btn, _ = st.columns([2, 3])
        with col_uber_btn:
            if st.button("💾 Salvar Alterações nas Diárias"):
                alteracoes_uber = st.session_state.get("editor_diarias_uber", {})
                
                linhas_removidas = alteracoes_uber.get("deleted_rows", [])
                for idx in linhas_removidas:
                    id_remocao = int(df_uber_editavel.iloc[idx]["id"])
                    excluir_diaria_uber(id_remocao)

                linhas_alteradas = alteracoes_uber.get("edited_rows", {})
                if linhas_alteradas:
                    for idx, campos in linhas_alteradas.items():
                        id_edit = int(df_uber_editavel.iloc[idx]["id"])
                        payload_edit = {}
                        for k, v in campos.items():
                            if k == "data":
                                payload_edit[k] = str(v)
                            else:
                                payload_edit[k] = float(v)
                        atualizar_diaria_uber(id_edit, payload_edit)

                st.success("Histórico atualizado com sucesso!")
                st.rerun()
    else:
        st.info("Nenhuma diária cadastrada ainda.")

# ----------------- ABA 4: ORÇAMENTOS -----------------
elif aba == "Orçamentos":
    st.markdown("## 🎯 Tetos de Orçamento Mensal")
    st.caption("Acompanhe o limite e o consumo planejado para cada categoria de despesa.")
    st.markdown("<br>", unsafe_allow_html=True)

    hoje_data = datetime.today().date()
    primeiro_dia_mes = hoje_data.replace(day=1)

    with st.container(border=True):
        col_o_title, col_o_btn = st.columns([3.5, 1.5])
        with col_o_title:
            st.markdown("### Limites do Mês Atual")
            st.caption("Ajuste as metas de gastos para equilibrar suas finanças.")
        with col_o_btn:
            if st.button("⚙️ Configurar Tetos", use_container_width=True):
                exibir_modal_orcamentos(df_orc)

        if not df_orc.empty:
            df_mes_atual = df.copy()
            if not df_mes_atual.empty:
                df_mes_atual['dt'] = pd.to_datetime(df_mes_atual['data']).dt.date
                df_mes_despesas = df_mes_atual[
                    (df_mes_atual['dt'] >= primeiro_dia_mes) & 
                    (df_mes_atual['tipo'] == 'despesa')
                ]
                gastos_categoria = df_mes_despesas.groupby('categoria')['valor'].sum().to_dict()
            else:
                gastos_categoria = {}

            for _, orc in df_orc.iterrows():
                cat_nome = orc['categoria']
                teto = float(orc['valor_teto'])
                gasto_atual = float(gastos_categoria.get(cat_nome, 0.0))
                percentual = min(gasto_atual / teto, 1.0) if teto > 0 else 0.0
                
                if percentual >= 0.90:
                    status_emoji = "🔴"
                elif percentual >= 0.70:
                    status_emoji = "🟡"
                else:
                    status_emoji = "🟢"

                st.write(f"**{status_emoji} {cat_nome}**: R\$ {gasto_atual:,.2f} de R\$ {teto:,.2f} ({int(percentual * 100)}%)")
                st.progress(percentual)
        else:
            st.info("Nenhum orçamento cadastrado. Clique no botão acima para definir seus tetos.")
