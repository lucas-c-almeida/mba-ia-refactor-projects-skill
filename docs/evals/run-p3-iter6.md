# Scorecard — `task-manager-api`, rodada 4 (`run/task-manager-api/iter6`)

- **Relatório avaliado:** `task-manager-api/reports/audit-latest.md` na branch `round4` (31 findings)
- **Gabarito:** README §A.3 (23 itens)
- **Rubrica:** [`rubric.md`](rubric.md)
- **Avaliado em:** 2026-09-29, por sessão separada da que executou a rodada

## Casamento com o gabarito

| # | Item do gabarito | Estado | Finding(s) | Nota |
|---|---|---|---|---|
| 1 | Hash de senha exposto em toda resposta de usuário | ✓ | AP-08 `models/user.py:16-25` | Escalado a CRITICAL pela composição com AP-04 |
| 2 | Sem autenticação real; qualquer um se cadastra como admin | ✓ | AP-04 `routes/task_routes.py:1-299` | O token decorativo é citado; a autoatribuição de `role: admin` não |
| 3 | Credenciais hardcoded | ✓ | AP-01 `app.py:13`, AP-01 `services/notification_service.py:7-10` | |
| 4 | MD5 sem salt | ✓ | AP-08 `models/user.py:27-32` | |
| 5 | Regra de negócio nas rotas; `services/` não usado | ✓ | AP-05 ×3 | |
| 6 | Debug + `0.0.0.0` | ✓ | AP-18 `app.py:34` | |
| 7 | N+1 | ✓ | AP-10 ×4 | Os quatro sites do gabarito |
| 8 | Relatórios com dezenas de `COUNT` e agregação em Python | ◐ | AP-10 `routes/report_routes.py:53-68` | O `Task.query.all()` é citado como observação; a sequência de `COUNT` não |
| 9 | Validação de tipos ausente → 500 | ✓ | AP-11 ×2 | |
| 10 | Lógica de "atrasada" duplicada em 6 lugares | ✓ | AP-12 `routes/task_routes.py:30-39` | Os seis sites, e o método do model não usado |
| 11 | Validação de tarefa duplicada; helpers não usados | ✓ | AP-12 `routes/task_routes.py:110-114` | |
| 12 | APIs deprecated (`Query.get`, `datetime.utcnow`) | ◐ | AP-14 `seed.py:66-74` | `utcnow` só achado na Fase 3a, depois do gate (o check da Fase 2 só importou o app); `Query.get` (`LegacyAPIWarning`) não achado |
| 13 | `except:` sem tipo | ✓ | AP-09 `routes/task_routes.py:146-154` | |
| 14 | Exclusão de categoria deixa tarefas órfãs | ✓ | AP-20 `routes/report_routes.py:211-223` | |
| 15 | Listagens sem paginação | ✓ | AP-13 `routes/task_routes.py:11-63` | |
| 16 | CORS aberto | ✓ | AP-18 `app.py:15` | |
| 17 | Serialização manual duplicada do `to_dict` | ✗ | — | |
| 18 | Código morto e dependências não usadas | ✓ | AP-17 ×2, AP-19 `requirements.txt:4-6` | |
| 19 | Imports não usados | ✓ | AP-17 `routes/task_routes.py:7` | |
| 20 | Magic numbers | ✓ | AP-15 `models/task.py:45-48` | |
| 21 | `print` como log | ✗ | — | |
| 22 | Config hardcoded e `create_all` na importação | ✓ | AP-06 `app.py:1-34` | |
| 23 | Condicionais verbosas | ✗ | — | |

**18 ✓ · 2 ◐ · 3 ✗**

## Métricas

| Métrica | Valor |
|---|---|
| Recall estrito | 18/23 = **78%** |
| Recall amplo | 20/23 = **87%** |
| Falsos positivos | **0** |
| Findings inventados | **0** — 31/31 referências existem e contêm o que a descrição diz. 1 imprecisão: `utils/helpers.py:1-117` num arquivo de 116 linhas |
| Achados além do gabarito | **2** — AP-19 `flask-cors` 4.0.0 com advisory HIGH alcançável (CVE-2024-6221; o gabarito disse não ter verificado CVEs, A.5); AP-12 regex de e-mail repetida em três lugares |
| Regressões | **0** — 24 PASS |
| Entradas de segurança | 2 FIXED, 1 NOT FIXED (esperado: o finding correspondente, AP-20, ficou em `PROPOSED, NOT APPLIED`) |
| Intervenções humanas | **0** |

## Observações

- A lacuna do item 12 é a R4-6 do relatório da rodada: a camada 1 do AP-14 só exercitou o código de
  importação. `Query.get` também só emite warning quando a rota roda.
- **Ordenação por severidade violada**, já no arquivo congelado no gate
  (`audit-20260925-1921.md`): o `[MEDIUM] Insecure Runtime Configuration — permissive cross-origin
  policy` vem depois dos quatro `[LOW]`. No `audit-latest.md` o AP-14 acrescentado depois do gate
  também ficou no fim. É um item do checklist avaliado (`Findings ordenados por severidade`).
- Inconsistência do próprio relatório: `## Verification Coverage` declara um `INCIDENT` (três
  `Remove-Item` encadeados por `;`) e a linha de validação imprime `✓ Processes: ... 0 incidents`.
  Corrigido no template pela D25 (a linha `Commands:` separada).
