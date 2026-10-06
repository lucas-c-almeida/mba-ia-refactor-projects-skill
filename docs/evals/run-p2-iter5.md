# Scorecard — `ecommerce-api-legacy`, rodada 5 (`run/ecommerce-api-legacy/iter5`)

- **Relatório avaliado:** `ecommerce-api-legacy/reports/audit-20261001-1550.md` (congelado no gate, 17 findings)
- **Gabarito:** README §A.2 (21 itens) · **Rubrica:** [`rubric.md`](rubric.md)
- **Avaliado em:** 2026-10-02, pelo orquestrador

## Casamento com o gabarito

| # | Item do gabarito | Estado | Finding(s) | Nota |
|---|---|---|---|---|
| 1 | Credenciais de produção hardcoded | ✓ | AP-01 `src/utils.js:1-7` | Inclui a senha literal do seed (na R4, só na re-auditoria) |
| 2 | Cartão e chave do gateway no log | ✓ | AP-08 `src/AppManager.js:45` | |
| 3 | "Hash" reversível; senha padrão | ✓ | AP-08 `src/utils.js:17-23`, AP-03 | |
| 4 | Endpoints administrativos sem autenticação | ✓ | AP-04 `src/AppManager.js:131-137` | Cobre DELETE e relatório |
| 5 | God Class | ✓ | AP-03 `src/AppManager.js:1-141` | |
| 6 | Compra associada a conta existente só pelo e-mail | ✗ | — | Igual à R4 |
| 7 | Checkout sem transação | ✓ | AP-09 `src/AppManager.js:50-63` | Agora é o assunto do finding (◐ na R4) |
| 8 | Pagamento simulado na rota | ✓ | AP-15 `src/AppManager.js:46`, AP-03 | |
| 9 | *Callback hell* | ✗ | — | Os contadores manuais são citados no AP-10, sem nomear o padrão. Correção de catálogo adiada de propósito |
| 10 | N+1 no relatório | ✓ | AP-10 `src/AppManager.js:83-127` | |
| 11 | Erros de banco ignorados; crash | ✓ | AP-09, AP-11 | Crash do processo observado (AP-11) |
| 12 | Órfãos; sem FK; e-mail não único | ✓ | AP-20 `src/AppManager.js:12-16` | |
| 13 | Estado global mutável | ✓ | AP-07 `src/utils.js:9-15` | |
| 14 | Validação ausente | ✓ | AP-11 `src/AppManager.js:29-46` | |
| 15 | Transitivas deprecated no lockfile | ◐ | AP-19 `package.json:11` | Mesma cadeia (sqlite3 → tar, node-gyp…), pelo ângulo de advisory, não de deprecation (✗ na R4) |
| 16 | Banco em memória | ✗ | — | |
| 17 | Nomes crípticos | ✓ | AP-16 `src/AppManager.js:29-33` | |
| 18 | Respostas inconsistentes; sem handler central | ◐ | AP-18 `src/app.js:5-14` | |
| 19 | `this` × `self` | ✓ | AP-16 `src/AppManager.js:29-33` | ✗ na R4 |
| 20 | Magic numbers e config fixa | ✓ | AP-15 `src/AppManager.js:46` | Inclui `10000` e a porta |
| 21 | Import não usado | ✓ | AP-17 `src/AppManager.js:2` | |

**16 ✓ · 2 ◐ · 3 ✗**

## Métricas

| Métrica | R4 | **R5** |
|---|---|---|
| Recall estrito | 14/21 (67%) | **16/21 (76%)** |
| Recall amplo | 16/21 (76%) | **18/21 (86%)** |
| Falsos positivos | 0 | **0** |
| Findings inventados | 0 (1 intervalo +1 linha) | **0** (17/17 referências exatas) |
| Achados além do gabarito | 1 (+1 re-auditoria) | **2** — AP-19 advisories nas transitivas do express (ReDoS em `path-to-regexp`, `qs`, `body-parser`); AP-18 `NODE_ENV` com stack trace. **+1 na Fase 3:** upstream do sqlite3 sem manutenção (Tier C) |
| Regressões | 0 (1 sancionada) | **0** — 9 PASS, 1 UNVERIFIED declarado |
| Entradas de segurança | — | **2 FIXED** |
| Intervenções humanas | 0 | **0** (resposta `y` no gate) |

## Observações

- Classificação a corrigir (R5-3): dois findings contados como `unresolved (failed)` têm como resto
  exatamente o que o gate de contrato segurou; pela D14.1 são `proposed` (12 / 5 / 0).
