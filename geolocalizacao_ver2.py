import streamlit as st
import pandas as pd
import os

# Configuração inicial da página
st.set_page_config(page_title="Acidentes PR 2025", layout="wide")

st.title("🚗 Geolocalização de Acidentes - Paraná 2025")
st.markdown("Selecione o tipo de ocorrência na barra lateral para visualizar os pontos no mapa.")

# Mapeamento dos arquivos CSV solicitados
arquivos = {
    "Sem Vítimas": "acidentes_pr_2025_sem_vitimas.csv",
    "Com Vítimas": "acidentes_pr_2025_com_vitimas.csv",
    "Com Fatalidades": "acidentes_pr_2025_com_fatalidade.csv"
}

# Sidebar para seleção do DataFrame
st.sidebar.header("Filtros")
categoria = st.sidebar.selectbox("Escolha a categoria:", list(arquivos.keys()))

nome_arquivo = arquivos[categoria]

# Lógica para carregar e exibir os dados
if os.path.exists(nome_arquivo):
    df = pd.read_csv(nome_arquivo)
    
    # O Streamlit reconhece automaticamente colunas chamadas 'latitude' e 'longitude'
    if 'latitude' in df.columns and 'longitude' in df.columns:
        st.subheader(f"Mapa: {categoria}")
        
        # Exibe o mapa interativo
        st.map(df)
        
        # Exibe uma prévia da tabela de dados para conferência
        with st.expander("Ver detalhes dos dados"):
            st.write(f"Total de ocorrências: {len(df)}")
            st.dataframe(df)
    else:
        st.error(f"Erro: O arquivo '{nome_arquivo}' não possui as colunas 'latitude' e 'longitude'.")
else:
    st.warning(f"Atenção: O arquivo '{nome_arquivo}' não foi encontrado na pasta do script.")