# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possuía alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda continha problemas arquiteturais e de qualidade.

## Estrutura

```
app.py            composition root: create_app() lê a configuração, monta camadas e sobe o servidor
config/           settings.py — lê o ambiente uma única vez e expõe um objeto imutável
models/           entidades, regras de domínio e persistência (consultas) de Task, User e Category
controllers/      casos de uso, um módulo por grupo (tasks, users, categories, reports)
routes/           views: declaração das rotas e formato das respostas (presenters.py)
middlewares/      error_handler.py — fronteira única de erros
database.py       extensão SQLAlchemy e commit com tratamento de falha
seed.py           popula o banco com dados de exemplo
```

## Como rodar

Configure o ambiente a partir de `.env.example` (`SECRET_KEY` é obrigatório; o `seed.py` exige
também `SEED_ADMIN_PASSWORD`, `SEED_USER_PASSWORD` e `SEED_MANAGER_PASSWORD`).

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000` (configurável por `APP_HOST`/`APP_PORT`). O modo debug
fica desligado, a menos que `APP_DEBUG=true`. O `seed.py` popula o banco SQLite (`tasks.db`) com
usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os
endpoints vão retornar listas vazias.
