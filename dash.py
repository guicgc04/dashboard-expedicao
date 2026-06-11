import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from calculos import carregar_dados, calcular_metricas, resumo_ultimo_dia, META_SEGFEX

st.set_page_config(page_title="Expedição PCG", page_icon="", layout="wide")

st.markdown("""
<style>
    .main { background-color: #ffffff; }
    .block-container { padding-top: 0.5rem; padding-bottom: 0.5rem; }

    .bloco-titulo { font-size: 11px; font-weight: 800; text-transform: uppercase;
                    letter-spacing: 1px; text-align: center; padding: 3px 0 5px 0;
                    border-bottom: 2px solid; margin-bottom: 6px; }
    .bloco-azul  { color: #1f6feb; border-color: #1f6feb; }

    .card { border-radius: 8px; padding: 5px 10px; text-align: center; margin-bottom: 5px; }
    .card-label { font-size: 9px; font-weight: 700; letter-spacing: 1px;
                  text-transform: uppercase; margin-bottom: 1px; }
    .card-value { font-size: 22px; font-weight: 900; line-height: 1.1; }
    .card-unit  { font-size: 9px; margin-top: 1px; }

    .card-azul     { background-color: #e8f0fe; border: 1px solid #4c9eff; }
    .card-azul     .card-label { color: #1a4080; }
    .card-azul     .card-value { color: #1f6feb; }
    .card-vermelho { background-color: #fde8e8; border: 1px solid #e05555; }
    .card-vermelho .card-label { color: #7a1a1a; }
    .card-vermelho .card-value { color: #cc2222; }
    .card-verde    { background-color: #e8fde8; border: 1px solid #55a055; }
    .card-verde    .card-label { color: #1a5a1a; }
    .card-verde    .card-value { color: #228822; }
    .card-laranja  { background-color: #fef0e8; border: 1px solid #d07030; }
    .card-laranja  .card-label { color: #6a2a00; }
    .card-laranja  .card-value { color: #cc5500; }

    .card-represado { background-color: #fefae8; border: 2px solid #c8a020;
                      border-radius: 8px; padding: 7px; text-align: center; margin-top: 4px; }
    .card-represado .rep-label { color: #5a4a00; font-size: 9px; font-weight: 700;
                                  letter-spacing: 1px; text-transform: uppercase; }
    .card-represado .rep-value { color: #b8860b; font-size: 26px; font-weight: 900; }
    .card-represado .rep-unit  { color: #5a4a00; font-size: 9px; }

    .tabela-custom { width: 100%; border-collapse: collapse; font-size: 12px; }
    .tabela-custom th { background-color: #1a3a6b; color: white; padding: 6px 8px;
                        text-align: center; font-weight: 700; font-size: 10px;
                        text-transform: uppercase; letter-spacing: 0.5px; }
    .tabela-custom td { padding: 5px 8px; text-align: center; border-bottom: 1px solid #e8e8e8; }
    .tabela-custom tr:hover td { background-color: #f5f8ff; }
    .tabela-custom tr:nth-child(even) td { background-color: #fafafa; }
    .azul    { color: #1f6feb; font-weight: 700; }
    .vermelho{ color: #cc2222; font-weight: 700; }
    .verde   { color: #228822; font-weight: 700; }
    .cinza   { color: #888888; font-weight: 600; }
    .normal  { color: #333333; }
</style>
""", unsafe_allow_html=True)

CAMINHO_EXCEL = "C:\\Users\\GUICA\\JSL SA\\Data Center JSL Operação GRU - BASE PBI\\CMS+\\Tonelagem\\Junho_DailyTonnageReportAllShift (IMPO).xlsx"

@st.cache_data(ttl=1800)
def obter_dados():
    return calcular_metricas(carregar_dados(CAMINHO_EXCEL))

df = obter_dados()

datas_disponiveis = df['Data'].dt.date.tolist()
data_min = min(datas_disponiveis)
data_max = max(datas_disponiveis)

# ── Título + Filtros + Botão ──────────────────────────────────────────────────
col_tit, col_de, col_ate, col_btn = st.columns([4, 1, 1, 0.3])
with col_tit:
    st.markdown(
        "<h3 style='margin:0; padding:6px 0; font-weight:800; color:#111111; "
        "letter-spacing:1px;'>ACOMPANHAMENTO DIÁRIO — EXPEDIÇÃO (PCG)</h3>",
        unsafe_allow_html=True
    )
with col_de:
    de_data = st.date_input("De", value=data_min, min_value=data_min, max_value=data_max)
with col_ate:
    ate_data = st.date_input("Até", value=data_max, min_value=data_min, max_value=data_max)
