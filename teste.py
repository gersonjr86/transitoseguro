from pathlib import Path
from datetime import time

import pandas as pd
import pydeck as pdk
import streamlit as st

st.set_page_config(
    page_title="Mapa Geoespacial de Acidentes 2025",
    layout="wide",
    initial_sidebar_state="expanded"
)

CSV_PADRAO = Path(r"C:\Users\gerso\OneDrive\Área de Trabalho\python\GitHub\projeto harve\acidentes_pr_2025.csv")


# =========================================================
# LEITURA E LIMPEZA
# =========================================================
@st.cache_data
def ler_csv(caminho):
    tentativas = [
        {"encoding": "utf-8", "sep": ","},
        {"encoding": "utf-8", "sep": ";"},
        {"encoding": "latin-1", "sep": ","},
        {"encoding": "latin-1", "sep": ";"},
        {"encoding": "cp1252", "sep": ";"},
    ]
    ultimo = None

    for tentativa in tentativas:
        try:
            return pd.read_csv(caminho, engine="python", **tentativa)
        except Exception as e:
            ultimo = e

    raise ValueError(f"Não foi possível ler o CSV. Último erro: {ultimo}")


def limpar_numero_virgula(serie):
    s = serie.astype(str).str.strip()
    s = s.str.replace(",", ".", regex=False)
    s = s.str.extract(r"(-?\d+(?:\.\d+)?)", expand=False)
    return pd.to_numeric(s, errors="coerce")


@st.cache_data
def preparar_dados(caminho):
    df = ler_csv(caminho).copy()

    # Limpeza só do que já existe no CSV
    df["latitude"] = limpar_numero_virgula(df["latitude"])
    df["longitude"] = limpar_numero_virgula(df["longitude"])
    df["km"] = limpar_numero_virgula(df["km"])
    df["br"] = pd.to_numeric(df["br"], errors="coerce")
    df["idade"] = pd.to_numeric(df["idade"], errors="coerce")

    # Mantém datetime para filtro
    df["data_inversa"] = pd.to_datetime(df["data_inversa"], errors="coerce")
    df["horario"] = pd.to_datetime(df["horario"], format="%H:%M:%S", errors="coerce")

    colunas_texto = [
        "municipio",
        "classificacao_acidente",
        "condicao_metereologica",
        "sentido_via",
        "tipo_veiculo",
        "sexo",
    ]

    for col in colunas_texto:
        df[col] = df[col].astype(str).str.strip()

    df = df.dropna(subset=["latitude", "longitude"]).copy()
    df = df[
        df["latitude"].between(-90, 90) &
        df["longitude"].between(-180, 180)
    ].copy()

    return df


def calcular_zoom(lat_min, lat_max, lon_min, lon_max):
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


def hora_para_minutos(h):
    if pd.isna(h) or h is None:
        return None

    # Se for Timestamp
    if hasattr(h, "hour") and hasattr(h, "minute"):
        return h.hour * 60 + h.minute

    return None


# =========================================================
# TÍTULO
# =========================================================
st.title("🗺️ Mapa Geoespacial de Acidentes Rodoviários 2025")
st.caption("Visualização com mapa base real, filtros do CSV tratado e zoom automático.")


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.header("Arquivo")
    caminho_csv = st.text_input("Caminho do CSV", str(CSV_PADRAO))

try:
    base = preparar_dados(caminho_csv)
except Exception as e:
    st.error(str(e))
    st.stop()

if base.empty:
    st.error("A base ficou vazia após a limpeza.")
    st.stop()


