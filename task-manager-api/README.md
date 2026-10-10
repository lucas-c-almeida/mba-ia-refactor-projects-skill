# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Organizada em camadas MVC: `models/` (entidades, regras, repositórios), `controllers/` (casos de uso), `routes/` (camada de entrega), `middlewares/` (fronteira de erros, guarda de operador) e `config/` (configuração lida uma vez do ambiente). `app.py` é a raiz de composição (`create_app()`).

## Como rodar

```bash
pip install -r requirements.txt
SEED_ADMIN_PASSWORD=... SEED_USER_PASSWORD=... SEED_MANAGER_PASSWORD=... python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias. As senhas das contas de exemplo vêm do ambiente (nenhuma credencial fica no código).

## Configuração

Todas as variáveis estão em `.env.example`. As principais:

- `APP_DEBUG` (padrão `false`): ativa o modo debug do Flask. Nunca habilite em produção.
- `OPERATOR_TOKEN` (sem padrão): credencial do relatório `GET /reports/summary` (cabeçalho `X-Operator-Token`). Sem ela configurada, o endpoint responde `403`.
- `SECRET_KEY`, `DATABASE_URI`, `APP_BIND`, `APP_PORT`: opcionais.