with col_btn:
    st.markdown("<div style='padding-top:28px'>", unsafe_allow_html=True)
    if st.button("🔄", use_container_width=True, help="Atualizar"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── Aplica filtro ─────────────────────────────────────────────────────────────
mask = (df['Data'].dt.date >= de_data) & (df['Data'].dt.date <= ate_data)
df_view = df[mask].copy()
df_view['represado_segfex_view'] = df_view['saldo_segfex'].cumsum()

resumo = resumo_ultimo_dia(df_view.assign(represado_segfex=df_view['represado_segfex_view']))

# ── Gráfico ───────────────────────────────────────────────────────────────────
fig = go.Figure()

cores_barras = ['#1f6feb' if d < 5 else '#aaaaaa' for d in df_view['dia_semana']]

fig.add_trace(go.Bar(
    x=df_view['data_label'], y=df_view['realizado'],
    name='Realizado (PCG)', marker_color=cores_barras,
    text=df_view['realizado'].apply(lambda v: f'{v:,}'),
    textposition='outside', textfont=dict(color='#1f6feb', size=13),
    yaxis='y1',
))
fig.add_trace(go.Scatter(
    x=df_view['data_label'], y=[META_SEGFEX] * len(df_view),
    name=f'Meta Diária — {META_SEGFEX:,} PCG',
    mode='lines', line=dict(color='#cc0000', width=2, dash='dash'), yaxis='y1',
))
fig.add_trace(go.Scatter(
    x=df_view['data_label'], y=df_view['represado_segfex_view'],
    name='Represado Acumulado', mode='lines+markers+text',
    line=dict(color='#b8860b', width=2), marker=dict(color='#b8860b', size=5),
    text=df_view['represado_segfex_view'].apply(lambda v: f'{v:,}'),
    textposition='top center', textfont=dict(color='#b8860b', size=12),
    yaxis='y2',
))

fig.update_layout(
    plot_bgcolor='#ffffff', paper_bgcolor='#ffffff', font=dict(color='#111111'),
    legend=dict(orientation='h', y=1.12, x=0.5, xanchor='center',
                bgcolor='rgba(0,0,0,0)', font=dict(size=13)),
    xaxis=dict(gridcolor='#e0e0e0', tickfont=dict(size=12), tickangle=-45),
    yaxis=dict(
        title=dict(text='PCG (Realizado)', font=dict(color='#1f6feb', size=12)),
        tickfont=dict(color='#1f6feb', size=12), gridcolor='#e0e0e0',
    ),
    yaxis2=dict(
        title=dict(text='Represado Acumulado', font=dict(color='#b8860b', size=12)),
        tickfont=dict(color='#b8860b', size=12), overlaying='y', side='right',
        gridcolor='rgba(0,0,0,0)',
    ),
    height=420, margin=dict(t=70, b=50, l=55, r=55), bargap=0.3,
)

st.plotly_chart(fig, use_container_width=True)

# ── Tabela + Cards ────────────────────────────────────────────────────────────
col_tabela, col_cards = st.columns([3, 1])

def formatar_linha(row):
    data      = f'<td class="normal">{row["data_label"]}</td>'
    realizado = f'<td class="azul">{int(row["realizado"]):,}</td>'
    minimo    = f'<td class="normal">{META_SEGFEX:,}</td>'
    dif = int(row["diferenca"])
    dif_str = f'<td class="azul">+{dif:,}</td>' if dif >= 0 else f'<td class="vermelho">{dif:,}</td>'
    sit_str = f'<td class="azul">PASSOU</td>' if "PASSOU" in row["situacao"] else f'<td class="vermelho">FALTOU</td>'
    excedente = f'<td class="normal">{int(row["excedente"]):,}</td>'
    faltam    = f'<td class="vermelho">{int(row["faltam"]):,}</td>' if row["faltam"] > 0 else '<td class="normal">0</td>'
    rep_sf    = f'<td class="azul">{int(row["represado_segfex_view"]):,}</td>'
    return f"<tr>{data}{realizado}{minimo}{dif_str}{sit_str}{excedente}{faltam}{rep_sf}</tr>"

linhas_html = "\n".join(df_view.apply(formatar_linha, axis=1))
tabela_html = f"""
<table class="tabela-custom">
  <thead><tr>
    <th>Data</th><th>Realizado</th><th>Meta Diária</th>
    <th>Diferença</th><th>Situação</th><th>Excedente</th>
    <th>Faltam</th><th>Represado Acumulado</th>
  </tr></thead>
  <tbody>{linhas_html}</tbody>
</table>"""

with col_tabela:
    st.markdown("##### Detalhamento por Dia")
    st.markdown(tabela_html, unsafe_allow_html=True)

with col_cards:
    st.markdown('<div class="bloco-titulo bloco-azul">⚡ Meta Diária — 4.250 PCG</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="card card-azul">
        <div class="card-label">Realizado ({resumo['data']})</div>
        <div class="card-value">{resumo['realizado']:,}</div>
        <div class="card-unit" style="color:#1a4080">PCG</div>
    </div>""", unsafe_allow_html=True)
    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown(f"""
        <div class="card card-vermelho">
            <div class="card-label">Faltam</div>
            <div class="card-value">{resumo['faltam_segfex']:,}</div>
            <div class="card-unit" style="color:#7a1a1a">PCG</div>
        </div>""", unsafe_allow_html=True)
    with cc2:
        cor = "card-verde" if resumo['atingimento_segfex'] >= 100 else "card-laranja"
        st.markdown(f"""
        <div class="card {cor}">
            <div class="card-label">Atingimento</div>
            <div class="card-value">{resumo['atingimento_segfex']}%</div>
            <div class="card-unit">da meta</div>
        </div>""", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="card-represado">
        <div class="rep-label">Represado Acumulado</div>
        <div class="rep-value">{resumo['represado_segfex']:,}</div>
        <div class="rep-unit">PCG</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#555; font-size:11px'>"
    "Meta diária: 4.250 PCG &nbsp;|&nbsp; Todos os dias contam para o represado acumulado"
    "</div>", unsafe_allow_html=True
)