# =========================================================
# FILTROS REAIS DO CSV
# =========================================================
with st.sidebar:
    st.header("Filtros")

    opcoes_br = sorted([int(x) for x in base["br"].dropna().unique()])
    br_escolhidas = st.multiselect(
        "BR",
        options=opcoes_br,
        default=opcoes_br
    )

    opcoes_municipio = sorted(base["municipio"].dropna().unique().tolist())
    municipios_escolhidos = st.multiselect(
        "Município",
        options=opcoes_municipio,
        default=[]
    )

    opcoes_classificacao = sorted(base["classificacao_acidente"].dropna().unique().tolist())
    classificacoes_escolhidas = st.multiselect(
        "Classificação do acidente",
        options=opcoes_classificacao,
        default=opcoes_classificacao
    )

    opcoes_clima = sorted(base["condicao_metereologica"].dropna().unique().tolist())
    climas_escolhidos = st.multiselect(
        "Condição meteorológica",
        options=opcoes_clima,
        default=opcoes_clima
    )

    opcoes_sentido = sorted(base["sentido_via"].dropna().unique().tolist())
    sentidos_escolhidos = st.multiselect(
        "Sentido da via",
        options=opcoes_sentido,
        default=opcoes_sentido
    )

    opcoes_tipo = sorted(base["tipo_veiculo"].dropna().unique().tolist())
    tipos_escolhidos = st.multiselect(
        "Tipo de veículo",
        options=opcoes_tipo,
        default=[]
    )

    opcoes_sexo = sorted(base["sexo"].dropna().unique().tolist())
    sexos_escolhidos = st.multiselect(
        "Sexo",
        options=opcoes_sexo,
        default=[]
    )

    km_validos = base["km"].dropna()
    if not km_validos.empty:
        km_min = float(km_validos.min())
        km_max = float(km_validos.max())
        faixa_km = st.slider(
            "Faixa de KM",
            min_value=float(km_min),
            max_value=float(km_max),
            value=(float(km_min), float(km_max))
        )
    else:
        faixa_km = None

    data_validas = base["data_inversa"].dropna()
    if not data_validas.empty:
        data_ini = data_validas.min().date()
        data_fim = data_validas.max().date()
        periodo = st.date_input(
            "Período",
            value=(data_ini, data_fim),
            min_value=data_ini,
            max_value=data_fim
        )
    else:
        periodo = None

    horas_validas = [h.to_pydatetime().time() for h in base["horario"].dropna().tolist()]
    if horas_validas:
        hora_min = min(horas_validas)
        hora_max = max(horas_validas)
        faixa_horario = st.slider(
            "Faixa de horário",
            min_value=hora_min,
            max_value=hora_max,
            value=(hora_min, hora_max),
            format="HH:mm"
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
            value=(idade_min, idade_max)
        )
    else:
        faixa_idade = None

    st.header("Mapa")
    estilo_mapa = st.selectbox(
        "Estilo do mapa",
        options=["light", "dark", "road", "satellite"],
        index=2
    )

    camada = "Somente pontos"

    raio_hex = st.slider("Raio do hexágono", 200, 15000, 2500, 100)
    elevacao = st.slider("Escala 3D", 1, 50, 12, 1)
    raio_ponto = st.slider("Raio dos pontos", 50, 4000, 220, 10)
    pitch = st.slider("Inclinação", 0, 60, 45, 5)


# =========================================================
# APLICA FILTROS
# =========================================================
filtrado = base.copy()

if br_escolhidas:
    filtrado = filtrado[filtrado["br"].isin(br_escolhidas)].copy()
else:
    filtrado = filtrado.iloc[0:0].copy()

if municipios_escolhidos:
    filtrado = filtrado[filtrado["municipio"].isin(municipios_escolhidos)].copy()

if classificacoes_escolhidas:
    filtrado = filtrado[filtrado["classificacao_acidente"].isin(classificacoes_escolhidas)].copy()

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

if periodo and isinstance(periodo, tuple) and len(periodo) == 2:
    data_inicial, data_final = periodo
    filtrado = filtrado[
        filtrado["data_inversa"].dt.date.between(data_inicial, data_final)
    ].copy()

if faixa_horario is not None:
    h_ini = hora_para_minutos(faixa_horario[0])
    h_fim = hora_para_minutos(faixa_horario[1])
    minutos_serie = filtrado["horario"].apply(hora_para_minutos)
    filtrado = filtrado[minutos_serie.between(h_ini, h_fim, inclusive="both")].copy()

if faixa_idade is not None:
    filtrado = filtrado[
        filtrado["idade"].between(faixa_idade[0], faixa_idade[1], inclusive="both")
    ].copy()

if filtrado.empty:
    st.warning("Nenhum registro encontrado com os filtros aplicados.")
    st.stop()


# =========================================================
# KPIs
# =========================================================
total_registros = len(filtrado)
qtd_municipios = filtrado["municipio"].nunique()
qtd_brs = filtrado["br"].nunique()
km_medio = filtrado["km"].mean()
idade_media = filtrado["idade"].mean()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Registros filtrados", f"{total_registros:,}".replace(",", "."))
k2.metric("Municípios", f"{qtd_municipios:,}".replace(",", "."))
k3.metric("BRs", f"{qtd_brs:,}".replace(",", "."))
k4.metric("KM médio", f"{km_medio:.1f}" if pd.notna(km_medio) else "-")
k5.metric("Idade média", f"{idade_media:.1f}" if pd.notna(idade_media) else "-")


# =========================================================
# MAPA COM BASEMAP REAL
# =========================================================
lat_min = float(filtrado["latitude"].min())
lat_max = float(filtrado["latitude"].max())
lon_min = float(filtrado["longitude"].min())
lon_max = float(filtrado["longitude"].max())

