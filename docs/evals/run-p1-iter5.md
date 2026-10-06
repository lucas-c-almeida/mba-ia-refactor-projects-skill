# Scorecard — `code-smells-project`, rodada 5 (`run/code-smells-project/iter5`)

- **Relatório avaliado:** `code-smells-project/reports/audit-20260930-1449.md` (congelado no gate, 29 findings)
- **Gabarito:** README §A.1 (25 itens) · **Rubrica:** [`rubric.md`](rubric.md)
- **Avaliado em:** 2026-10-02, pelo orquestrador (não pela sessão que executou a rodada)

## Casamento com o gabarito

| # | Item do gabarito | Estado | Finding(s) | Nota |
|---|---|---|---|---|
| 1 | SQL injection generalizado | ✓ | AP-02 `models.py:105-120` | Bypass do login observado; "systemic" com os demais sites |
| 2 | `/admin/query` executa SQL arbitrário | ✓ | AP-02 `app.py:59-78` | |
| 3 | `/admin/reset-db` sem autenticação | ✓ | AP-04 `app.py:47-57` | |
| 4 | `SECRET_KEY` hardcoded e vazada no `/health` | ✓ | AP-01 `app.py:7`, AP-18 `controllers.py:264-292` | |
| 5 | Senhas em texto puro, devolvidas pela API | ✓ | AP-08 `models.py:72-103`, AP-08 `models.py:122-131` | |
| 6 | Nenhuma autenticação em rota alguma | ✓ | AP-04 `app.py:11-30` | Inclui o IDOR de `/pedidos/usuario/<id>` |
| 7 | Debug + `0.0.0.0` | ✓ | AP-18 `app.py:80-88` | Debugger observado no boot |
| 8 | Pedido sem integridade | ◐ | AP-11 `controllers.py:188-220` | Quantidade negativa na Fase 2; itens repetidos burlando estoque só na re-auditoria (`missed-in-phase-2`, corrigido); transação não |
| 9 | Conexão SQLite global entre threads | ✓ | AP-07 `database.py:4-11` | |
| 10 | Sem separação de camadas | ✓ | AP-03 `models.py:1-314`, AP-03 `controllers.py:1-292` | Na R4 só `controllers.py`; agora o módulo que o gabarito aponta |
| 11 | N+1 na listagem de pedidos | ✓ | AP-10 `models.py:171-233` | |
| 12 | `try/except` duplicado vazando `str(e)` | ✓ | AP-09 `controllers.py:5-12` | |
| 13 | Validação ausente/inconsistente | ✓ | AP-11, AP-12 `controllers.py:64-96` | |
| 14 | Status de pedido sem checar existência | ◐ | — (re-auditoria) | Achado só na re-auditoria (`missed-in-phase-2`, proposto) |
| 15 | Regra de negócio e efeitos colaterais no controller | ✓ | AP-03 `controllers.py:1-292` | |
| 16 | Esquema sem restrições | ✓ | AP-20 `database.py:14-53` | |
| 17 | CORS aberto | ✗ | — | Nenhum finding nem observação |
| 18 | Dinheiro em ponto flutuante | ✓ | AP-20 `database.py:14-53` | |
| 19 | Schema e seed dentro de `get_db()` | ◐ | AP-01 `database.py:75-83` | Citado como contexto do seed, não como problema |
| 20 | `print` como log, com dados pessoais | ✓ | AP-08 `controllers.py:161-182` | ✗ na R4 |
| 21 | Magic numbers | ✓ | AP-15 `models.py:256-262`, AP-15 `controllers.py:242-250` | |
| 22 | Mapeamento linha→dict duplicado | ✓ | AP-12 `models.py:9-21` | ✗ na R4 |
| 23 | Relatório com 5 queries | ✓ | AP-10 `models.py:171-233` | Nomeado explicitamente na descrição; ✗ na R4 |
| 24 | Config hardcoded e imports mortos | ✓ | AP-17 `database.py:2`, AP-06 | Imports mortos achados (◐ na R4) |
| 25 | Nomes sombreando builtins; coluna `ativo` ignorada | ◐ | AP-16 `controllers.py:14` | Sombra de `id` citada; `ativo` não |

**20 ✓ · 4 ◐ · 1 ✗**

## Métricas

| Métrica | R4 | **R5** |
|---|---|---|
| Recall estrito | 16/25 (64%) | **20/25 (80%)** |
| Recall amplo | 21/25 (84%) | **24/25 (96%)** |
| Falsos positivos | 0 | **0** |
| Findings inventados | 0 (1 intervalo +1 linha) | **0** (29/29 referências exatas) |
| Achados além do gabarito | 3 | **3** — AP-19 flask-cors 5.0.1; AP-19 flask 3.1.1; AP-13 listagens sem limite |
| Regressões | 0 | **0** — 45 PASS |
| Entradas de segurança | 5 FIXED | **9 FIXED** |
| Intervenções humanas (correção de rumo) | 0 | **0** (resposta `y` no gate) |

## Observações

- O ganho de recall vem de LOW/MEDIUM que a R4 não arquivou (log com e-mail, mapeamento duplicado,
  agregação, imports mortos). Nenhuma mudança de catálogo entre R4 e R5 (contaminação declarada em
  `round5-changes.md`): a diferença é variância de execução, não ajuste.
- A Fase 2 continua sem ver duas regras de negócio de pedido (itens repetidos, existência no update
  de status); a re-auditoria viu as duas.
