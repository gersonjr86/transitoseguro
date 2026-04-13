import io
import os
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st


st.set_page_config(
    page_title="Mapa Geoespacial de Acidentes 2025",
    layout="wide",
    initial_sidebar_state="expanded",
)


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CSV_ENV_VAR = "ACIDENTES_CSV_PATH"
CSV_PADRAO = DATA_DIR / "acidentes_pr_2025.csv"
CSV_LEGADO = Path(r'C:\Users\gerso\OneDrive\Área de Trabalho\python\GitHub\projeto harve\geolocalizacaover2\acidentes_pr_2025.csv')
COLUNAS_OBRIGATORIAS = [
    "latitude",
    "longitude",
    "km",
    "br",
    "idade",
    "data_inversa",
    "horario",
    "municipio",
    "classificacao_acidente",
    "condicao_metereologica",
    "sentido_via",
    "tipo_veiculo",
    "sexo",
]
COLUNAS_MAPA = [
    "data_inversa",
    "horario",
    "br",
    "km",
    "municipio",
    "classificacao_acidente",
    "condicao_metereologica",
    "sentido_via",
    "tipo_veiculo",
    "idade",
    "sexo",
    "latitude",
    "longitude",
]


def resolver_caminho_csv_padrao() -> Path:
    caminho_env = os.getenv(CSV_ENV_VAR, "").strip()
    if caminho_env:
        return Path(caminho_env).expanduser()
    if CSV_PADRAO.exists():
        return CSV_PADRAO
    if CSV_LEGADO.exists():
        return CSV_LEGADO
    return CSV_PADRAO


def _ler_csv_tentativas(abrir_fonte):
    tentativas = [
        {"encoding": "utf-8", "sep": ","},
        {"encoding": "utf-8", "sep": ";"},
        {"encoding": "latin-1", "sep": ","},
        {"encoding": "latin-1", "sep": ";"},
        {"encoding": "cp1252", "sep": ";"},
    ]
    ultimo_erro = None

    for tentativa in tentativas:
        try:
            return pd.read_csv(abrir_fonte(), engine="python", **tentativa)
        except Exception as erro:  # pragma: no cover - depende do arquivo de entrada
            ultimo_erro = erro

    raise ValueError(f"Nao foi possivel ler o CSV. Ultimo erro: {ultimo_erro}")


@st.cache_data
def ler_csv(caminho: str) -> pd.DataFrame:
    caminho_resolvido = Path(caminho).expanduser()
    return _ler_csv_tentativas(lambda: caminho_resolvido)


@st.cache_data
def ler_csv_upload(nome_arquivo: str, conteudo_bytes: bytes) -> pd.DataFrame:
    del nome_arquivo
    return _ler_csv_tentativas(lambda: io.BytesIO(conteudo_bytes))


def validar_colunas(df: pd.DataFrame) -> None:
    faltantes = [coluna for coluna in COLUNAS_OBRIGATORIAS if coluna not in df.columns]
    if faltantes:
        raise ValueError(
            "O CSV nao possui as colunas obrigatorias: " + ", ".join(faltantes)
        )


def limpar_numero_virgula(serie: pd.Series) -> pd.Series:
    serie_limpa = serie.astype(str).str.strip()
    serie_limpa = serie_limpa.str.replace(",", ".", regex=False)
    serie_limpa = serie_limpa.str.extract(r"(-?\d+(?:\.\d+)?)", expand=False)
    return pd.to_numeric(serie_limpa, errors="coerce")


def preparar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    validar_colunas(df)
    base = df.copy()

    base["latitude"] = limpar_numero_virgula(base["latitude"])
    base["longitude"] = limpar_numero_virgula(base["longitude"])
    base["km"] = limpar_numero_virgula(base["km"])
    base["br"] = pd.to_numeric(base["br"], errors="coerce")
    base["idade"] = pd.to_numeric(base["idade"], errors="coerce")

    base["data_inversa"] = pd.to_datetime(base["data_inversa"], errors="coerce")
    base["horario"] = pd.to_datetime(base["horario"], format="%H:%M:%S", errors="coerce")

    colunas_texto = [
        "municipio",
        "classificacao_acidente",
        "condicao_metereologica",
        "sentido_via",
        "tipo_veiculo",
        "sexo",
    ]
    for coluna in colunas_texto:
        base[coluna] = base[coluna].fillna("").astype(str).str.strip()

    base = base.dropna(subset=["latitude", "longitude"]).copy()
    base = base[
        base["latitude"].between(-90, 90) & base["longitude"].between(-180, 180)
    ].copy()

    return base