zoom = calcular_zoom(lat_min, lat_max, lon_min, lon_max)
lat_centro = float(filtrado["latitude"].mean())
lon_centro = float(filtrado["longitude"].mean())

tooltip_html = """
<b>Data:</b> {data_inversa}<br/>
<b>Horário:</b> {horario}<br/>
<b>BR:</b> {br}<br/>
<b>KM:</b> {km}<br/>
<b>Município:</b> {municipio}<br/>
<b>Classificação:</b> {classificacao_acidente}<br/>
<b>Condição meteorológica:</b> {condicao_metereologica}<br/>
<b>Sentido da via:</b> {sentido_via}<br/>
<b>Tipo de veículo:</b> {tipo_veiculo}<br/>
<b>Idade:</b> {idade}<br/>
<b>Sexo:</b> {sexo}<br/>
<b>Latitude:</b> {latitude}<br/>
<b>Longitude:</b> {longitude}<br/>
"""

map_df = filtrado.copy()

# Converter colunas problemáticas para string antes de mandar pro PyDeck
map_df["data_inversa"] = map_df["data_inversa"].dt.strftime("%Y-%m-%d")
map_df["horario"] = map_df["horario"].dt.strftime("%H:%M:%S")

# Substituir NaN por None onde fizer sentido visualmente
colunas_mapa = [
    "data_inversa", "horario", "br", "km", "municipio",
    "classificacao_acidente", "condicao_metereologica",
    "sentido_via", "tipo_veiculo", "idade", "sexo",
    "latitude", "longitude"
]

map_df = map_df[colunas_mapa].copy()
map_df = map_df.where(pd.notnull(map_df), None)


layers = [
    pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[longitude, latitude]",
        get_fill_color=[230, 120, 40, 180],
        get_radius=180,
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
        pitch=0,
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

st.pydeck_chart(deck, width="stretch", height=780)

col_mapa, col_lateral = st.columns([3.7, 1.3])

with col_mapa:
    st.subheader("Mapa geoespacial")
    st.pydeck_chart(deck, width="stretch", height=780)

with col_lateral:
    st.subheader("Resumo")

    st.markdown("**Classificação do acidente**")
    resumo_classificacao = (
        filtrado["classificacao_acidente"]
        .value_counts(dropna=False)
        .rename_axis("Classificação")
        .reset_index(name="Qtd")
    )
    st.dataframe(resumo_classificacao, width="stretch", hide_index=True)

    st.markdown("**Municípios com mais registros**")
    resumo_municipio = (
        filtrado["municipio"]
        .value_counts(dropna=False)
        .head(10)
        .rename_axis("Município")
        .reset_index(name="Qtd")
    )
    st.dataframe(resumo_municipio, width="stretch", hide_index=True)

    st.markdown("**Tipos de veículo**")
    resumo_veiculo = (
        filtrado["tipo_veiculo"]
        .value_counts(dropna=False)
        .head(10)
        .rename_axis("Veículo")
        .reset_index(name="Qtd")
    )
    st.dataframe(resumo_veiculo, width="stretch", hide_index=True)

    st.markdown("**Condição meteorológica**")
    resumo_clima = (
        filtrado["condicao_metereologica"]
        .value_counts(dropna=False)
        .rename_axis("Clima")
        .reset_index(name="Qtd")
    )
    st.dataframe(resumo_clima, width="stretch", hide_index=True)


# =========================================================
# TABELAS
# =========================================================
st.subheader("Análise tabular")

tab1, tab2, tab3 = st.tabs(["Trechos BR/KM", "Municípios", "Base filtrada"])

with tab1:
    ranking_trechos = (
        filtrado.groupby(["br", "km"], dropna=False)
        .size()
        .reset_index(name="qtd_registros")
        .sort_values("qtd_registros", ascending=False)
        .head(30)
    )
    st.dataframe(ranking_trechos, width="stretch", hide_index=True)

with tab2:
    ranking_municipios = (
        filtrado.groupby("municipio", dropna=False)
        .size()
        .reset_index(name="qtd_registros")
        .sort_values("qtd_registros", ascending=False)
        .head(30)
    )
    st.dataframe(ranking_municipios, width="stretch", hide_index=True)

with tab3:
    colunas_exibir = [
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
    st.dataframe(filtrado[colunas_exibir], width="stretch", hide_index=True)


# =========================================================
# DIAGNÓSTICO
# =========================================================
with st.expander("Diagnóstico"):
    st.write("Linhas após limpeza:", len(base))
    st.write("Linhas após filtros:", len(filtrado))
    st.write("Colunas disponíveis:", list(base.columns))
    st.dataframe(base.head(10), width="stretch")