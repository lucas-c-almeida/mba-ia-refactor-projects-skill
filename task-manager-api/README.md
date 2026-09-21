# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`.

## Estrutura

```
app.py            composition root (create_app)
config/           leitura do ambiente (única fonte de configuração)
models/           entidades, regras de domínio, repositórios, erros de domínio, relógio
controllers/      casos de uso (tasks, users/login, categories, reports)
routes/           rotas HTTP (views) e serializers das respostas
middlewares/      tratamento centralizado de erros
seed.py           dados iniciais
```

## Como rodar

```bash
pip install -r requirements.txt -c requirements.lock
export SECRET_KEY=<valor-aleatório-longo>      # obrigatório; ver .env.example
python seed.py                                  # senhas via SEED_*_PASSWORD ou geradas e impressas
python app.py                                   # ou: flask --app app run
```

A aplicação sobe em `http://localhost:5000` (`APP_HOST`/`APP_PORT` alteram). O modo debug fica
desligado a menos que `APP_DEBUG=true`. O `seed.py` popula o banco (`DATABASE_URL`, padrão SQLite
`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso
contrário os endpoints vão retornar listas vazias.
