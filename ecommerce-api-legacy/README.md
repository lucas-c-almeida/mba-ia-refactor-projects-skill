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
| `PORT` | não (padrão `3000`) | Porta HTTP |
| `OPERATOR_TOKEN` | não | Credencial de operador. As rotas `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem o header `X-Operator-Token` com este valor. **Sem a variável definida (ou vazia), essas rotas respondem `403`.** |

```bash
export OPERATOR_TOKEN=<um valor longo e aleatório>
npm start
```

## Estrutura

```
src/
├── app.js           composition root: configuração, wiring, rotas, error handler, listen
├── config/          leitura e validação do ambiente
├── models/          regras de domínio, schema/seed e repositórios (persistência)
├── controllers/     casos de uso (checkout, relatório financeiro, remoção de usuário)
├── views/           rotas HTTP e validação de entrada
└── middlewares/     guard de operador, error boundary, adaptador async
```
