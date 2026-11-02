import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

def renderizar_grafico_fluxo(df_fluxo, granularidade):
    formato_rotulo = '%b/%y' if granularidade == "Mês" else ('Sem %d/%m' if granularidade == "Semana" else '%d/%m')
    
    if granularidade == "Mês":
        rotulos_x = [datetime.strptime(p, '%Y-%m').strftime(formato_rotulo) for p in df_fluxo['periodo_agrupado']]
    else:
        rotulos_x = [datetime.strptime(p, '%Y-%m-%d').strftime(formato_rotulo) for p in df_fluxo['periodo_agrupado']]

    fig = go.Figure()

    # Linha e área de Renda (Verde Ciano)
    fig.add_trace(go.Scatter(
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

    # Linha e área de Despesas (Lilás / Roxo)
    fig.add_trace(go.Scatter(
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

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8', family='Inter, sans-serif'),
        margin=dict(t=15, b=25, l=15, r=15),
        hovermode='x unified',
        hoverlabel=dict(bgcolor='#0f172a', font_size=12, font_color='#f8fafc', bordercolor='#334155'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=12, color='#cbd5e1')),
        xaxis=dict(showgrid=False, zeroline=False, showline=False, tickfont=dict(color='#64748b', size=11)),
        yaxis=dict(showgrid=True, gridcolor='#1e293b', gridwidth=1, zeroline=False, showline=False, tickprefix='R$ ', tickfont=dict(color='#64748b', size=11))
    )
    return fig

def renderizar_grafico_pizza(despesas_df):
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
    return fig
