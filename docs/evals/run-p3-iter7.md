# Scorecard — `task-manager-api`, rodada 5 (`run/task-manager-api/iter7`)

- **Relatório avaliado:** `task-manager-api/reports/audit-20261001-1639.md` (congelado no gate, 28 findings)
- **Gabarito:** README §A.3 (23 itens) · **Rubrica:** [`rubric.md`](rubric.md)
- **Avaliado em:** 2026-10-02, pelo orquestrador

## Casamento com o gabarito

| # | Item do gabarito | Estado | Finding(s) | Nota |
|---|---|---|---|---|
| 1 | Hash de senha exposto | ✓ | AP-08 `models/user.py:16-25` | |
| 2 | Sem autenticação; qualquer um vira admin | ✓ | AP-04 `routes/user_routes.py:49-78`, AP-04 `:185-211` | Autoatribuição de `role` agora explícita (só o token na R4) |
| 3 | Credenciais hardcoded | ✓ | AP-01 ×3 | |
| 4 | MD5 sem salt | ✓ | AP-08 `models/user.py:27-32` | |
| 5 | Regra de negócio nas rotas | ✓ | AP-05 ×2, AP-03 | |
| 6 | Debug + `0.0.0.0` | ✓ | AP-18 `app.py:33-34` | `/console` observado |
| 7 | N+1 | ✓ | AP-10 `routes/task_routes.py:41-57` | Os quatro sites na descrição |
| 8 | Relatórios com dezenas de `COUNT` | ◐ | AP-13, AP-03 | `Task.query.all()` do relatório citado; a sequência de `COUNT` não |
| 9 | Validação de tipos → 500 | ✓ | AP-11 `routes/task_routes.py:110-114` | |
| 10 | "Atrasada" duplicada | ✓ | AP-12 `routes/task_routes.py:30-39` | |
| 11 | Validação duplicada; helpers não usados | ✓ | AP-12 `:89-124`, AP-17 `utils/helpers.py:57-108` | |
| 12 | APIs deprecated (`Query.get`, `utcnow`) | ✓ | AP-14 `models/task.py:15-16`, AP-14 `routes/task_routes.py:42` | **As duas na Fase 2** (◐ na R4) |
| 13 | `except:` sem tipo | ✓ | AP-09 `routes/task_routes.py:62-63` | |
| 14 | Categoria órfã | ✓ | AP-20 `models/task.py:11-14` | |
| 15 | Sem paginação | ✓ | AP-13 `routes/task_routes.py:14` | |
| 16 | CORS aberto | ◐ | AP-19 `requirements.txt:3` | Pelo ângulo do advisory do `CORS(app)` padrão; o wildcard de origem só aparece na proposta da Fase 3 |
| 17 | Serialização duplicada do `to_dict` | ✓ | AP-12 `routes/task_routes.py:30-39` | ✗ na R4 |
| 18 | Código morto e dependências não usadas | ✓ | AP-17, AP-19 `requirements.txt:4-6` | |
| 19 | Imports não usados | ✓ | AP-17 `routes/task_routes.py:7` | |
| 20 | Magic numbers | ✓ | AP-15 `utils/helpers.py:110-116` | |
| 21 | `print` como log | ✗ | — | |
| 22 | Config hardcoded e `create_all` na importação | ✓ | AP-06 `app.py:9-31` | |
| 23 | Condicionais verbosas | ✗ | — | |

**19 ✓ · 2 ◐ · 2 ✗**

## Métricas

| Métrica | R4 | **R5** |
|---|---|---|
| Recall estrito | 18/23 (78%) | **19/23 (83%)** |
| Recall amplo | 20/23 (87%) | **21/23 (91%)** |
| Falsos positivos | 0 | **0** |
| Findings inventados | 0 (1 intervalo +1 linha) | **0** (28/28 referências exatas) |
| Achados além do gabarito | 2 | **2** — AP-19 flask-cors 4.0.0 com advisory HIGH alcançável; AP-16 o módulo de relatórios hospeda a API de categorias, com contadores `p1..p5` |
| Regressões | 0 | **0** — 53 PASS |
| Entradas de segurança | 2 FIXED · 1 NOT FIXED | **6 FIXED** |
| Intervenções humanas | 0 | **0** (resposta `y` no gate; retomada após limite de API pelo orquestrador) |

## Observações

- Ordenação por severidade correta (falhou na R4).
- R5-6: a recomendação do flask-cors 4.0.2 afirmou, sem verificar, que não exigia configuração;
  o próprio subagente corrigiu na Fase 3 (`audit-latest.md`), mantendo o relatório congelado.
