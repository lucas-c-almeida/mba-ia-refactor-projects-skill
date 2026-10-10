# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

## Estrutura

```
app.py           composição (create_app) e ponto de entrada
config/          leitura única do ambiente (ver .env.example)
routes/          rotas e validação de entrada: parse, chamar um controller, renderizar
controllers/     casos de uso, sem objetos de request/response
models/          regras de domínio e persistência (SQLite)
middlewares/     tratamento de erros centralizado e guarda de operador
```

## Configuração

Todas as chaves estão em `.env.example`. Por padrão o modo debug fica desligado e a rota
`GET /relatorios/vendas` responde 403 até que `OPERATOR_TOKEN` seja definido (enviado no
cabeçalho `X-Operator-Token`).
