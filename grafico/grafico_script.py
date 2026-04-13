import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Acidentes PR 2025", layout="wide")

st.title("📊 Análise de Acidentes - PR 2025")

# Função para carregar os dados
@st.cache_data
def load_data():
    # Carrega o CSV (certifique-se que o arquivo está na mesma pasta do script)
    df = pd.read_csv('acidentes_pr_2025.csv')
    # Garante que KM seja numérico para o gráfico
    #df['km'] = pd.to_numeric(df['km'].str.replace(',', '.'), errors='coerce')
    return df

try:
    df = load_data()

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("Filtros Interativos")

    # Filtro por BR
    lista_br = sorted(df['br'].unique().tolist())
    br_selecionada = st.sidebar.multiselect("Selecione as BRs:", lista_br, default=lista_br)

    # Filtro por Tipo de Acidente
    lista_tipos = df['classificacao_acidente'].unique().tolist()
    tipos_selecionados = st.sidebar.multiselect("Classificação do Acidente:", lista_tipos, default=lista_tipos)

    # Aplicando os filtros ao DataFrame
    df_filtrado = df[
        (df['br'].isin(br_selecionada)) & 
        (df['classificacao_acidente'].isin(tipos_selecionados))
    ]

    # --- GRÁFICO INTERATIVO ---
    st.subheader("Distribuição de Acidentes por KM e BR")
    
    if not df_filtrado.empty:
        fig = px.scatter(
            df_filtrado, 
            x="km", 
            y="br", 
            color="classificacao_acidente",
            hover_data=['classificacao_acidente', 'br', 'km'],
            title="Acidentes: BR vs KM",
            labels={"km": "Quilômetro (KM)", "br": "Rodovia (BR)", "classificacao_acidente": "Tipo"},
            height=600
        )
        
        # Ajustando o eixo Y para tratar BR como categoria (evita escalas numéricas estranhas)
        fig.update_yaxes(type='category')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Exibição da tabela de dados filtrados
        with st.expander("Ver dados brutos filtrados"):
            st.dataframe(df_filtrado)
    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")

except FileNotFoundError:
    st.error("Arquivo 'acidentes_pr_2025.csv' não encontrado. Verifique o nome e o local do arquivo.")