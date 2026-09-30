# Scorecard — `code-smells-project`, rodada 4 (`run/code-smells-project/iter4`)

- **Relatório avaliado:** `code-smells-project/reports/audit-latest.md` na branch `round4` (19 findings)
- **Gabarito:** README §A.1 (25 itens)
- **Rubrica:** [`rubric.md`](rubric.md)
- **Avaliado em:** 2026-09-29, por sessão separada da que executou a rodada

## Casamento com o gabarito

| # | Item do gabarito | Estado | Finding(s) | Nota |
|---|---|---|---|---|
| 1 | SQL injection generalizado | ✓ | AP-02 `models.py:289-297` | Lista os demais sites na descrição, inclusive o login |
| 2 | `/admin/query` executa SQL arbitrário | ✓ | AP-02 `app.py:59-78` | |
| 3 | `/admin/reset-db` sem autenticação | ✓ | AP-04 `app.py:47-58` | |
| 4 | `SECRET_KEY` hardcoded e vazada no `/health` | ✓ | AP-01 `app.py:7`, AP-18 `app.py:8` | |
| 5 | Senhas em texto puro, devolvidas pela API | ✓ | AP-08 `models.py:105-120` | |
| 6 | Nenhuma autenticação; login não emite sessão | ✓ | AP-04 `app.py:47-58` | Descrito como causa raiz no mesmo finding |
| 7 | Debug ligado + `0.0.0.0` | ✓ | AP-18 `app.py:8` | Confirmado em runtime (PIN do debugger no log) |
| 8 | Pedido sem integridade (quantidade negativa, itens repetidos, sem transação) | ◐ | AP-11 `controllers.py:188-220` | Só a quantidade negativa; itens repetidos burlando estoque e ausência de transação não aparecem |
| 9 | Conexão SQLite global compartilhada entre threads | ✓ | AP-07 `database.py:4-11` | |
| 10 | Sem separação de camadas (`models.py` + `app.py`) | ◐ | AP-03 `controllers.py:1-293`, AP-06 | God Module identificado em `controllers.py`, não em `models.py`, que o gabarito aponta como o módulo principal |
| 11 | N+1 na listagem de pedidos | ✓ | AP-10 `models.py:171-233` | |
| 12 | `try/except` duplicado vazando `str(e)` | ✓ | AP-09 `controllers.py:5-12` | |
| 13 | Validação ausente/inconsistente | ✓ | AP-11, AP-12 `controllers.py:24-96` | Divergência criar × atualizar é o assunto do AP-12 |
| 14 | Status de pedido sem checar existência; cancelamento não devolve estoque | ◐ | AP-11 `controllers.py:188-220` | Só a existência (200 para pedido inexistente); estoque e transições não |
| 15 | Regra de negócio e efeitos colaterais no controller | ✓ | AP-03 `controllers.py:1-293` | SQL direto no `health_check`, lista de categorias |
| 16 | Esquema sem restrições (email único, FKs) | ✓ | AP-20 `database.py:14-53` | |
| 17 | CORS aberto para qualquer origem | ◐ | AP-19 `requirements.txt:2` | Só como observação ("the app's own policy is already allow every origin") |
| 18 | Dinheiro em ponto flutuante | ✓ | AP-20 `database.py:14-53` | |
| 19 | Schema e seed dentro de `get_db()` | ✓ | AP-16 `database.py:7-86` | |
| 20 | `print` como log, com dados pessoais | ✗ | — | Catálogo de cobertura diz que viu os `print` com e-mails e não arquivou |
| 21 | Magic numbers e listas mágicas | ✓ | AP-15 `models.py:256-262` | |
| 22 | Mapeamento linha→dict duplicado | ✗ | — | |
| 23 | Relatório com 5 queries onde um `GROUP BY` basta | ✗ | — | |
| 24 | Config hardcoded e imports mortos | ◐ | AP-06 `database.py:4-11` | Caminho do banco citado; AP-17 declarou "none found" para imports não usados, que o gabarito aponta |
| 25 | Nomes sombreando builtins; coluna `ativo` ignorada | ✗ | — | |

**16 ✓ · 5 ◐ · 4 ✗**

## Métricas

| Métrica | Valor |
|---|---|
| Recall estrito | 16/25 = **64%** |
| Recall amplo | 21/25 = **84%** |
| Falsos positivos | **0** |
| Findings inventados | **0** — 19/19 referências existem e o intervalo contém o que a descrição diz. 1 imprecisão: `controllers.py:1-293` num arquivo de 292 linhas (intervalo de arquivo inteiro, uma linha além do fim) |
| Achados além do gabarito | **3** — AP-19 `flask-cors` 5.0.1 (3 advisories, OSV.dev); AP-19 `flask` 3.1.1 (1 advisory, LOW); AP-13 listagens sem paginação |
| Regressões | **0** — 25 PASS, 1 UNVERIFIED (`sqli-search`, limitação do shape; verificado manualmente) |
| Entradas de segurança | 5 FIXED, 0 NOT FIXED |
| Intervenções humanas | **0** |

## Observações

- Os ✗ se concentram em LOW/MEDIUM de legibilidade e performance (itens 20, 22, 23, 25). Nenhum
  CRITICAL ou HIGH do gabarito ficou sem ser visto.
- Divergência de julgamento, não erro: a skill arquivou as credenciais do seed como CRITICAL (AP-01);
  o gabarito decidiu não listá-las à parte (A.5).
- Os reexames usados neste scorecard (conferência das 19 referências e reclassificação offline do
  replay com `probe.py compare --current`) estão descritos na seção C do README.
