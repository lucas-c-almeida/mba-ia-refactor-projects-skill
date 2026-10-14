# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
SEED_PASSWORD=<senha> python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias. A senha das contas de exemplo vem de `SEED_PASSWORD`; sem ela, uma senha aleatória é gerada e exibida.

## Configuração

Toda a configuração vem de variáveis de ambiente (veja `.env.example`): `DATABASE_URL`, `SECRET_KEY`, `APP_DEBUG` (desligado por padrão), `APP_HOST`, `APP_PORT` e `OPERATOR_TOKEN`.

As rotas de operador — `GET /reports/summary`, `GET /reports/user/<id>` e `DELETE /users/<id>` — exigem o header `X-Operator-Token` igual a `OPERATOR_TOKEN`. Sem a variável definida, respondem `403`.

## Estrutura

- `app.py`: raiz de composição (`create_app`).
- `config/`: leitura única do ambiente.
- `models/`: entidades, regras de domínio, repositórios e erros de domínio.
- `controllers/`: casos de uso, sem Flask.
- `routes/`: declaração das rotas (parse, chamada, resposta).
- `middlewares/`: tratamento centralizado de erros e guarda de operador.
