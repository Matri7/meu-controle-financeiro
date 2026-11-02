import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client
from google import genai
from google.genai import types
from PIL import Image
import json
from datetime import datetime, timedelta

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
        margin-bottom: 16px;
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
            model='gemini-2.0-flash',
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

    # --- Seção do Gráfico Estilo Google Ads com Filtros de Período e Granularidade ---
    st.markdown("""
    <div class="chart-box">
        <div class="chart-pre-header">A VISÃO GERAL</div>
        <div class="chart-header">Fluxo de caixa ao longo do tempo</div>
        <div class="chart-sub">Personalize o intervalo e a escala de visualização.</div>
    """, unsafe_allow_html=True)

    if not df.empty:
        df_temp = df.copy()
        df_temp['data_dt'] = pd.to_datetime(df_temp['data'])

        # Barra de Controles Estilo Google Ads
        col_filtro1, col_filtro2 = st.columns([2, 1.2])
        
        with col_filtro1:
            opcao_periodo = st.selectbox(
                "Período de análise",
                ["Últimos 30 dias", "Últimos 7 dias", "Este Mês", "Todo o período", "Personalizado"],
                key="filtro_periodo"
            )
        
        with col_filtro2:
            granularidade = st.selectbox(
                "Intervalo (Escala)",
                ["Dia", "Semana", "Mês"],
                index=0,
                key="filtro_granularidade"
            )

        # Definição dos limites de datas com base no seletor
        hoje = datetime.today().date()
        if opcao_periodo == "Últimos 7 dias":
            data_inicio = hoje - timedelta(days=7)
            data_fim = hoje
        elif opcao_periodo == "Últimos 30 dias":
            data_inicio = hoje - timedelta(days=30)
            data_fim = hoje
        elif opcao_periodo == "Este Mês":
            data_inicio = hoje.replace(day=1)
            data_fim = hoje
        elif opcao_periodo == "Todo o período":
            data_inicio = df_temp['data_dt'].min().date()
            data_fim = df_temp['data_dt'].max().date()
        else:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                data_inicio = st.date_input("Início", hoje - timedelta(days=30), format="DD/MM/YYYY")
            with col_d2:
                data_fim = st.date_input("Fim", hoje, format="DD/MM/YYYY")

        # Filtra o DataFrame para o período selecionado
        df_filtrado = df_temp[(df_temp['data_dt'].dt.date >= data_inicio) & (df_temp['data_dt'].dt.date <= data_fim)].copy()

        if not df_filtrado.empty:
            # Aplicação da Granularidade
            if granularidade == "Dia":
                df_filtrado['periodo_agrupado'] = df_filtrado['data_dt'].dt.strftime('%Y-%m-%d')
                formato_rotulo = '%d/%m'
            elif granularidade == "Semana":
                df_filtrado['periodo_agrupado'] = df_filtrado['data_dt'].dt.to_period('W').apply(lambda r: r.start_time.strftime('%Y-%m-%d'))
                formato_rotulo = 'Sem %d/%m'
            else: # Mês
                df_filtrado['periodo_agrupado'] = df_filtrado['data_dt'].dt.strftime('%Y-%m')
                formato_rotulo = '%b/%y'

            df_fluxo = df_filtrado.groupby(['periodo_agrupado', 'tipo'])['valor'].sum().unstack(fill_value=0).reset_index()
            df_fluxo = df_fluxo.sort_values('periodo_agrupado')

            if 'receita' not in df_fluxo.columns:
                df_fluxo['receita'] = 0.0
            if 'despesa' not in df_fluxo.columns:
                df_fluxo['despesa'] = 0.0

            # Formatação dos rótulos do eixo X
            if granularidade == "Mês":
                rotulos_x = [datetime.strptime(p, '%Y-%m').strftime(formato_rotulo) for p in df_fluxo['periodo_agrupado']]
            else:
                rotulos_x = [datetime.strptime(p, '%Y-%m-%d').strftime(formato_rotulo) for p in df_fluxo['periodo_agrupado']]

            fig_fluxo = go.Figure()

            # Linha e área de Renda (Verde Ciano Suave)
            fig_fluxo.add_trace(go.Scatter(
                x=rotulos_x,
                y=df_fluxo['receita'],
                name='Renda',
                mode='lines+markers',
                line=dict(color='#5eead4', width=3, shape='spline'),
                fill='tozeroy',
                fillcolor='rgba(94, 234, 212, 0.07)',
                marker=dict(size=6, color='#5eead4', line=dict(color='#0f172a', width=2)),
                hovertemplate="<b>Renda:</b> R$ %{y:,.2f}<extra></extra>"
            ))

            # Linha e área de Despesas (Lilás / Roxo Suave)
            fig_fluxo.add_trace(go.Scatter(
                x=rotulos_x,
                y=df_fluxo['despesa'],
                name='Despesas',
                mode='lines+markers',
                line=dict(color='#a78bfa', width=3, shape='spline'),
                fill='tozeroy',
                fillcolor='rgba(167, 139, 250, 0.07)',
                marker=dict(size=6, color='#a78bfa', line=dict(color='#0f172a', width=2)),
                hovertemplate="<b>Despesas:</b> R$ %{y:,.2f}<extra></extra>"
            ))

            fig_fluxo.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8', family='Inter, sans-serif'),
                margin=dict(t=15, b=25, l=15, r=15),
                hovermode='x unified',
                hoverlabel=dict(
                    bgcolor='#0f172a',
                    font_size=12,
                    font_color='#f8fafc',
                    bordercolor='#334155'
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(size=12, color='#cbd5e1')
                ),
                xaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    showline=False,
                    tickfont=dict(color='#64748b', size=11)
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='#1e293b',
                    gridwidth=1,
                    zeroline=False,
                    showline=False,
                    tickprefix='R$ ',
                    tickfont=dict(color='#64748b', size=11)
                )
            )

            st.plotly_chart(fig_fluxo, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Nenhuma transação registrada no período selecionado.")
    else:
        st.info("Insira lançamentos para visualizar o gráfico.")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # --- Seção Inferior: Extrato Recente e Categorias ---
    col_g1, col_g2 = st.columns([1.2, 1])
    
    with col_g1:
        st.subheader("Extrato Recente")
        if not df.empty:
            df_exibicao = df[["data", "descricao", "categoria", "tipo", "valor"]].head(5).copy()
            df_exibicao["data"] = df_exibicao["data"].apply(formatar_data_br)
            df_exibicao.rename(columns={
                "data": "Data",
                "descricao": "Descrição",
                "categoria": "Categoria",
                "tipo": "Tipo",
                "valor": "Valor (R$)"
            }, inplace=True)
            
            st.dataframe(
                df_exibicao,
                use_container_width=True,
                hide_index=True
            )
            
            if st.button("🔍 Ver histórico completo"):
                exibir_modal_historico(df)
        else:
            st.info("Nenhuma transação cadastrada ainda.")

    with col_g2:
        st.subheader("Distribuição por Categoria")
        despesas_df = df[df["tipo"] == "despesa"] if not df.empty else pd.DataFrame()
        if not despesas_df.empty:
            fig_pizza = px.pie(
                despesas_df,
                names="categoria",
                values="valor",
                hole=0.65,
                color_discrete_sequence=px.colors.sequential.Tealgrn_r
            )
            fig_pizza.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#cbd5e1",
                showlegend=True,
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig_pizza, use_container_width=True)
        else:
            st.info("Sem despesas para exibir a distribuição.")

