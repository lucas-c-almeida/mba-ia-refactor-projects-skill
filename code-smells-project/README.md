# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

A configuração vem do ambiente (ver `.env.example`): `SECRET_KEY`, `APP_DEBUG` (desligado por padrão), `APP_HOST`, `APP_PORT`, `DB_PATH`, `APP_ENV`.

## Estrutura

```
app.py          composition root (create_app) e entry point
config/         leitura única da configuração
models/         regras de domínio e persistência (repositórios SQL parametrizados)
controllers/    casos de uso, sem objetos HTTP
views/          rotas: parse -> controller -> resposta
middlewares/    tratamento centralizado de erros e conexão por requisição
adapters/       efeitos externos (notificações)
```
