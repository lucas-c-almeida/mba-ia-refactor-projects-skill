# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
export SECRET_KEY=...       # obrigatório; demais chaves em .env.example
python seed.py
python app.py               # ou: flask --app app run
```

A configuração vem de variáveis de ambiente: `SECRET_KEY` (obrigatória), `DATABASE_URL`, `HOST`, `PORT`, `FLASK_DEBUG`, `LOG_LEVEL` — ver `.env.example`.

Estrutura: `models/` (entidades, regras e repositórios), `controllers/` (casos de uso), `routes/` (rotas e apresentação das respostas), `middlewares/` (tratamento centralizado de erros), `config/` (configuração), `app.py` (composition root).

A aplicação sobe em `http://localhost:5000` por padrão. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.