# ----------------- ABA 2: ESCANEAR EXTRATO COM GEMINI (IMAGEM OU PDF) -----------------
elif aba == "Escanear Extrato (IA)":
    st.subheader("Leitor Inteligente de Extratos (PDF e Imagens)")
    st.caption("Suba o extrato bancário em PDF do mês ou prints de faturas/comprovantes.")

    if "mensagem_status" in st.session_state and st.session_state["mensagem_status"]:
        tipo_msg = st.session_state["mensagem_status"]["tipo"]
        texto_msg = st.session_state["mensagem_status"]["texto"]
        if tipo_msg == "warning":
            st.warning(texto_msg)
        elif tipo_msg == "success":
            st.success(texto_msg)
        elif tipo_msg == "info":
            st.info(texto_msg)
        
        if st.button("Fechar aviso"):
            st.session_state["mensagem_status"] = None
            st.rerun()

    if "uploader_key" not in st.session_state:
        st.session_state["uploader_key"] = 0

    uploaded_file = st.file_uploader(
        "Escolha o arquivo (PDF, PNG ou JPG)", 
        type=["png", "jpg", "jpeg", "pdf"],
        key=f"uploader_{st.session_state['uploader_key']}"
    )

    if uploaded_file:
        st.session_state["mensagem_status"] = None
        is_pdf = uploaded_file.name.lower().endswith(".pdf")
        
        if not is_pdf:
            img = Image.open(uploaded_file)
            col_img, col_info = st.columns([1, 4])
            with col_img:
                st.image(img, caption="Miniatura", width=110)
            with col_info:
                with st.expander("🔍 Clique aqui para ver a imagem ampliada"):
                    st.image(img, use_container_width=True)
        else:
            st.info(f"📄 Documento PDF carregado: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")

        if st.button("Lançar transação"):
            with st.spinner("Analisando extrato completo com IA... Aguarde alguns instantes."):
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
                    file_bytes = uploaded_file.read()
                    content_part = types.Part.from_bytes(data=file_bytes, mime_type="application/pdf")
                    contents_payload = [content_part, prompt]
                else:
                    contents_payload = [img, prompt]

                try:
                    response = gemini_client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=contents_payload,
                        config=config
                    )
                except Exception:
                    response = gemini_client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=contents_payload,
                        config=config
                    )

                try:
                    dados = json.loads(response.text)
                    if isinstance(dados, dict):
                        dados = [dados]
                    st.session_state["dados_extraidos"] = dados
                    st.toast("Leitura concluída com sucesso!", icon="✅")
                except Exception as e:
                    st.error(f"Erro ao interpretar dados da IA: {e}")

    if "dados_extraidos" in st.session_state and st.session_state["dados_extraidos"]:
        st.markdown("---")
        st.markdown(f"### 📋 Prévia: {len(st.session_state['dados_extraidos'])} Transações Identificadas")
        st.caption("Confira os lançamentos identificados antes de gravar no Supabase.")

        df_previa = pd.DataFrame(st.session_state["dados_extraidos"]).copy()
        df_previa_exibicao = df_previa.copy()
        df_previa_exibicao["data"] = df_previa_exibicao["data"].apply(formatar_data_br)
        df_previa_exibicao.rename(columns={
            "data": "Data",
            "descricao": "Descrição",
            "categoria": "Categoria",
            "tipo": "Tipo",
            "valor": "Valor (R$)",
            "metodo_pagamento": "Método"
        }, inplace=True)
        
        st.dataframe(df_previa_exibicao, use_container_width=True, hide_index=True)

        col_c1, col_c2 = st.columns([1, 4])
        with col_c1:
            if st.button("Confirmar e Salvar"):
                itens_salvos = 0
                itens_duplicados = 0

                for item in st.session_state["dados_extraidos"]:
                    duplicado = supabase.table("transacoes").select("id")\
                        .eq("data", item["data"])\
                        .eq("descricao", item["descricao"])\
                        .eq("valor", item["valor"])\
                        .execute()

                    if duplicado.data and len(duplicado.data) > 0:
                        itens_duplicados += 1
                    else:
                        supabase.table("transacoes").insert(item).execute()
                        itens_salvos += 1

                if itens_salvos > 0 and itens_duplicados == 0:
                    st.session_state["mensagem_status"] = {
                        "tipo": "success",
                        "texto": f"✅ Sucesso! {itens_salvos} transação(ões) salva(s) no banco de dados."
                    }
                elif itens_salvos > 0 and itens_duplicados > 0:
                    st.session_state["mensagem_status"] = {
                        "tipo": "warning",
                        "texto": f"⚠️ {itens_salvos} transação(ões) nova(s) salva(s), e {itens_duplicados} lançamento(s) foram ignorados por já estarem cadastrados."
                    }
                elif itens_duplicados > 0 and itens_salvos == 0:
                    st.session_state["mensagem_status"] = {
                        "tipo": "warning",
                        "texto": f"⚠️ Nenhum item novo: todas as {itens_duplicados} transações deste arquivo já constavam no banco de dados."
                    }

                st.session_state["dados_extraidos"] = []
                st.session_state["uploader_key"] += 1
                st.rerun()

        with col_c2:
            if st.button("Descartar Leitura"):
                st.session_state["dados_extraidos"] = []
                st.session_state["uploader_key"] += 1
                st.session_state["mensagem_status"] = {
                    "tipo": "info",
                    "texto": "ℹ️ Leitura descartada sem salvar nenhuma alteração."
                }
                st.rerun()

