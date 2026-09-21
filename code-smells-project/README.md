# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt -c constraints.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

A configuração vem do ambiente — veja `.env.example` (`SECRET_KEY`, `APP_DEBUG`, `APP_HOST`, `APP_PORT`, `DATABASE_PATH`, `APP_ENV`, `CORS_ORIGINS`). O modo debug fica desligado por padrão.

## Estrutura

```
app.py            raiz de composição (create_app) e ponto de entrada
config/           leitura e validação da configuração
models/           entidades, regras de negócio e repositórios (SQL)
controllers/      casos de uso, sem HTTP e sem SQL
views/            rotas HTTP e serialização das respostas
middlewares/      fronteira de erros e conexão por requisição
```
