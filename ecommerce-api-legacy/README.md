# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000` (ou na porta definida em `PORT`). O banco SQLite é em
memória por padrão (`DB_PATH`) e já carrega seeds automaticamente no boot. As variáveis aceitas estão
em `.env.example`.

Exemplos de requisições estão em `api.http`.

## Estrutura

```
src/
├── app.js            composition root (config → banco → repositórios → controllers → rotas)
├── config/           leitura única do ambiente
├── models/           entidades, regras e persistência (repositórios, schema/seed)
├── controllers/      casos de uso (checkout, relatório financeiro, usuários)
├── routes/           rotas HTTP (parse → controller → resposta)
└── middlewares/      tratamento centralizado de erros
```
