# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`, reorganizada em MVC.

## Como rodar

```bash
pip install -r requirements.txt
SEED_USER_PASSWORD=<senha> python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**. A senha dos usuários de exemplo vem de `SEED_USER_PASSWORD`.

## Configuração

Veja `.env.example`. Tudo é lido uma vez em `config/settings.py`. Pontos relevantes:

- `APP_DEBUG` (padrão `false`): o modo debug do Flask só liga por opt-in.
- `OPERATOR_TOKEN` (padrão vazio): operações privilegiadas — `GET /reports/summary` e `DELETE /users/<id>` — exigem o header `X-Operator-Token`; sem token configurado respondem `403`.

## Estrutura

`models/` (entidades, regras, repositórios) · `controllers/` (casos de uso) · `routes/` (rotas e serializers) · `middlewares/` (error boundary, guard) · `config/` · `app.py` (composition root).