@st.cache_data
def preparar_dados(caminho: str) -> pd.DataFrame:
    return preparar_dataframe(ler_csv(caminho))


@st.cache_data
def preparar_dados_upload(nome_arquivo: str, conteudo_bytes: bytes) -> pd.DataFrame:
    return preparar_dataframe(ler_csv_upload(nome_arquivo, conteudo_bytes))


def calcular_zoom(lat_min: float, lat_max: float, lon_min: float, lon_max: float) -> float:
    lat_span = max(lat_max - lat_min, 0.0001)
    lon_span = max(lon_max - lon_min, 0.0001)
    span = max(lat_span, lon_span)

    if span > 40:
        return 3.5
    if span > 20:
        return 4.5
    if span > 10:
        return 5.5
    if span > 5:
        return 6.5
    if span > 2:
        return 7.5
    if span > 1:
        return 8.5
    if span > 0.5:
        return 10
    if span > 0.2:
        return 11.5
    if span > 0.1:
        return 12.5
    return 13.5


def hora_para_minutos(valor) -> int | None:
    if pd.isna(valor) or valor is None:
        return None
    if hasattr(valor, "hour") and hasattr(valor, "minute"):
        return valor.hour * 60 + valor.minute
    return None


st.title("Mapa Geoespacial de Acidentes Rodoviarios 2025")
st.caption("Visualizacao com mapa base real, filtros do CSV tratado e zoom automatico.")


with st.sidebar:
    st.header("Arquivo")
    st.caption(
        "Use upload, a pasta data/ do projeto ou a variavel "
        f"{CSV_ENV_VAR} para compartilhar a base."
    )
    caminho_inicial = resolver_caminho_csv_padrao()
    arquivo_csv = st.file_uploader("CSV de acidentes", type=["csv"])
    caminho_csv = st.text_input("Caminho do CSV", str(caminho_inicial))

try:
    if arquivo_csv is not None:
        base = preparar_dados_upload(arquivo_csv.name, arquivo_csv.getvalue())
        fonte_dados = f"Upload: {arquivo_csv.name}"
    else:
        caminho_texto = caminho_csv.strip()
        if not caminho_texto:
            raise FileNotFoundError(
                "Informe um caminho para o CSV, coloque o arquivo em data/ ou use upload."
            )
        caminho_resolvido = Path(caminho_texto).expanduser()
        if not caminho_resolvido.exists():
            raise FileNotFoundError(
                "CSV nao encontrado. Envie o arquivo por upload, coloque-o em "
                f"{CSV_PADRAO} ou ajuste o caminho informado."
            )
        base = preparar_dados(str(caminho_resolvido))
        fonte_dados = str(caminho_resolvido)
except Exception as erro:
    st.error(str(erro))
    st.stop()

if base.empty:
    st.error("A base ficou vazia apos a limpeza.")
    st.stop()

st.caption(f"Fonte de dados ativa: `{fonte_dados}`")


with st.sidebar:
    st.header("Filtros")

    opcoes_br = sorted([int(valor) for valor in base["br"].dropna().unique()])
    br_escolhidas = st.multiselect("BR", options=opcoes_br, default=opcoes_br)

    opcoes_municipio = sorted(base["municipio"].dropna().unique().tolist())
    municipios_escolhidos = st.multiselect(
        "Municipio",
        options=opcoes_municipio,
        default=[],
    )

    opcoes_classificacao = sorted(
        base["classificacao_acidente"].dropna().unique().tolist()
    )
    classificacoes_escolhidas = st.multiselect(
        "Classificacao do acidente",
        options=opcoes_classificacao,
        default=opcoes_classificacao,
    )

    opcoes_clima = sorted(base["condicao_metereologica"].dropna().unique().tolist())
    climas_escolhidos = st.multiselect(
        "Condicao meteorologica",
        options=opcoes_clima,
        default=opcoes_clima,
    )

    opcoes_sentido = sorted(base["sentido_via"].dropna().unique().tolist())
    sentidos_escolhidos = st.multiselect(
        "Sentido da via",
        options=opcoes_sentido,
        default=opcoes_sentido,
    )

    opcoes_tipo = sorted(base["tipo_veiculo"].dropna().unique().tolist())
    tipos_escolhidos = st.multiselect(
        "Tipo de veiculo",
        options=opcoes_tipo,
        default=[],
    )

    opcoes_sexo = sorted(base["sexo"].dropna().unique().tolist())
    sexos_escolhidos = st.multiselect("Sexo", options=opcoes_sexo, default=[])

    km_validos = base["km"].dropna()
    if not km_validos.empty:
        km_min = float(km_validos.min())
        km_max = float(km_validos.max())
        faixa_km = st.slider(
            "Faixa de KM",
            min_value=km_min,
            max_value=km_max,
            value=(km_min, km_max),
        )
    else:
        faixa_km = None

    data_validas = base["data_inversa"].dropna()
    if not data_validas.empty:
        data_ini = data_validas.min().date()
        data_fim = data_validas.max().date()
        periodo = st.date_input(
            "Periodo",
            value=(data_ini, data_fim),
            min_value=data_ini,
            max_value=data_fim,
        )
    else:
        periodo = None

    horas_validas = [valor.to_pydatetime().time() for valor in base["horario"].dropna()]
    if horas_validas:
        hora_min = min(horas_validas)
        hora_max = max(horas_validas)
        faixa_horario = st.slider(
            "Faixa de horario",
            min_value=hora_min,
            max_value=hora_max,
            value=(hora_min, hora_max),
            format="HH:mm",
        )
    else:
        faixa_horario = None

    idade_validas = base["idade"].dropna()
    if not idade_validas.empty:
        idade_min = int(idade_validas.min())
        idade_max = int(idade_validas.max())
        faixa_idade = st.slider(
            "Faixa de idade",
            min_value=idade_min,
            max_value=idade_max,
            value=(idade_min, idade_max),
        )
    else:
        faixa_idade = None

    st.header("Mapa")
    estilo_mapa = st.selectbox(
        "Estilo do mapa",
        options=["light", "dark", "road", "satellite"],
        index=2,
    )
    raio_ponto = st.slider("Raio dos pontos", 50, 4000, 220, 10)
    pitch = st.slider("Inclinacao", 0, 60, 45, 5)


