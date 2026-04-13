# Projeto Streamlit de Acidentes PR

Este projeto foi organizado para rodar de tres formas:

- localmente com `venv`
- de forma padronizada com `Docker`
- online com time usando repositorio Git + Dev Container/Codespaces

## Estrutura

- `app_mapa_acidentes_pr.py`: app principal
- `requirements.txt`: dependencias Python
- `Dockerfile`: imagem da aplicacao
- `docker-compose.yml`: sobe o app com volume local
- `.devcontainer/devcontainer.json`: abre o projeto em Dev Containers/Codespaces
- `data/`: pasta sugerida para o CSV compartilhado

## Onde colocar o CSV

Voce pode usar qualquer uma destas opcoes:

1. Colocar o arquivo em `data/acidentes_pr_2025.csv`
2. Definir a variavel de ambiente `ACIDENTES_CSV_PATH`
3. Fazer upload do CSV pela sidebar do Streamlit

## Rodar com venv

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app_mapa_acidentes_pr.py
```

Depois abra `http://localhost:8501`.

## Rodar com Docker

```powershell
docker compose up --build
```

O app ficara disponivel em `http://localhost:8501`.

## Trabalhar online com a equipe

1. Suba esta pasta para um repositorio no GitHub ou GitLab.
2. Se usarem GitHub, abram o repositorio em Codespaces.
3. Se usarem VS Code, abram em `Dev Containers`.
4. Dentro do ambiente, rodem:

```powershell
streamlit run app_mapa_acidentes_pr.py
```

## Observacoes

- Se o CSV puder ir para o repositorio, coloquem em `data/`.
- Se o CSV for grande ou sensivel, deixem fora do Git e usem upload ou `ACIDENTES_CSV_PATH`.
- O app ainda aceita o caminho antigo em `Downloads` como fallback local, mas o fluxo recomendado agora eh usar `data/` ou upload.
