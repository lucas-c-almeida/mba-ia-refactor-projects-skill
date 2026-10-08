# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Organizada em camadas MVC: `models/` (entidades, regras e repositórios), `controllers/` (casos de uso), `routes/` (camada HTTP), `middlewares/` (fronteira de erros e guarda de operador) e `config/` (leitura única do ambiente). `app.py` é a raiz de composição (`create_app()`).

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Configuração

Toda a configuração vem do ambiente (veja `.env.example`); nenhuma chave é opcional demais para ter um valor inseguro por padrão:

- `APP_DEBUG` (padrão `false`), `APP_HOST` (padrão `0.0.0.0`), `APP_PORT` (padrão `5000`), `DATABASE_URL`, `SECRET_KEY` (sem valor, uma chave aleatória por processo é usada).
- `CORS_ORIGINS` (lista separada por vírgulas; vazio libera qualquer origem, como antes) e `CORS_ALLOW_PRIVATE_NETWORK` (padrão `true`, como antes).
- `OPERATOR_TOKEN`: credencial das rotas de operador (`GET /reports/summary`, `DELETE /users/<id>`), enviada no header `X-Operator-Token`. Sem ele, essas rotas respondem `403`.
- `SEED_ADMIN_PASSWORD`, `SEED_USER_PASSWORD`, `SEED_MANAGER_PASSWORD`: senhas das contas do `seed.py`. Sem elas, senhas aleatórias são geradas e mostradas uma única vez.
