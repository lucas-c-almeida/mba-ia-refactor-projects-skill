# Rodada 2 — lista de mudanças congelada

- **Data do congelamento:** 2026-09-21
- **Origem:** os 13 problemas da skill listados em [`docs/rounds/round1-report.md`](round1-report.md),
  seção "Problemas da skill revelados nesta rodada".
- **Regra:** na rodada 2, a skill só muda em pontos atribuíveis a um item desta lista. Esta lista foi
  commitada **antes** de existir o gabarito da seção A do README. Assim, nenhum item do gabarito
  entra no catálogo sem ficar visível (D12, em sua forma enfraquecida: o autor já leu o relatório da
  rodada 1, mas não o gabarito).
- **Restrição permanente (CLAUDE.md §2):** toda correção é escrita como sinal observável e raciocínio,
  nunca como a instância da rodada 1, e precisa passar no Teste do Quarto Projeto.

## Decisões tomadas antes da implementação

| Item | Decisão |
|---|---|
| #6 Autorização | **Teste do "uso legítimo".** Sem modelo de identidade, todo cliente atual receberia o 401, então é mudança de contrato → `PROPOSED`. Com identidade, mas sem checagem de dono ou papel, só o uso ilegítimo é rejeitado → aplicado. |
| #3 Escrita na Fase 2 | A Fase 2 executa a aplicação a partir de uma **cópia descartável** (worktree ou cópia temporária) fora do alvo. A regra de escrita de D5/D10 continua como está. |
| #11 Finding parcial | **Não existe categoria "parcial".** `Findings resolved: X resolved, Y proposed, Z unresolved`. Um finding só conta como `resolved` se foi resolvido por inteiro. Se sobrou alguma parte, conta como `unresolved` (ou `proposed`, se o que sobrou foi barrado pelo gate de contrato), e a descrição diz o que foi e o que não foi corrigido. |
| Seção A (gabarito) | Sessão nova numa worktree do commit `6d1ce62` (sem CLAUDE.md, skill ou relatórios). Lucas revisa o resultado, mas não o escreve. |

## Mudanças planejadas

### W1 — Protocolo de validação e harness
Arquivos: `06-validation-protocol.md`, `probe.py`, `probe.mjs`.

| # | Mudança |
|---|---|
| 4 | Erro de transporte no baseline conta como **falha** (spec §4), não como `UNVERIFIED`. Se o replay tiver sucesso, o resultado é `PASS (improved from transport error)`. Alinhar `probe.mjs` à spec. |
| 5 | Corpo que não é JSON: comparar um **esqueleto normalizado** (números, UUIDs e timestamps mascarados, o resto preservado) em vez de tratá-lo como `opaque`. |
| 9 | Entrada de superfície `kind: security` com `finding: AP-xx` e `expect: changed`. Rejeitada no replay → `FIXED`; inalterada → `NOT FIXED`. Nunca vira `REGRESSION`. |
| 10 | Capturar uma **allowlist normativa de headers de contrato**: `Content-Type`, `Location`, `Access-Control-*`, `WWW-Authenticate` e os nomes dos `Set-Cookie`. |
| 12 | Entrada adicionada depois do baseline é **capturada contra o original**, subindo o commit anterior à refatoração numa worktree temporária. |
| — | **Teste de conformidade:** as mesmas fixtures rodam nos dois probes, e as saídas precisam ser byte-idênticas. |

### W2 — Ambiente e execução
Arquivos: `SKILL.md`, `01-project-analysis.md`.

| # | Mudança |
|---|---|
| 1 | Ordem para escolher a porta: override do framework (CLI ou variável de ambiente) → porta nativa, com baseline e replay em sequência, nunca ao mesmo tempo → launcher **fora da árvore** que importa a aplicação. O original nunca é editado. |
| 2 | Instalar as dependências **declaradas pelo próprio alvo** num ambiente isolado, fora da árvore ou ignorado pelo git, é permitido e fica registrado no relatório. Adicionar uma dependência nova continua proibido. |
| 3 | Ver decisão acima. Artefatos de runtime vão para a cópia descartável. |
| — | A skill **nunca altera o índice nem o histórico do git**. A remoção de arquivos da D9 é feita pelo sistema de arquivos. |

### W3 — Catálogo e playbook
Arquivos: `02-antipattern-catalog.md`, `05-refactoring-playbook.md`, `03-report-template.md`.

| # | Mudança |
|---|---|
| 7 | Nova **AP-18 Insecure Runtime Configuration** (OWASP A05), com RP correspondente e código antes/depois. |
| 8 | Nova **AP-19 Known-Vulnerable Dependency** (OWASP A06), separada de AP-14. A regra de evidência é a da D13 (fonte + data). |
| 13 | AP-01 passa a cobrir credenciais literais em dados que chegam ao datastore de runtime. AP-11 passa a incluir invariantes de domínio. O error handler padrão que expõe stack trace entra em AP-18. A Fase 2 faz uma **varredura por entrada do catálogo** e grava uma tabela de cobertura no relatório. |
| — | A re-auditoria ganha a classe **`missed-in-phase-2`**: finding em código que a refatoração não tocou. |

### W4 — Consistência do gate de contrato
Arquivos: `04-architecture-guidelines.md`, RP-04, `SKILL.md`, `03-report-template.md`.

| # | Mudança |
|---|---|
| 6 | Ver decisão acima, com o mesmo texto nos três lugares. |
| 10 | Patch ou minor dentro da mesma major é seguro. Major, ou versão cujo changelog cita mudança de comportamento, só é seguro se o replay, agora com headers, cobrir o comportamento afetado. Caso contrário, vira `PROPOSED`. |
| 11 | Ver decisão acima. |

### Especificação
D15–D18 em `CLAUDE.md` §8 e em `docs/decisions.md`: autorização (#6), cópia descartável na Fase 2 (#3), entradas de segurança na superfície (#9) e upgrade de dependência versus contrato (#10).
