import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Acidentes PR 2025", layout="wide")

st.title("📍 Mapa de Acidentes - Paraná 2025")

@st.cache_data
def carregar_dados():
    try:
        # Carrega o arquivo CSV
        df = pd.read_csv('acidentes_pr_2025.csv')
        
        # Garante que as colunas de latitude e longitude existam e remove valores nulos
        # O Streamlit reconhece automaticamente nomes como 'latitude', 'lat', 'longitude' ou 'lon'
        df = df.dropna(subset=['latitude', 'longitude'])
        
        return df
    except FileNotFoundError:
        st.error("O arquivo 'acidentes_pr_2025.csv' não foi encontrado.")
        return None

df_acidentes = carregar_dados()

if df_acidentes is not None:
    # Filtro opcional na barra lateral
    st.sidebar.header("Filtros")
    if st.sidebar.checkbox("Mostrar tabela de dados"):
        st.subheader("Dados Brutos")
        st.dataframe(df_acidentes)

    # Exibição do Mapa
    st.subheader("Geolocalização dos Acidentes")
    st.map(df_acidentes)