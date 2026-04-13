import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import numpy as np

st.set_page_config(page_title="Mapa de Acidentes Inteligente", layout="wide")

st.title("🚦 Análise Inteligente de Acidentes no Paraná")

df = pd.read_csv("acidentes_pr_2025.csv", sep=";", encoding="latin1")

df['latitude'] = df['latitude'].astype(str).str.replace(',', '.').astype(float)
df['longitude'] = df['longitude'].astype(str).str.replace(',', '.').astype(float)

df['data_inversa'] = pd.to_datetime(df['data_inversa'], errors='coerce')
df['hora'] = pd.to_datetime(df['horario'], errors='coerce').dt.hour

df = df.dropna(subset=['latitude', 'longitude'])

tipo = st.selectbox("Tipo de acidente", df['classificacao_acidente'].dropna().unique())
df_filtrado = df[df['classificacao_acidente'] == tipo]

mapa = folium.Map(location=[-25.4, -49.2], zoom_start=7)

dados_heatmap = df_filtrado[['latitude', 'longitude']].values.tolist()

HeatMap(dados_heatmap, radius=12, blur=20, min_opacity=0.4).add_to(mapa)

for _, row in df_filtrado.iterrows():
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=3,
        popup=f"{row['municipio']} - {row['classificacao_acidente']}"
    ).add_to(mapa)

mapa_data = st_folium(mapa, width=1000, height=600)

if mapa_data and mapa_data.get("last_clicked"):
    lat = mapa_data["last_clicked"]["lat"]
    lon = mapa_data["last_clicked"]["lng"]

    st.subheader("📍 Análise da região clicada")

    def distancia(lat1, lon1, lat2, lon2):
        return np.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

    df_filtrado['dist'] = df_filtrado.apply(
        lambda row: distancia(lat, lon, row['latitude'], row['longitude']), axis=1
    )

    proximos = df_filtrado[df_filtrado['dist'] < 0.05]

    st.metric("Acidentes próximos", len(proximos))

    if len(proximos) > 0:
        st.bar_chart(proximos['classificacao_acidente'].value_counts())
    else:
        st.write("Nenhum acidente próximo.")

st.subheader("📊 Estatísticas Gerais")

col1, col2 = st.columns(2)

with col1:
    st.metric("Total de acidentes", len(df_filtrado))
    st.bar_chart(df_filtrado['municipio'].value_counts().head(10))

with col2:
    st.bar_chart(df_filtrado['hora'].value_counts().sort_index())

st.subheader("🧠 Insights Automáticos")

total = len(df_filtrado)

if total > 0:
    cidade_top = df_filtrado['municipio'].mode()[0]
    hora_top = int(df_filtrado['hora'].mode()[0]) if not df_filtrado['hora'].isna().all() else "N/A"

    st.write(f'''
    🔍 Principais descobertas:

    - Cidade com mais ocorrências: {cidade_top}
    - Horário mais crítico: {hora_top}h
    - Total analisado: {total} acidentes

    💡 Indica concentração de risco em regiões e horários específicos.
    ''')

else:
    st.write("Sem dados suficientes para análise.")
