# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Estrutura

```
app.py            raiz de composição (create_app) e ponto de entrada
config/           configuração lida do ambiente (settings.py) e lista de variáveis
models/           regras de domínio e persistência (SQLite)
controllers/      casos de uso
views/            rotas HTTP e validação de entrada
middlewares/      tratamento de erros, conexão por requisição, guarda de operador
```

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`, na raiz do projeto) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

A configuração vem de variáveis de ambiente — **exporte-as** antes de iniciar; a aplicação não lê arquivo `.env`. A lista completa, com o significado de cada uma, está em `config/variables.example`. As principais:

- `OPERATOR_TOKEN` — credencial de operador para `GET /relatorios/vendas` (cabeçalho `X-Operator-Token`). Sem ela, a rota responde 403.
- `SEED_ADMIN_PASSWORD`, `SEED_JOAO_PASSWORD`, `SEED_MARIA_PASSWORD` — senhas das contas de exemplo, usadas só no primeiro boot. Sem elas, as contas são criadas sem senha utilizável.
- `APP_DEBUG=true` — liga o modo debug (desligado por padrão).

```bash
export OPERATOR_TOKEN=...
export SEED_JOAO_PASSWORD=...
python app.py
```
