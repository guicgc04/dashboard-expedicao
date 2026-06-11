import io
import requests
import pandas as pd


META_SEGFEX  = 4250
META_CORRIDA = 3259
META_DIARIA  = META_SEGFEX


def carregar_dados(caminho: str) -> pd.DataFrame:
    if caminho.startswith("http"):
        base = caminho.split("?")[0]
        url_download = base + "?download=1"
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/octet-stream"}
        resp = requests.get(url_download, headers=headers, allow_redirects=True, timeout=30)
        resp.raise_for_status()
        df = pd.read_excel(io.BytesIO(resp.content), engine="openpyxl")
    else:
        df = pd.read_excel(caminho, engine="openpyxl")

    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
    df = df.sort_values('Data').reset_index(drop=True)
    return df


def calcular_metricas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df['dia_semana'] = df['Data'].dt.dayofweek
    df['realizado']  = df['Quantidade de PCG Entregue']

    # ── Saldo: TODOS os dias contam igual (4250 - realizado)
    # FDS não é mais alívio — cargas continuam entrando
    df['saldo_segfex'] = META_SEGFEX - df['realizado']
    df['represado_segfex'] = df['saldo_segfex'].cumsum()

    df['diferenca'] = df['realizado'] - META_SEGFEX

    df['situacao'] = df.apply(
        lambda r: '✅ PASSOU' if r['realizado'] >= META_SEGFEX else '❌ FALTOU',
        axis=1
    )
    df['excedente'] = df['diferenca'].apply(lambda v: v if v > 0 else 0)
    df['faltam']    = df['diferenca'].apply(lambda v: abs(v) if v < 0 else 0)

    # Corrida (mantido no cálculo mas não exibido)
    df['saldo_corrida']    = META_CORRIDA - df['realizado']
    df['represado_corrida'] = df['saldo_corrida'].cumsum()

    df['data_label'] = df['Data'].dt.strftime('%d/%b')
    df['mes']        = df['Data'].dt.strftime('%b/%Y')

    # legado
    df['saldo_dia']           = df['saldo_segfex']
    df['represado_acumulado'] = df['represado_segfex']

    return df


def resumo_ultimo_dia(df: pd.DataFrame) -> dict:
    u = df.iloc[-1]
    return {
        'data':               u['data_label'],
        'realizado':          int(u['realizado']),
        'meta_segfex':        META_SEGFEX,
        'faltam_segfex':      int(u['faltam']),
        'represado_segfex':   int(u['represado_segfex']),
        'atingimento_segfex': round(u['realizado'] / META_SEGFEX * 100, 1),
        'situacao':           u['situacao'],
        'faltam_corrida':     int(u.get('faltam_corrida', 0)),
        'represado_corrida':  int(u['represado_corrida']),
        'atingimento_corrida':round(u['realizado'] / META_CORRIDA * 100, 1),
        'meta':               META_SEGFEX,
        'faltam':             int(u['faltam']),
        'represado':          int(u['represado_segfex']),
        'atingimento_pct':    round(u['realizado'] / META_SEGFEX * 100, 1),
        'is_fds':             u['dia_semana'] >= 5,
    }