import streamlit as st
import pandas as pd
from PIL import Image
from datetime import datetime, timedelta

from database import (
    supabase, formatar_data_br, carregar_transacoes, salvar_no_banco,
    atualizar_transacao, excluir_transacao,
    carregar_orcamentos, salvar_orcamento,
    obter_relatorio_semanal, salvar_relatorio_semanal
)
from ai_service import (
    processar_comando_texto, processar_comando_audio, processar_arquivo_extrato,
    gerar_auditoria_semanal
)
from charts import renderizar_grafico_fluxo, renderizar_grafico_pizza

st.set_page_config(
    page_title="FinSmart | Controle Financeiro",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Pocketwise
st.markdown("""
<style>
    .stApp { background-color: #0b1118; color: #f1f5f9; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #080d13; border-right: 1px solid #162433; }
    
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
    
    .budget-box {
        background: #101c27;
        border: 1px solid #1c2e40;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .budget-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 4px;
    }
    .budget-sub {
        font-size: 0.82rem;
        color: #64748b;
        margin-bottom: 14px;
    }
    
    .chart-box { background: #101c27; border: 1px solid #1c2e40; border-radius: 16px; padding: 20px; margin-top: 20px; }
    .chart-pre-header { color: #5eead4; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px; }
    .chart-header { font-size: 1.25rem; font-weight: 700; color: #ffffff; margin-bottom: 2px; }
    .chart-sub { font-size: 0.85rem; color: #64748b; margin-bottom: 16px; }

    div.stButton > button:first-child { 
        background-color: #10b981; 
        color: #062419; 
        font-weight: 600; 
        border: none; 
        border-radius: 10px; 
        padding: 10px 22px; 
        transition: all 0.2s ease-in-out; 
    }
    div.stButton > button:first-child:hover { background-color: #059669; color: #ffffff; }
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("### 💳 FinSmart")
st.sidebar.caption("Seu orçamento sob foco")
aba = st.sidebar.radio("Navegar", ["Visão Geral", "Escanear Extrato (IA)", "Lançamento Rápido"])

CATEGORIAS_DISPONIVEIS = ["Alimentação", "Transporte", "Moradia", "Lazer", "Saúde", "Serviços", "Outros"]

# Janela modal para configurar os tetos de orçamento
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

# Janela modal com editor interativo corrigido
@st.dialog("Histórico e Gerenciamento de Transações", width="large")
def exibir_modal_historico(dados_completos):
    st.caption("Pode alterar os campos diretamente nas células e carregar no botão abaixo para guardar as alterações.")

    df_editavel = dados_completos[["id", "data", "descricao", "valor", "tipo", "categoria", "metodo_pagamento"]].copy()
    df_editavel["data"] = pd.to_datetime(df_editavel["data"]).dt.date
    df_editavel["valor"] = df_editavel["valor"].astype(float)

    editor_output = st.data_editor(
        df_editavel,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY", required=True),
            "descricao": st.column_config.TextColumn("Descrição", required=True),
            "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0.01, required=True),
            "tipo": st.column_config.SelectboxColumn("Tipo", options=["despesa", "receita"], required=True),
            "categoria": st.column_config.SelectboxColumn("Categoria", options=CATEGORIAS_DISPONIVEIS, required=True),
            "metodo_pagamento": st.column_config.SelectboxColumn("Método", options=["Pix", "Crédito", "Débito", "Dinheiro", "Boleto"], required=True)
        },
        key="editor_transacoes"
    )

    if st.button("💾 Guardar Alterações no Banco"):
        alteracoes = st.session_state.get("editor_transacoes", {})
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

            st.success("Transações atualizadas com sucesso!")
            st.rerun()
        else:
            st.info("Nenhuma alteração foi efetuada nas células.")

@st.dialog("Auditoria e Diagnóstico Semanal da IA", width="large")
def exibir_modal_auditoria(texto_analise):
    st.markdown(texto_analise)

df = carregar_transacoes()
df_orc = carregar_orcamentos()

# ----------------- ABA 1: VISÃO GERAL -----------------
if aba == "Visão Geral":
    st.markdown("## Seu dinheiro, em foco.")
    st.caption("Visão em tempo real das suas receitas, despesas e distribuição de gastos.")
    st.markdown("<br>", unsafe_allow_html=True)

    # --- Seção de Auditoria Semanal Inteligente com Cruzamento de Orçamento ---
    if not df.empty:
        hoje = datetime.today().date()
        semana_atual_chave = f"{hoje.year}-W{hoje.isocalendar()[1]}"
        relatorio_cache = obter_relatorio_semanal(semana_atual_chave)

        if not relatorio_cache:
            df_temp = df.copy()
            df_temp['data_dt'] = pd.to_datetime(df_temp['data'])
            sete_dias_atras = hoje - timedelta(days=7)
            df_semana = df_temp[df_temp['data_dt'].dt.date >= sete_dias_atras]
            
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

    with st.expander("⚡ Lançamento Rápido (Texto ou Gravar Voz)", expanded=False):
        modo_entrada = st.radio("Escolha a forma de entrada:", ["Digitar Frase", "Gravar Áudio"], horizontal=True, key="modo_vg")
        
        if modo_entrada == "Digitar Frase":
            col_txt, col_btn = st.columns([4, 1])
            with col_txt:
                frase_topo = st.text_input("Dite ou digite:", placeholder="Ex: Paguei 35 reais no almoço no débito hoje...", key="input_frase_topo", label_visibility="collapsed")
            with col_btn:
                btn_topo = st.button("Lançar", key="btn_frase_topo")

            if btn_topo and frase_topo.strip():
                with st.spinner("Processando..."):
                    ok, msg = processar_comando_texto(frase_topo)
                    if ok: st.success(msg); st.rerun()
                    else: st.warning(msg)

        elif modo_entrada == "Gravar Áudio":
            audio_vg = st.audio_input("Grave seu comando de voz:", key="audio_input_vg")
            if audio_vg is not None and st.button("Processar Áudio Gravado", key="btn_proc_audio_vg"):
                with st.spinner("Processando áudio com IA..."):
                    ok, msg = processar_comando_audio(audio_vg.read(), mime_type="audio/wav")
                    if ok: st.success(msg); st.rerun()
                    else: st.warning(msg)

    st.markdown("<br>", unsafe_allow_html=True)

    receitas = df[df["tipo"] == "receita"]["valor"].sum() if not df.empty else 0.0
    despesas = df[df["tipo"] == "despesa"]["valor"].sum() if not df.empty else 0.0
    saldo = receitas - despesas

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Saldo Líquido</div><div class="metric-value metric-highlight">R$ {saldo:,.2f}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Receitas</div><div class="metric-value">R$ {receitas:,.2f}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Gastos Totais</div><div class="metric-value">R$ {despesas:,.2f}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Seção de Orçamento do Mês com Barras de Progresso ---
    hoje_data = datetime.today().date()
    primeiro_dia_mes = hoje_data.replace(day=1)
    
    st.markdown("""
    <div class="budget-box">
        <div class="budget-header">🎯 Orçamento do Mês</div>
        <div class="budget-sub">Acompanhe o consumo dos seus tetos planejados para este mês.</div>
    """, unsafe_allow_html=True)

    col_orc_top1, col_orc_top2 = st.columns([4, 1.2])
    with col_orc_top2:
        if st.button("⚙️ Ajustar Tetos"):
            exibir_modal_orcamentos(df_orc)

    if not df_orc.empty:
        # Filtra os gastos do mês corrente
        df_mes_atual = df.copy()
        if not df_mes_atual.empty:
            df_mes_atual['dt'] = pd.to_datetime(df_mes_atual['data']).dt.date
            df_mes_despesas = df_mes_atual[(df_mes_atual['dt'] >= primeiro_dia_mes) & (df_mes_atual['tipo'] == 'despesa')]
            gastos_categoria = df_mes_despesas.groupby('categoria')['valor'].sum().to_dict()
        else:
            gastos_categoria = {}

        for _, orc in df_orc.iterrows():
            cat_nome = orc['categoria']
            teto = float(orc['valor_teto'])
            gasto_atual = float(gastos_categoria.get(cat_nome, 0.0))
            percentual = min(gasto_atual / teto, 1.0) if teto > 0 else 0.0
            
            # Status e cor do progresso
            if percentual >= 0.90:
                status_emoji = "🔴"
            elif percentual >= 0.70:
                status_emoji = "🟡"
            else:
                status_emoji = "🟢"

            st.write(f"**{status_emoji} {cat_nome}**: R$ {gasto_atual:,.2f} de R$ {teto:,.2f} ({int(percentual * 100)}%)")
            st.progress(percentual)
    else:
        st.info("Nenhum teto orçado cadastrado. Clique em '⚙️ Ajustar Tetos' para planejar seus gastos.")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Gráfico Estilo Google Ads
    st.markdown('<div class="chart-box"><div class="chart-pre-header">A VISÃO GERAL</div><div class="chart-header">Fluxo de caixa ao longo do tempo</div><div class="chart-sub">Personalize o intervalo e a escala de visualização.</div>', unsafe_allow_html=True)
    if not df.empty:
        df_temp = df.copy()
        df_temp['data_dt'] = pd.to_datetime(df_temp['data'])
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
        st.subheader("Extrato Recente")
        if not df.empty:
            df_exibicao = df[["data", "descricao", "categoria", "tipo", "valor"]].head(5).copy()
            df_exibicao["data"] = df_exibicao["data"].apply(formatar_data_br)
            df_exibicao.rename(columns={"data": "Data", "descricao": "Descrição", "categoria": "Categoria", "tipo": "Tipo", "valor": "Valor (R$)"}, inplace=True)
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
            if st.button("🔍 Gerenciar / Ver histórico completo"):
                exibir_modal_historico(df)
        else:
            st.info("Nenhuma transação cadastrada ainda.")

    with col_g2:
        st.subheader("Distribuição por Categoria")
        despesas_df = df[df["tipo"] == "despesa"] if not df.empty else pd.DataFrame()
        if not despesas_df.empty:
            fig_pizza = renderizar_grafico_pizza(despesas_df)
            st.plotly_chart(fig_pizza, use_container_width=True)
        else:
            st.info("Sem despesas para exibir a distribuição.")

# ----------------- ABA 2: ESCANEAR EXTRATO COM GEMINI -----------------
elif aba == "Escanear Extrato (IA)":
    st.subheader("Leitor Inteligente de Extratos (PDF e Imagens)")
    st.caption("Suba o extrato bancário em PDF do mês ou prints de faturas/comprovantes.")

    if "mensagem_status" in st.session_state and st.session_state["mensagem_status"]:
        tipo_msg = st.session_state["mensagem_status"]["tipo"]
        texto_msg = st.session_state["mensagem_status"]["texto"]
        if tipo_msg == "warning": st.warning(texto_msg)
        elif tipo_msg == "success": st.success(texto_msg)
        elif tipo_msg == "info": st.info(texto_msg)
        if st.button("Fechar aviso"):
            st.session_state["mensagem_status"] = None
            st.rerun()

    if "uploader_key" not in st.session_state: st.session_state["uploader_key"] = 0

    uploaded_file = st.file_uploader("Escolha o arquivo (PDF, PNG ou JPG)", type=["png", "jpg", "jpeg", "pdf"], key=f"uploader_{st.session_state['uploader_key']}")

    if uploaded_file:
        st.session_state["mensagem_status"] = None
        is_pdf = uploaded_file.name.lower().endswith(".pdf")
        
        if not is_pdf:
            img = Image.open(uploaded_file)
            col_img, col_info = st.columns([1, 4])
            with col_img: st.image(img, caption="Miniatura", width=110)
            with col_info:
                with st.expander("🔍 Clique aqui para ver a imagem ampliada"):
                    st.image(img, use_container_width=True)
        else:
            st.info(f"📄 Documento PDF carregado: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")

        if st.button("Lançar transação"):
            with st.spinner("Analisando extrato com IA... Aguarde alguns instantes."):
                arquivo_entrada = uploaded_file.read() if is_pdf else img
                try:
                    dados = processar_arquivo_extrato(arquivo_entrada, is_pdf=is_pdf)
                    st.session_state["dados_extraidos"] = dados
                    st.toast("Leitura concluída com sucesso!", icon="✅")
                except Exception as e:
                    st.error(f"Erro ao interpretar dados da IA: {e}")

    if "dados_extraidos" in st.session_state and st.session_state["dados_extraidos"]:
        st.markdown("---")
        st.markdown(f"### 📋 Prévia: {len(st.session_state['dados_extraidos'])} Transações Identificadas")
        df_previa = pd.DataFrame(st.session_state["dados_extraidos"]).copy()
        df_previa_exibicao = df_previa.copy()
        df_previa_exibicao["data"] = df_previa_exibicao["data"].apply(formatar_data_br)
        df_previa_exibicao.rename(columns={"data": "Data", "descricao": "Descrição", "categoria": "Categoria", "tipo": "Tipo", "valor": "Valor (R$)", "metodo_pagamento": "Método"}, inplace=True)
        st.dataframe(df_previa_exibicao, use_container_width=True, hide_index=True)

        col_c1, col_c2 = st.columns([1, 4])
        with col_c1:
            if st.button("Confirmar e Salvar"):
                itens_salvos, itens_duplicados = 0, 0
                for item in st.session_state["dados_extraidos"]:
                    ok, _ = salvar_no_banco(item)
                    if ok: itens_salvos += 1
                    else: itens_duplicados += 1

                if itens_salvos > 0 and itens_duplicados == 0:
                    st.session_state["mensagem_status"] = {"tipo": "success", "texto": f"✅ Sucesso! {itens_salvos} transação(ões) salva(s) no banco de dados."}
                elif itens_salvos > 0 and itens_duplicados > 0:
                    st.session_state["mensagem_status"] = {"tipo": "warning", "texto": f"⚠️ {itens_salvos} transação(ões) nova(s) salva(s), e {itens_duplicados} lançamento(s) ignorados por duplicidade."}
                elif itens_duplicados > 0 and itens_salvos == 0:
                    st.session_state["mensagem_status"] = {"tipo": "warning", "texto": f"⚠️ Nenhum item novo: todas as {itens_duplicados} transações já constavam no banco de dados."}

                st.session_state["dados_extraidos"] = []
                st.session_state["uploader_key"] += 1
                st.rerun()

        with col_c2:
            if st.button("Descartar Leitura"):
                st.session_state["dados_extraidos"] = []
                st.session_state["uploader_key"] += 1
                st.session_state["mensagem_status"] = {"tipo": "info", "texto": "ℹ️ Leitura descartada sem salvar nenhuma alteração."}
                st.rerun()

# ----------------- ABA 3: LANÇAMENTO RÁPIDO -----------------
elif aba == "Lançamento Rápido":
    st.subheader("Novo Lançamento")
    st.markdown("#### 🎙️ Entrada Inteligente com IA")
    opcao_aba3 = st.radio("Método de entrada:", ["Digitar Texto", "Gravar Áudio"], horizontal=True, key="modo_aba3")

    if opcao_aba3 == "Digitar Texto":
        col_l1, col_l2 = st.columns([4, 1])
        with col_l1:
            frase_manual = st.text_input("Texto livre:", placeholder="Ex: Gastei 25 reais no uber hoje de manhã no crédito...", key="input_frase_aba3")
        with col_l2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            btn_manual = st.button("Lançar com IA", key="btn_frase_aba3")

        if btn_manual and frase_manual.strip():
            with st.spinner("Processando..."):
                ok, msg = processar_comando_texto(frase_manual)
                if ok: st.success(msg); st.rerun()
                else: st.warning(msg)

    elif opcao_aba3 == "Gravar Áudio":
        audio_aba3 = st.audio_input("Grave sua mensagem de voz:", key="audio_input_aba3")
        if audio_aba3 is not None and st.button("Processar Áudio", key="btn_proc_audio_aba3"):
            with st.spinner("Processando áudio com IA..."):
                ok, msg = processar_comando_audio(audio_aba3.read(), mime_type="audio/wav")
                if ok: st.success(msg); st.rerun()
                else: st.warning(msg)

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
            payload = {"descricao": desc, "valor": valor, "data": str(data_t), "tipo": tipo, "categoria": categoria, "metodo_pagamento": metodo}
            supabase.table("transacoes").insert(payload).execute()
            st.success("Transação salva com sucesso!")
            st.rerun()
