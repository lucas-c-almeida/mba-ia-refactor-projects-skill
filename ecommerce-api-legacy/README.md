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

Veja `.env.example`. Variáveis lidas uma única vez em `src/config`:

- `PORT` (padrão 3000).
- `OPERATOR_TOKEN`: credencial das operações privilegiadas (`GET /api/admin/financial-report` e `DELETE /api/users/:id`), enviada no cabeçalho `X-Operator-Token`. Sem ela essas rotas respondem 403.

## Estrutura

`src/app.js` (raiz de composição) · `src/config` · `src/models` (domínio e persistência) · `src/controllers` (casos de uso) · `src/routes` (declaração de rotas) · `src/middlewares` (guarda de operador, fronteira de erros).
