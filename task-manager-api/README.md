# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`, organizada em camadas MVC:

```
app.py          composition root: create_app() monta configuração, controllers, rotas e error handler
config/         leitura e validação das variáveis de ambiente
models/         entidades, regras de domínio e consultas (Task, User, Category, relógio, erros)
controllers/    casos de uso (tarefas, usuários, categorias, relatórios)
routes/         rotas HTTP (parse → controller → resposta), validação de entrada e formatos de resposta
middlewares/    tratamento centralizado de erros e credencial de operador
seed.py         script de operador que recria os dados de exemplo
```

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env        # ou exporte as variáveis listadas nele
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000` (configurável por `APP_HOST`/`APP_PORT`; debug só com `APP_DEBUG=true`).
O `seed.py` recria o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**.
As senhas das contas de exemplo vêm de `SEED_ADMIN_PASSWORD`, `SEED_USER_PASSWORD` e `SEED_MANAGER_PASSWORD`; sem elas, cada conta recebe uma senha aleatória.

### Operações de operador

`GET /reports/summary`, `DELETE /users/<id>` e a alteração de `role` ou `active` de um usuário exigem o header
`X-Operator-Token` com o valor de `OPERATOR_TOKEN`. Sem `OPERATOR_TOKEN` configurado, essas operações respondem `403`.
