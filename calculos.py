import io
import requests
import pandas as pd


META_DIARIA = 4250


def carregar_dados(caminho: str) -> pd.DataFrame:
    """Lê o Excel do SharePoint ou caminho local e retorna o DataFrame tratado."""

    if caminho.startswith("http"):
        # Monta URL de download direto do SharePoint
        base = caminho.split("?")[0]
        url_download = base + "?download=1"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/octet-stream",
        }

        resp = requests.get(url_download, headers=headers, allow_redirects=True, timeout=30)
        resp.raise_for_status()
        df = pd.read_excel(io.BytesIO(resp.content), engine="openpyxl")
    else:
        df = pd.read_excel(caminho, engine="openpyxl")

    # Garante que a coluna Data está no formato datetime
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)

    # Ordena por data (importante para o cumsum ficar certo)
    df = df.sort_values('Data').reset_index(drop=True)

    return df


def calcular_metricas(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica todos os cálculos do dashboard sobre o DataFrame."""
    df = df.copy()

    # Coluna de dia da semana: 0=Segunda ... 4=Sexta, 5=Sábado, 6=Domingo
    df['dia_semana'] = df['Data'].dt.dayofweek

    # Realizado do dia (renomeia pra facilitar)
    df['realizado'] = df['Quantidade de PCG Entregue']

    # ---------------------------------------------------------------
    # Saldo do dia
    #   Seg-Sex: 4250 - realizado  (positivo = acumulou, negativo = queimou)
    #   Sab-Dom: 0 - realizado     (tudo que sair é alívio)
    # ---------------------------------------------------------------
    df['saldo_dia'] = df.apply(
        lambda row: META_DIARIA - row['realizado'] if row['dia_semana'] < 5
        else -row['realizado'],
        axis=1
    )

    # Represado acumulado = soma cumulativa dos saldos
    df['represado_acumulado'] = df['saldo_dia'].cumsum()

    # Diferença em relação à meta (só faz sentido em dias de semana)
    df['diferenca'] = df['realizado'] - META_DIARIA

    # Situação do dia
    df['situacao'] = df.apply(
        lambda row: '✅ PASSOU' if row['dia_semana'] < 5 and row['realizado'] >= META_DIARIA
        else ('🟡 FDS' if row['dia_semana'] >= 5 else '❌ FALTOU'),
        axis=1
    )

    # Excedente (só dias de semana que passaram da meta)
    df['excedente'] = df.apply(
        lambda row: row['diferenca'] if (row['dia_semana'] < 5 and row['diferenca'] > 0) else 0,
        axis=1
    )

    # Faltam para atingir a meta (só dias de semana abaixo da meta)
    df['faltam'] = df.apply(
        lambda row: abs(row['diferenca']) if (row['dia_semana'] < 5 and row['diferenca'] < 0) else 0,
        axis=1
    )

    # Data formatada para exibição nos gráficos
    df['data_label'] = df['Data'].dt.strftime('%d/%b')

    return df


def resumo_ultimo_dia(df: pd.DataFrame) -> dict:
    """Retorna os valores do card de resumo (último dia com dados)."""
    ultimo = df.iloc[-1]
    return {
        'data':               ultimo['data_label'],
        'realizado':          int(ultimo['realizado']),
        'meta':               META_DIARIA,
        'faltam':             int(ultimo['faltam']),
        'represado':          int(ultimo['represado_acumulado']),
        'atingimento_pct':    round(ultimo['realizado'] / META_DIARIA * 100, 1),
        'situacao':           ultimo['situacao'],
        'is_fds':             ultimo['dia_semana'] >= 5,
    }