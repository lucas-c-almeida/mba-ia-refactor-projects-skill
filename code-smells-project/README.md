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
app.py            composition root (create_app)
config/           leitura única do ambiente (settings.py)
models/           entidades, regras e persistência (SQLite), erros de domínio
controllers/      casos de uso (valores simples entrada/saída)
routes/           declaração das rotas (parse -> controller -> render)
middlewares/      fronteira de erros e guarda de operador
```

Convenção de nomes: o vocabulário de domínio (produtos, pedidos, usuários) e as rotas ficam em português, porque são o contrato da API; os termos técnicos de infraestrutura (`Settings`, `Database`, `create_app`) ficam em inglês.

## Configuração (variáveis de ambiente)

Veja `.env.example`. Pontos importantes:

- `APP_DEBUG` fica desligado por padrão.
- `SECRET_KEY` não tem valor embutido; sem ele, uma chave aleatória é gerada a cada processo.
- `OPERATOR_TOKEN` habilita `GET /relatorios/vendas` (enviar o header `x-operator-token`). Sem ele, a rota responde 403.
- As rotas `/admin/query` e `/admin/reset-db` foram removidas (executavam SQL recebido e apagavam todos os dados sem autenticação).
