import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from calculos import carregar_dados, calcular_metricas, resumo_ultimo_dia, META_DIARIA

# ── Configuração da página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Expedição PCG",
    page_icon="📦",
    layout="wide",
)

# ── CSS customizado ───────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #ffffff; }
    .titulo { text-align: center; font-size: 28px; font-weight: 800;
              color: #111111; letter-spacing: 2px; margin-bottom: 4px; }
    .subtitulo { text-align: center; font-size: 13px; color: #888; margin-bottom: 24px; }

    .card { border-radius: 10px; padding: 16px 20px; text-align: center; margin-bottom: 12px; }
    .card-label { font-size: 11px; font-weight: 600; letter-spacing: 1px;
                  text-transform: uppercase; margin-bottom: 4px; }
    .card-value { font-size: 38px; font-weight: 900; line-height: 1.1; }
    .card-unit  { font-size: 12px; margin-top: 2px; }

    .card-azul   { background-color: #e8f0fe; border: 1px solid #4c9eff; }
    .card-azul   .card-label { color: #1a4080; }
    .card-azul   .card-value { color: #1f6feb; }

    .card-vermelho { background-color: #fde8e8; border: 1px solid #e05555; }
    .card-vermelho .card-label { color: #7a1a1a; }
    .card-vermelho .card-value { color: #cc2222; }

    .card-verde  { background-color: #e8fde8; border: 1px solid #55a055; }
    .card-verde  .card-label { color: #1a5a1a; }
    .card-verde  .card-value { color: #228822; }

    .card-amarelo { background-color: #fefae8; border: 1px solid #c8a020; }
    .card-amarelo .card-label { color: #5a4a00; }
    .card-amarelo .card-value { color: #b8860b; }

    .card-laranja { background-color: #fef0e8; border: 1px solid #d07030; }
    .card-laranja .card-label { color: #6a2a00; }
    .card-laranja .card-value { color: #cc5500; }

    .card-represado { background-color: #fefae8; border: 2px solid #c8a020;
                      border-radius: 10px; padding: 20px; text-align: center; margin-top: 12px; }
    .card-represado .card-label { color: #5a4a00; font-size: 12px; font-weight: 700;
                                   letter-spacing: 1px; text-transform: uppercase; }
    .card-represado .card-value { color: #b8860b; font-size: 48px; font-weight: 900; }
    .card-represado .card-unit  { color: #5a4a00; font-size: 13px; }

    .tabela-custom { width: 100%; border-collapse: collapse; font-size: 15px; }
    .tabela-custom th {
        background-color: #1a3a6b; color: white; padding: 10px 12px;
        text-align: center; font-weight: 700; font-size: 13px;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    .tabela-custom td {
        padding: 9px 12px; text-align: center;
        border-bottom: 1px solid #e8e8e8;
    }
    .tabela-custom tr:hover td { background-color: #f5f8ff; }
    .tabela-custom tr:nth-child(even) td { background-color: #fafafa; }

    .azul     { color: #1f6feb; font-weight: 700; }
    .vermelho { color: #cc2222; font-weight: 700; }
    .verde    { color: #228822; font-weight: 700; }
    .cinza    { color: #888888; font-weight: 600; }
    .normal   { color: #333333; }
</style>
""", unsafe_allow_html=True)

# ── Caminho da planilha ───────────────────────────────────────────────────────
CAMINHO_EXCEL = "https://juliosimoes.sharepoint.com/:x:/s/datacenterGRU.ops/IQBhuvTT9gYmQ7SyieYLots_AeO-_4xNfrkO8YDLLWBFRzM?e=fe3dd3"
# ── Leitura com cache (atualiza a cada 30 minutos) ────────────────────────────
@st.cache_data(ttl=1800)
def obter_dados():
    df_raw = carregar_dados(CAMINHO_EXCEL)
    return calcular_metricas(df_raw)

# ── Título + Botão ────────────────────────────────────────────────────────────
col_title, col_btn = st.columns([5, 1])
with col_title:
    st.markdown('<div class="titulo">📦 ACOMPANHAMENTO DIÁRIO — EXPEDIÇÃO (PCG)</div>', unsafe_allow_html=True)
with col_btn:
    if st.button("🔄 Atualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

df = obter_dados()
resumo = resumo_ultimo_dia(df)

st.markdown(
    f'<div class="subtitulo">Última atualização: dados até {resumo["data"]} &nbsp;|&nbsp; '
    f'Atualização automática a cada 30 minutos</div>',
    unsafe_allow_html=True
)

# ── Gráfico principal ─────────────────────────────────────────────────────────
fig = go.Figure()

cores_barras = ['#1f6feb' if d < 5 else '#aaaaaa' for d in df['dia_semana']]
fig.add_trace(go.Bar(
    x=df['data_label'],
    y=df['realizado'],
    name='Realizado (PCG)',
    marker_color=cores_barras,
    text=df['realizado'].apply(lambda v: f'{v:,}'),
    textposition='outside',
    textfont=dict(color='#1f6feb', size=14),
    yaxis='y1',
))

fig.add_trace(go.Scatter(
    x=df['data_label'],
    y=[META_DIARIA] * len(df),
    name=f'Mínimo Diário (Meta) — {META_DIARIA:,} PCG',
    mode='lines',
    line=dict(color='red', width=2, dash='dash'),
    yaxis='y1',
))

fig.add_trace(go.Scatter(
    x=df['data_label'],
    y=df['represado_acumulado'],
    name='Represado Acumulado (PCG)',
    mode='lines+markers+text',
    line=dict(color='#b8860b', width=2),
    marker=dict(color='#b8860b', size=8),
    text=df['represado_acumulado'].apply(lambda v: f'{v:,}'),
    textposition='top center',
    textfont=dict(color='#b8860b', size=13),
    yaxis='y2',
))

fig.update_layout(
    plot_bgcolor='#ffffff',
    paper_bgcolor='#ffffff',
    font=dict(color='#111111'),
    legend=dict(orientation='h', y=1.08, x=0.5, xanchor='center',
                bgcolor='rgba(0,0,0,0)', font=dict(size=12)),
    xaxis=dict(gridcolor='#e0e0e0', tickfont=dict(size=12)),
    yaxis=dict(
        title=dict(text='PCG (Realizado)', font=dict(color='#1f6feb')),
        tickfont=dict(color='#1f6feb'),
        gridcolor='#e0e0e0',
    ),
    yaxis2=dict(
        title=dict(text='PCG (Represado Acumulado)', font=dict(color='#b8860b')),
        tickfont=dict(color='#b8860b'),
        overlaying='y',
        side='right',
        gridcolor='rgba(0,0,0,0)',
    ),
    height=480,
    margin=dict(t=60, b=40, l=60, r=60),
    bargap=0.3,
)

st.plotly_chart(fig, use_container_width=True)

# ── Tabela + Cards lado a lado ────────────────────────────────────────────────
col_tabela, col_cards = st.columns([3, 1])

# ── Tabela colorida ───────────────────────────────────────────────────────────
def formatar_linha(row):
    data      = f'<td class="normal">{row["data_label"]}</td>'
    realizado = f'<td class="azul">{int(row["realizado"]):,}</td>'
    minimo    = f'<td class="normal">{META_DIARIA:,}</td>'

    dif = int(row["diferenca"])
    if row["dia_semana"] >= 5:
        dif_str = f'<td class="cinza">—</td>'
    elif dif >= 0:
        dif_str = f'<td class="azul">+{dif:,}</td>'
    else:
        dif_str = f'<td class="vermelho">{dif:,}</td>'

    if "PASSOU" in row["situacao"]:
        sit_str = f'<td class="azul">PASSOU</td>'
    elif "FDS" in row["situacao"]:
        sit_str = f'<td class="cinza">FDS</td>'
    else:
        sit_str = f'<td class="vermelho">FALTOU</td>'

    excedente = f'<td class="normal">{int(row["excedente"]):,}</td>'
    faltam    = f'<td class="vermelho">{int(row["faltam"]):,}</td>' if row["faltam"] > 0 else f'<td class="normal">0</td>'
    represado = f'<td class="azul">{int(row["represado_acumulado"]):,}</td>'

    return f"<tr>{data}{realizado}{minimo}{dif_str}{sit_str}{excedente}{faltam}{represado}</tr>"

linhas_html = "\n".join(df.apply(formatar_linha, axis=1))

tabela_html = f"""
<table class="tabela-custom">
  <thead>
    <tr>
      <th>Data</th>
      <th>Realizado (PCG)</th>
      <th>Mínimo Diário</th>
      <th>Diferença do Dia</th>
      <th>Situação do Dia</th>
      <th>Excedente do Dia</th>
      <th>Faltam no Dia</th>
      <th>Represado Acumulado</th>
    </tr>
  </thead>
  <tbody>
    {linhas_html}
  </tbody>
</table>
"""

with col_tabela:
    st.markdown("### 📋 Detalhamento por Dia")
    st.markdown(tabela_html, unsafe_allow_html=True)

# ── Cards laterais ────────────────────────────────────────────────────────────
with col_cards:
    st.markdown("<br><br>", unsafe_allow_html=True)

    # Realizado
    st.markdown(f"""
    <div class="card card-azul">
        <div class="card-label">Realizado ({resumo['data']})</div>
        <div class="card-value">{resumo['realizado']:,}</div>
        <div class="card-unit" style="color:#1a4080">PCG</div>
    </div>""", unsafe_allow_html=True)

    # Mínimo Diário
    st.markdown(f"""
    <div class="card card-vermelho">
        <div class="card-label">Mínimo Diário</div>
        <div class="card-value">{resumo['meta']:,}</div>
        <div class="card-unit" style="color:#7a1a1a">PCG</div>
    </div>""", unsafe_allow_html=True)

    # Faltam + Atingimento em duas colunas
    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown(f"""
        <div class="card card-vermelho">
            <div class="card-label">Faltam no Dia</div>
            <div class="card-value" style="font-size:28px">{resumo['faltam']:,}</div>
            <div class="card-unit" style="color:#7a1a1a">PCG</div>
        </div>""", unsafe_allow_html=True)
    with cc2:
        cor = "card-verde" if resumo['atingimento_pct'] >= 100 else "card-laranja"
        st.markdown(f"""
        <div class="card {cor}">
            <div class="card-label">Atingimento</div>
            <div class="card-value" style="font-size:28px">{resumo['atingimento_pct']}%</div>
            <div class="card-unit">da meta</div>
        </div>""", unsafe_allow_html=True)

    # Represado Acumulado — destaque
    st.markdown(f"""
    <div class="card-represado">
        <div class="card-label">🔴 Represado Acumulado</div>
        <div class="card-value">{resumo['represado']:,}</div>
        <div class="card-unit">PCG</div>
    </div>""", unsafe_allow_html=True)

# ── Rodapé ────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#555; font-size:12px'>"
    "Meta diária: 4.250 PCG &nbsp;|&nbsp; Fins de semana: expedição conta como alívio do represado"
    "</div>",
    unsafe_allow_html=True
)