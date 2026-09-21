# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py                       # ou: flask --app app.py run --port 5000
```

A aplicação sobe em `http://127.0.0.1:5000` por padrão. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas armazenadas com hash).

## Configuração

Toda configuração vem do ambiente (veja `.env.example`):

| Variável | Padrão | Uso |
|---|---|---|
| `SECRET_KEY` | aleatória por processo (com aviso no log) | chave de assinatura do Flask |
| `DATABASE_PATH` | `loja.db` | arquivo SQLite |
| `APP_ENV` | `producao` | informado em `/health` |
| `APP_HOST` / `APP_PORT` | `127.0.0.1` / `5000` | bind do `python app.py` |
| `APP_DEBUG` | `false` | modo debug (nunca habilitar em rede aberta) |

## Estrutura

```
app.py            composition root (create_app)
config/           leitura do ambiente
models/           domínio: repositórios, regras, constantes, erros
controllers/      casos de uso (sem HTTP)
views/            rotas (blueprints), validação de entrada, serialização
middlewares/      tratamento central de erros, contexto por requisição
```
