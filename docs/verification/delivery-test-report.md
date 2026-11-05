# Relatório da verificação independente da entrega (`release/delivery-r6`)

- **Data:** 2026-10-13 · **Código verificado:** `364bd60` · **Original:** `7ef5932`
- **Método:** três subagentes independentes (um por projeto), cada um com um worktree da entrega e um do
  original, plano em [`delivery-test-plan.md`](delivery-test-plan.md). Requisições escritas à mão; o
  replay da skill não foi usado como prova. Windows, Python 3.13, Node 24, sem container.
- **Natureza da evidência:** relatório de cada subagente, consolidado pelo orquestrador. Os scripts e as
  saídas ficaram no scratch da sessão e **não** estão versionados.

## Resultado

| | P1 `code-smells-project` | P2 `ecommerce-api-legacy` | P3 `task-manager-api` |
|---|---|---|---|
| Provisiona do zero e sobe | PASS | PASS | PASS |
| Contrato igual ao original (status/shape) | PASS, 0 regressão | PASS, 0 regressão | PASS, 0 regressão |
| Operações privilegiadas (D27) | PASS | PASS | PASS |
| Negócio permanece aberto | PASS | PASS | PASS |
| Robustez ("nunca 500") | PARCIAL (2 casos) | PASS | PARCIAL (4 casos) |
| Fluxo ponta a ponta com valores | PASS | PASS | PASS (21 asserts) |
| Migração de banco legado | n/a (não testado) | n/a (banco em memória) | PASS |
| `git status` limpo no fim | PASS | PASS | PASS |
| Conferência cruzada com `probe` | 34 PASS, 0 REGRESSION | NOT RUN | NOT RUN |

Guarda de operador, nos três: 403 sem `OPERATOR_TOKEN` no ambiente; 403 com header ausente, vazio,
errado, prefixo, sufixo, outra caixa, `Bearer`; 403 em variações de caminho; com o token correto,
status e shape do original. P1: `POST /admin/reset-db` e `POST /admin/query` respondem 404 em todos os
métodos (o original executava o reset até em `//admin/reset-db`).

## Defeitos encontrados (nenhum é regressão; não corrigidos)

| # | Projeto | Descrição | Original |
|---|---|---|---|
| 1 | P1 | `GET /produtos/<int gigante>` e `POST /produtos` com `estoque` gigante → 500 (estouro de inteiro do SQLite) | 404 / 201 |
| 2 | P1 | `POST /pedidos` com `itens` numérico → 500 (`len(itens)` antes de validar a lista) | 500 |
| 3 | P3 | `POST /tasks` com `tags` objeto → 500 | 500 |
| 4 | P3 | `PUT /users/<id>` com `active:"maybe"` → 500 | 500 |
| 5 | P3 | `PUT /categories/<id>` com `name` lista → 500 | 500 |
| 6 | P3 | `GET /tasks/<int gigante>` → 500 | 500 |

## Observações

- `.env.example` do P2 traz `OPERATOR_TOKEN=change-me`: se alguém copiar sem trocar, a guarda aceita
  esse valor conhecido.
- P3: `python app.py` com outro diretório corrente cria o banco em `instance/` relativo ao CWD; o README
  não avisa. `SEED_PASSWORD` só é lida pelo `seed.py`.
- `surface.json`/`baseline.json` guardam senhas do seed original e o token fixture do replay.
- O seed do P1 cria `admin@loja.com` com senha conhecida (proposta já registrada no relatório de auditoria).
- Divergências intencionais confirmadas: 500 → 400 em tipos errados; 200 → 400 em corpo array no
  `PUT` de tarefa e de categoria (P3); array como senha no checkout (P2); mensagens de erro
  centralizadas; senhas mascaradas; hash forte com migração no login; relatório do P2 com ordem
  determinística.

## Não testado

Boot com ambiente totalmente vazio e com o `.env.example` literal (o código não lê `.env`); concorrência;
segundo boot sobre banco já migrado e migração que viola `CHECK` (P3); caminho de upgrade de hash legado
no P1; corrida de checkouts no P2; 500 interno real no P2; cobertura por amostragem (~243 requisições no
P1, ~140 pares no P3), e não por mutação.

## Incidente de processo

O verificador do P1 deixou dois processos vivos (app da entrega na 5101 e launcher do original na 5201)
que o sistema de permissões não deixou encerrar. Ficam para encerramento manual pelo autor.
