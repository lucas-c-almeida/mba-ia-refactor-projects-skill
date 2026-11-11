# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

## Configuração

A aplicação lê a configuração de variáveis de ambiente. **Exporte** as variáveis antes de
iniciar (a aplicação não lê nenhum arquivo `.env`). A lista completa, com os valores padrão,
está em `config/environment.example`.

| Variável | Padrão | Efeito |
|---|---|---|
| `SECRET_KEY` | vazio | Chave de assinatura do Flask |
| `APP_DEBUG` | `false` | Modo debug (debugger interativo). Nunca ligue fora da máquina de desenvolvimento |
| `APP_HOST` / `APP_PORT` | `0.0.0.0` / `5000` | Endereço e porta |
| `DATABASE_FILE` | `loja.db` | Arquivo SQLite, relativo à raiz do projeto |
| `APP_ENV` | `producao` | Valor de `ambiente` em `GET /health` |
| `CORS_ORIGINS` | `*` | Origens permitidas (lista separada por vírgula) |
| `OPERATOR_TOKEN` | vazio | Credencial do operador para `GET /relatorios/vendas` (header `X-Operator-Token`). Vazio = rota fechada (403) |
| `SEED_ADMIN_PASSWORD`, `SEED_CUSTOMER_PASSWORD` | vazio | Senhas das contas criadas no primeiro boot. Vazio = contas sem senha utilizável |

## Estrutura

```
app.py            composition root (configuração, montagem das dependências, rotas)
config/           leitura da configuração
models/           domínio, regras e persistência (repositórios)
controllers/      casos de uso
views/            rotas HTTP, validação de entrada e serialização
middlewares/      tratamento de erros, conexão por requisição, guarda de operador
adapters/         notificações
```