filtrado = base.copy()

if br_escolhidas:
    filtrado = filtrado[filtrado["br"].isin(br_escolhidas)].copy()
else:
    filtrado = filtrado.iloc[0:0].copy()

if municipios_escolhidos:
    filtrado = filtrado[filtrado["municipio"].isin(municipios_escolhidos)].copy()

if classificacoes_escolhidas:
    filtrado = filtrado[
        filtrado["classificacao_acidente"].isin(classificacoes_escolhidas)
    ].copy()

if climas_escolhidos:
    filtrado = filtrado[filtrado["condicao_metereologica"].isin(climas_escolhidos)].copy()

if sentidos_escolhidos:
    filtrado = filtrado[filtrado["sentido_via"].isin(sentidos_escolhidos)].copy()

if tipos_escolhidos:
    filtrado = filtrado[filtrado["tipo_veiculo"].isin(tipos_escolhidos)].copy()

if sexos_escolhidos:
    filtrado = filtrado[filtrado["sexo"].isin(sexos_escolhidos)].copy()

if faixa_km is not None:
    filtrado = filtrado[
        filtrado["km"].between(faixa_km[0], faixa_km[1], inclusive="both")
    ].copy()

if isinstance(periodo, (list, tuple)) and len(periodo) == 2:
    data_inicial, data_final = periodo
    filtrado = filtrado[
        filtrado["data_inversa"].dt.date.between(data_inicial, data_final)
    ].copy()

if faixa_horario is not None:
    hora_inicial = hora_para_minutos(faixa_horario[0])
    hora_final = hora_para_minutos(faixa_horario[1])
    minutos_serie = filtrado["horario"].apply(hora_para_minutos)
    filtrado = filtrado[
        minutos_serie.between(hora_inicial, hora_final, inclusive="both")
    ].copy()

if faixa_idade is not None:
    filtrado = filtrado[
        filtrado["idade"].between(faixa_idade[0], faixa_idade[1], inclusive="both")
    ].copy()

if filtrado.empty:
    st.warning("Nenhum registro encontrado com os filtros aplicados.")
    st.stop()


total_registros = len(filtrado)
qtd_municipios = filtrado["municipio"].nunique()
qtd_brs = filtrado["br"].nunique()
km_medio = filtrado["km"].mean()
idade_media = filtrado["idade"].mean()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Registros filtrados", f"{total_registros:,}".replace(",", "."))
k2.metric("Municipios", f"{qtd_municipios:,}".replace(",", "."))
k3.metric("BRs", f"{qtd_brs:,}".replace(",", "."))
k4.metric("KM medio", f"{km_medio:.1f}" if pd.notna(km_medio) else "-")
k5.metric("Idade media", f"{idade_media:.1f}" if pd.notna(idade_media) else "-")


lat_min = float(filtrado["latitude"].min())
lat_max = float(filtrado["latitude"].max())
lon_min = float(filtrado["longitude"].min())
lon_max = float(filtrado["longitude"].max())

