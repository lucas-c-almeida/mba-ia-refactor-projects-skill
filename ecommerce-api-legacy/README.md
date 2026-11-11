# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Configuração

A aplicação não carrega arquivo `.env`: exporte as variáveis no ambiente antes de `npm start`.

| Variável | Obrigatória | Efeito |
|---|---|---|
| `PORT` | não | Porta HTTP. Padrão: `3000`. |
| `OPERATOR_TOKEN` | não | Credencial de operador exigida no header `X-Operator-Token` por `GET /api/admin/financial-report` e `DELETE /api/users/:id`. **Sem ela, as duas rotas respondem `403`.** |
| `SEED_USER_PASSWORD` | não | Senha da conta de demonstração criada no boot. Sem ela, é gerada uma senha aleatória. |

## Estrutura

```
src/
├── app.js            composition root: configuração, objetos, rotas, servidor
├── config/           leitura do ambiente (único ponto)
├── models/           regras de domínio, erros, schema/seed e repositórios
├── controllers/      casos de uso (checkout, relatório, remoção de conta)
├── routes/           rotas HTTP e validação de entrada
└── middlewares/      guarda de operador, id de requisição, tratamento de erros
```
