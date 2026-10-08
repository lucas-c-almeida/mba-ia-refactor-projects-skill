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

Veja `.env.example`. `PORT` (padrão 3000) e `OPERATOR_TOKEN`. As rotas privilegiadas
(`GET /api/admin/financial-report` e `DELETE /api/users/:id`) respondem 403 enquanto
`OPERATOR_TOKEN` não estiver definido; com ele definido, envie o valor no header `x-operator-token`.