zoom = calcular_zoom(lat_min, lat_max, lon_min, lon_max)
lat_centro = float(filtrado["latitude"].mean())
lon_centro = float(filtrado["longitude"].mean())

tooltip_html = """
<b>Data:</b> {data_inversa}<br/>
<b>Horario:</b> {horario}<br/>
<b>BR:</b> {br}<br/>
<b>KM:</b> {km}<br/>
<b>Municipio:</b> {municipio}<br/>
<b>Classificacao:</b> {classificacao_acidente}<br/>
<b>Condicao meteorologica:</b> {condicao_metereologica}<br/>
<b>Sentido da via:</b> {sentido_via}<br/>
<b>Tipo de veiculo:</b> {tipo_veiculo}<br/>
<b>Idade:</b> {idade}<br/>
<b>Sexo:</b> {sexo}<br/>
<b>Latitude:</b> {latitude}<br/>
<b>Longitude:</b> {longitude}<br/>
"""

map_df = filtrado[COLUNAS_MAPA].copy()
map_df["data_inversa"] = map_df["data_inversa"].dt.strftime("%Y-%m-%d")
map_df["horario"] = map_df["horario"].dt.strftime("%H:%M:%S")
map_df = map_df.where(pd.notnull(map_df), None)

layers = [
    pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[longitude, latitude]",
        get_fill_color=[230, 120, 40, 180],
        get_radius=raio_ponto,
        radius_min_pixels=4,
        radius_max_pixels=12,
        pickable=True,
        stroked=True,
        get_line_color=[255, 255, 255, 120],
        line_width_min_pixels=1,
    )
]

deck = pdk.Deck(
    map_style=estilo_mapa,
    initial_view_state=pdk.ViewState(
        latitude=lat_centro,
        longitude=lon_centro,
        zoom=zoom,
        pitch=pitch,
    ),
    layers=layers,
    tooltip={
        "html": tooltip_html,
        "style": {
            "backgroundColor": "#081225",
            "color": "white",
            "fontSize": "13px",
        },
    },
)

col_mapa, col_lateral = st.columns([3.7, 1.3])

with col_mapa:
    st.subheader("Mapa geoespacial")
    st.pydeck_chart(deck, use_container_width=True)

with col_lateral:
    st.subheader("Resumo")

    st.markdown("**Classificacao do acidente**")
    resumo_classificacao = (
        filtrado["classificacao_acidente"]
        .value_counts(dropna=False)
        .rename_axis("Classificacao")
        .reset_index(name="Qtd")
    )
    st.dataframe(resumo_classificacao, use_container_width=True, hide_index=True)

    st.markdown("**Municipios com mais registros**")
    resumo_municipio = (
        filtrado["municipio"]
        .value_counts(dropna=False)
        .head(10)
        .rename_axis("Municipio")
        .reset_index(name="Qtd")
    )
    st.dataframe(resumo_municipio, use_container_width=True, hide_index=True)

    st.markdown("**Tipos de veiculo**")
    resumo_veiculo = (
        filtrado["tipo_veiculo"]
        .value_counts(dropna=False)
        .head(10)
        .rename_axis("Veiculo")
        .reset_index(name="Qtd")
    )
    st.dataframe(resumo_veiculo, use_container_width=True, hide_index=True)

    st.markdown("**Condicao meteorologica**")
    resumo_clima = (
        filtrado["condicao_metereologica"]
        .value_counts(dropna=False)
        .rename_axis("Clima")
        .reset_index(name="Qtd")
    )
    st.dataframe(resumo_clima, use_container_width=True, hide_index=True)


st.subheader("Analise tabular")

tab1, tab2, tab3 = st.tabs(["Trechos BR/KM", "Municipios", "Base filtrada"])

with tab1:
    ranking_trechos = (
        filtrado.groupby(["br", "km"], dropna=False)
        .size()
        .reset_index(name="qtd_registros")
        .sort_values("qtd_registros", ascending=False)
        .head(30)
    )
    st.dataframe(ranking_trechos, use_container_width=True, hide_index=True)

with tab2:
    ranking_municipios = (
        filtrado.groupby("municipio", dropna=False)
        .size()
        .reset_index(name="qtd_registros")
        .sort_values("qtd_registros", ascending=False)
        .head(30)
    )
    st.dataframe(ranking_municipios, use_container_width=True, hide_index=True)

with tab3:
    st.dataframe(filtrado[COLUNAS_MAPA], use_container_width=True, hide_index=True)


with st.expander("Diagnostico"):
    st.write("Linhas apos limpeza:", len(base))
    st.write("Linhas apos filtros:", len(filtrado))
    st.write("Colunas disponiveis:", list(base.columns))
    st.dataframe(base.head(10), use_container_width=True)