# ----------------- ABA 3: LANÇAMENTO RÁPIDO -----------------
elif aba == "Lançamento Rápido":
    st.subheader("Novo Lançamento")
    
    st.markdown("#### 🎙️ Entrada Inteligente com IA")
    st.caption("Fale no gravador ou digite uma frase informal.")
    
    opcao_aba3 = st.radio("Método de entrada:", ["Digitar Texto", "Gravar Áudio"], horizontal=True, key="modo_aba3")

    if opcao_aba3 == "Digitar Texto":
        col_l1, col_l2 = st.columns([4, 1])
        with col_l1:
            frase_manual = st.text_input(
                "Texto livre:",
                placeholder="Ex: Gastei 25 reais no uber hoje de manhã no crédito...",
                key="input_frase_aba3"
            )
        with col_l2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            btn_manual = st.button("Lançar com IA", key="btn_frase_aba3")

        if btn_manual and frase_manual.strip():
            with st.spinner("Processando..."):
                ok, msg = processar_comando_texto(frase_manual)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.warning(msg)

    elif opcao_aba3 == "Gravar Áudio":
        audio_aba3 = st.audio_input("Grave sua mensagem de voz:", key="audio_input_aba3")
        if audio_aba3 is not None:
            if st.button("Processar Áudio", key="btn_proc_audio_aba3"):
                with st.spinner("Processando áudio com IA..."):
                    audio_bytes = audio_aba3.read()
                    ok, msg = processar_comando_audio(audio_bytes, mime_type="audio/wav")
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.warning(msg)

    st.markdown("---")
    
    st.markdown("#### 📝 Lançamento Manual Estruturado")
    with st.form("form_transacao"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            desc = st.text_input("Descrição (Ex: Padaria, Salário)")
            valor = st.number_input("Valor (R$)", min_value=0.01, step=1.00)
            data_t = st.date_input("Data", datetime.today(), format="DD/MM/YYYY")
        with col_f2:
            tipo = st.selectbox("Tipo", ["despesa", "receita"])
            categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Moradia", "Lazer", "Saúde", "Serviços", "Outros"])
            metodo = st.selectbox("Método de Pagamento", ["Pix", "Crédito", "Débito", "Dinheiro"])
        
        submit = st.form_submit_button("Salvar Manualmente")
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
