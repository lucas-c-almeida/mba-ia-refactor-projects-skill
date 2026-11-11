# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`, agora organizada em camadas MVC:

```
app.py            raiz de composição (create_app): configuração, repositórios, controllers, rotas
config/           leitura do ambiente (único módulo que lê variáveis de ambiente)
models/           entidades, regras de domínio, repositórios (todas as queries), erros, relógio
controllers/      casos de uso (tarefas, usuários, categorias, relatórios)
routes/           camada de entrega: rotas, validação de entrada, serialização das respostas
middlewares/      tratamento centralizado de erros e credencial de operador
seed.py           popula o banco com dados de exemplo
```

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**. As senhas dos usuários de exemplo são geradas a cada execução e impressas uma única vez.

## Configuração

A aplicação não carrega arquivo `.env`: **exporte** as variáveis abaixo no ambiente do processo. Todas são opcionais.

| Variável | Padrão | Efeito |
|---|---|---|
| `OPERATOR_TOKEN` | vazio (fechado) | Credencial de operador, enviada no header `X-Operator-Token`. Exigida por `GET /reports/summary`, `DELETE /users/<id>` e por um `PUT /users/<id>` que altere `email`, `password`, `role` ou `active`. Sem valor, essas operações respondem `403`. |
| `SECRET_KEY` | aleatória por processo | Chave de assinatura do Flask. |
| `DATABASE_URL` | `sqlite:///tasks.db` | Banco de dados (caminho SQLite relativo à pasta `instance/` do projeto). |
| `APP_DEBUG` | `false` | Modo debug do servidor. Nunca ligue em um host acessível pela rede. |
| `APP_HOST` | `0.0.0.0` | Endereço de bind. |
| `APP_PORT` | `5000` | Porta. |
