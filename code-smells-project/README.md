# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

## Configuração

Toda a configuração vem do ambiente (veja `.env.example`). Nada é lido fora de `config/settings.py`.

| Variável | Padrão | Efeito |
|---|---|---|
| `SECRET_KEY` | chave aleatória por processo | chave de assinatura do Flask |
| `APP_DEBUG` | `false` | modo debug (depurador interativo); nunca habilitar em host exposto |
| `APP_HOST` / `APP_PORT` | `0.0.0.0` / `5000` | endereço e porta do servidor |
| `DB_PATH` | `loja.db` | arquivo SQLite |
| `OPERATOR_TOKEN` | vazio | credencial do operador; vazio mantém `GET /relatorios/vendas` fechado (403) |

`GET /relatorios/vendas` exige o header `X-Operator-Token`. As rotas administrativas `/admin/reset-db` e `/admin/query` foram removidas.

## Estrutura

```
app.py            composição: monta repositórios, controllers e rotas
config/           leitura única do ambiente
models/           regras de domínio, persistência (SQLite) e erros de domínio
controllers/      casos de uso (valores simples entrada/saída)
views/            rotas Flask: parse, chama um controller, serializa
middlewares/      conexão por requisição, tratamento central de erros, guarda do operador
reports/          saída da skill refactor-arch (auditoria, inventário e baseline)
```
