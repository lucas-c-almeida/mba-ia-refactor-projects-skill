# Scorecard — `ecommerce-api-legacy`, rodada 4 (`run/ecommerce-api-legacy/iter4`)

- **Relatório avaliado:** `ecommerce-api-legacy/reports/audit-latest.md` na branch `round4` (17 findings)
- **Gabarito:** README §A.2 (21 itens)
- **Rubrica:** [`rubric.md`](rubric.md)
- **Avaliado em:** 2026-09-29, por sessão separada da que executou a rodada

## Casamento com o gabarito

| # | Item do gabarito | Estado | Finding(s) | Nota |
|---|---|---|---|---|
| 1 | Credenciais de produção hardcoded | ✓ | AP-01 `src/utils.js:1-7` | |
| 2 | Cartão e chave do gateway no log | ✓ | AP-08 `src/AppManager.js:45-46` | Confirmado em runtime |
| 3 | "Hash" reversível; senha padrão `123456` | ✓ | AP-08 `src/utils.js:17-23`, AP-01 `src/AppManager.js:66-71` | |
| 4 | Endpoints administrativos sem autenticação | ✓ | AP-04 ×2 | |
| 5 | God Class | ✓ | AP-03 `src/AppManager.js:1-142` | |
| 6 | Checkout associa compra a conta existente só pelo e-mail | ✗ | — | AP-11 e AP-20 tocam o e-mail, mas nenhum descreve a tomada de conta |
| 7 | Checkout sem transação; matrícula duplicada | ◐ | AP-09 `src/AppManager.js:131-137` | Falta de transação citada como observação dentro do AP-09 do DELETE; duplicidade não |
| 8 | Aprovação de pagamento simulada na rota | ✓ | AP-15 `src/AppManager.js:46`, AP-03 | |
| 9 | *Callback hell* | ✗ | — | O catálogo tem o sinal (AP-14, "structurally superseded constructs"); a cobertura do AP-14 não o registra como checado |
| 10 | N+1 no relatório financeiro | ✓ | AP-10 `src/AppManager.js:80-129` | Escalado a HIGH (N+1 aninhado) |
| 11 | Erros de banco ignorados | ✓ | AP-09 `src/AppManager.js:131-137` | O crash do processo no `err` ignorado (linha 92) não é citado |
| 12 | Exclusão deixa órfãos; sem FK; e-mail não único | ✓ | AP-20 `src/AppManager.js:12-16` | |
| 13 | Estado global mutável, cache sem limite | ✓ | AP-07 `src/utils.js:9-15` | |
| 14 | Validação de entrada ausente | ✓ | AP-11 `src/AppManager.js:29-35` | |
| 15 | Dependências transitivas deprecated no lockfile | ✗ | — | Camada 1/2 consultou só as 2 dependências diretas; o sinal "manifest/lockfile deprecation" não foi aplicado ao lockfile |
| 16 | Banco em memória | ✗ | — | O gabarito já admite que pode ser escolha de demo |
| 17 | Nomes crípticos | ✓ | AP-16 `src/AppManager.js:29-33` | |
| 18 | Respostas inconsistentes; sem error handler central | ◐ | AP-18 `src/app.js:1-14` | Ausência de middleware de erro citada; a inconsistência texto × JSON não |
| 19 | Mistura de `this` e `self` | ✗ | — | |
| 20 | Magic numbers e configuração fixa | ✓ | AP-15 `src/AppManager.js:46` | Os literais do `badCrypto` aparecem como instâncias adicionais |
| 21 | Import não usado | ✓ | AP-17 `src/utils.js:10` | |

**14 ✓ · 2 ◐ · 5 ✗**

## Métricas

| Métrica | Valor |
|---|---|
| Recall estrito | 14/21 = **67%** |
| Recall amplo | 16/21 = **76%** |
| Falsos positivos | **0** |
| Findings inventados | **0** — 17/17 referências existem e contêm o que a descrição diz. 1 imprecisão: `src/AppManager.js:1-142` num arquivo de 141 linhas |
| Achados além do gabarito | **1** na Fase 2 — AP-18: `NODE_ENV` nunca definido, a página de erro padrão do Express devolve stack trace com paths internos (confirmado em runtime). **+1 na re-auditoria** (`missed-in-phase-2`): senha do usuário do seed gravada como literal |
| Regressões | **0 não sancionadas** — 8 PASS, 1 REGRESSION sancionada (`checkout-malformed-json`: status 400 nos dois lados, corpo passou de página HTML com stack trace para texto seguro; D22) |
| Entradas de segurança | nenhuma no inventário |
| Intervenções humanas | **0** — o orquestrador retomou o subagente após interrupção por limite de turno, sem redirecionar conteúdo |

## Observações

- É o projeto com recall mais baixo, e os ✗ têm causa identificável na skill: o item 9 e o item 15
  são sinais que o catálogo **tem** e que a varredura por sinal não aplicou. É candidato a ajuste
  (a varredura do AP-14 deveria registrar os três sinais na cobertura, não só as camadas 1 e 2).
- O inventário não tem entradas de segurança, embora a rodada tenha corrigido o hash reversível e o
  log do cartão. Os dois são invisíveis pela superfície HTTP, o que é coerente; mas o AP-11 aplicado
  (rejeição de `c_id` não numérico) poderia ter tido uma entrada `rejected`.
