import streamlit as st

# Configuração da página
st.set_page_config(page_title="Meu Hub de Dados", layout="wide")

st.title("🚀 Painel de Controle Principal")
st.markdown("Selecione uma ferramenta abaixo para começar:")

# Definição das páginas apontando para os caminhos dos seus arquivos
pg = st.navigation([
    st.Page("geolocalizacaover2/geo_script.py", title="Geolocalização", icon="📍"),
    st.Page("grafico/grafico_script.py", title="Visualização de Gráficos", icon="📊")
])

# Executa a navegação
pg.run()