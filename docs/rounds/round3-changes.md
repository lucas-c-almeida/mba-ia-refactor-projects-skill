# Rodada 3 — lista de mudanças congelada

- **Data do congelamento:** 2026-09-21
- **Origem:** o incidente R2-1 e os problemas R2-2 a R2-12 de
  [`docs/rounds/round2-report.md`](round2-report.md), seção "Problemas da skill revelados nesta
  rodada".
- **Regra:** na rodada 3, a skill só muda em pontos atribuíveis a um item desta lista.
- **Restrição permanente (CLAUDE.md §2):** toda correção é escrita como sinal observável e raciocínio,
  nunca como a instância da rodada 2, e precisa passar no Teste do Quarto Projeto.

## ⚠ Contaminação declarada (D12)

Diferente da rodada 2, **o autor desta lista já leu o gabarito** (`docs/gabarito.md`) e a comparação
dele com a rodada 2. A D12 não se sustenta mais nem na forma enfraquecida. Consequências:

- A única mudança de catálogo desta rodada (W5, entrada nova de integridade de esquema) é escrita a
  partir da literatura: Karwin, *SQL Antipatterns* ("Keyless Entry", "Rounding Errors") e as regras
  usuais de projeto de esquema relacional. Ela não reproduz itens do gabarito.
- **O recall da rodada 3 nessa família não conta como evidência de generalização.** O relatório da
  rodada 3 separa o recall em duas colunas: famílias intocadas desde a rodada 2 e famílias que a
  rodada 3 alterou.
- "Achados além do gabarito" (D8) continua válido: mede o que o gabarito *não* tem.

## Decisões tomadas antes da implementação

| Item | Decisão |
|---|---|
| R2-1 | **D19 — isolamento de execução, container primeiro.** Com runtime de container disponível, toda execução (original e refatorada) roda num container descartável, com nome e label exclusivos da rodada, e encerrar é remover *aquele* container pelo nome. Sem container: modo host com a ferramenta de ciclo de vida (D20), **declarado** como `Isolation: reduced (host)`. Nos dois modos, é proibido encerrar por nome, imagem ou padrão, e todo start/stop entra no `## Execution Log` do relatório. |
| R2-1 | **D20 — ferramenta de ciclo de vida separada do probe (emenda à D6.1).** `scripts/proc.py` e `scripts/proc.mjs` executam um comando **que o agente derivou**, gravam PID, grupo e hora de início, esperam a porta e encerram só a árvore que criaram, conferindo a identidade do PID antes. O probe continua sem subir nada. A ferramenta não sabe nada de stack: o conhecimento de *como* subir continua com o agente, e a D6.1 perde só a parte "o agente encerra o processo". |
| R2-2 | **Emenda à D16:** a aplicação refatorada também roda de uma cópia (`refactored-<n>/`), nunca no alvo. O snapshot é apagado depois da 3d, não na 3c. |
| R2-5 | **D21 — entrada de segurança "neutralizada".** `expect: "neutralized"` com `like: <id de entrada benigna>`. Vira `FIXED` quando o replay responde sem erro e com o mesmo shape da entrada benigna irmã. Nunca vira `REGRESSION`. |
| R2-7 | **D22 — o contrato de erro.** São contrato o status e o shape dos corpos de erro **intencionais** da aplicação. A página de erro padrão do framework não é: trocá-la mantendo o status é seguro. Mascarar um segredo vazado mantendo o campo é seguro, pelo teste do uso legítimo da D15. Correção que exige **dependência de runtime nova** é proposta. |
| R2-10 | **D23 — laço de correção limitado.** Um replay completo obrigatório. Findings `failed` e `introduced` da re-auditoria podem ser corrigidos na mesma rodada, seguidos de replay e de **no máximo mais uma** re-auditoria. As duas passadas ficam no relatório. `missed-in-phase-2` corrigido na Fase 3 é contado à parte, para o recall da Fase 2 continuar mensurável. |

## Mudanças planejadas

### W1 — Isolamento de execução (bloqueante)
Arquivos: `SKILL.md`, `06-validation-protocol.md`, `03-report-template.md`, `scripts/proc.py`,
`scripts/proc.mjs` (novos), `tests/probe-conformance/`.

| # | Mudança |
|---|---|
| R2-1 | Nova seção **Process ownership** no `SKILL.md`, com proibições nomeadas: encerrar por nome, imagem ou padrão (`pkill`, `killall`, `taskkill /IM`, `Stop-Process -Name`, remoção em massa de containers); encerrar o que a skill não subiu; liberar à força uma porta ocupada por outro processo. |
| R2-1 | `06` §1.3 **Execution modes**: detecção do runtime de container; imagem oficial do runtime na versão da Fase 1; a cópia de execução montada no container; o probe roda **dentro** do container via `exec`, o que dispensa publicar porta e mudar bind; nome `refactor-arch-<alvo>-<run>`; checagem final de que nenhum container da rodada sobrou. Degradação declarada para o modo host. |
| R2-1 | `proc start/stop/status`, só com stdlib/built-ins: grupo de processos novo, arquivo de estado, readiness pela porta, recusa de porta ocupada, conferência de identidade do PID antes de encerrar, encerramento da árvore registrada. |
| R2-1 | `## Execution Log` no template: fase · ação · modo · handle · comando · resultado. Ação sobre processo fora do log é **incidente** e vai para `## Verification Coverage`. |
| R2-2 | Aplicação refatorada roda de `refactored-<n>/`; as dependências dela são instaladas nessa cópia (ou no container) a partir do manifesto refatorado, e o relatório diz onde. Snapshot apagado depois da 3d. |
| R2-3 | O launcher fora da árvore só vale se o entry point exporta o objeto da aplicação. Override de porta que muda outra configuração (debug, bind) é registrado, e a evidência de AP-18 vem de uma execução na configuração nativa. |

### W2 — Contrato da Fase 1
Arquivos: `SKILL.md`, `01-project-analysis.md`.

| # | Mudança |
|---|---|
| R2-4 | `Target:` relativo ao CWD quando possível, senão absoluto. Campos novos: `Boot:`, `Port:`, `Runtime env:`, `Isolation:`. |
| R2-4 | O inventário da superfície fica em memória na Fase 1; `surface.json` é escrito na 3a. |
| R2-4 | A regra de exclusão da contagem de arquivos nomeia diretórios de configuração de ferramentas e agentes. |

### W3 — Coerência da especificação
Arquivos: `02`, `03`, `04`, `05`, `SKILL.md`.

| # | Mudança |
|---|---|
| R2-6 | RP-18 passa a seguir o §6 (major permitida se o replay cobrir a mudança). "Versão corrigida mais baixa" inclui a configuração opt-in que a correção exige. Advisory só domina AP-14 quando afeta o caminho de runtime. Sem lockfile, pin exato conta como pinado; no pip, as versões resolvidas vêm dos metadados instalados. Degrau de severidade para advisory LOW em pacote de runtime. AP-14 aceita "nenhum sucessor nomeado pelo upstream (fonte, data)". |
| R2-7 | Ver D22, com o mesmo texto no `04` §6 e no RP-17. `missed-in-phase-2` que precisa de decisão de produto pode ser `proposed`. |
| R2-9 | `audit-<ts>.md` é a Fase 2 como estava; `audit-latest.md` é o estado final. Com `--yes`, o prompt não é impresso; imprime-se a linha de confirmação registrada. Uma única seção `## Proposed, Not Applied`. `File:` pode cobrir o arquivo inteiro para God Module, com a contagem de linhas. |
| R2-10 | Ver D23. |
| R2-12 | Regra única de precedência entre AP-03 e AP-05: um finding por módulo, com ordem de desempate declarada. |

### W4 — Protocolo e harness
Arquivos: `06-validation-protocol.md`, `probe.py`, `probe.mjs`, `tests/probe-conformance/run.py`.

| # | Mudança |
|---|---|
| R2-5 | Ver D21. Campo `rawBody` (enviado literalmente, com o content-type declarado) para testar corpo malformado. Entradas `destructive: true` rodam por último, cada uma numa execução própria. |
| R2-11 | Mensagens citam §3.1. O aviso de erros de transporte conta só a execução corrente. `capture --only --merge` informa quantas entradas capturou agora. Fixtures de conformidade para `--merge` com erros preexistentes, `neutralized` e `rawBody`. |
| R2-1 | O teste de conformidade passa a cobrir `proc.py` e `proc.mjs`, incluindo o teste do processo-isca (a isca continua viva depois do `stop`). |

### W5 — Recall: integridade no esquema
Arquivos: `02-antipattern-catalog.md`, `05-refactoring-playbook.md`.

| # | Mudança |
|---|---|
| R2-8 | Nova **AP-20 Missing Schema-Level Integrity Constraints**: coluna de identidade sem restrição de unicidade; coluna de referência sem chave estrangeira, e exclusão do pai deixando filhos órfãos; valor monetário em tipo de ponto flutuante binário. Default MEDIUM, HIGH quando corrompe dinheiro ou identidade. RP-19 com código antes/depois. |
| R2-8 | **Não muda o catálogo:** limite de tamanho de requisição e transição de estado sem guarda **já são sinais de AP-11**, e mesmo assim foram perdidos. Nesses dois casos o problema é de atenção na varredura, não de conteúdo. A tabela `## Catalog Coverage` passa a exigir, por entrada, **quais sinais foram checados**, e não só se houve acerto. |

### Método da rodada 3 (orquestração, fora da skill)
- Sandbox como na rodada 2, com as tags `run/<projeto>/iter3`.
- Defesa em profundidade: regras de permissão `deny` no sandbox de cada subagente para comandos que
  encerram por nome.
- O relatório da rodada confere a mensagem final de cada subagente contra o log dele, para que um
  incidente não exista só na mensagem.

### Especificação
D19–D23 em `CLAUDE.md` §8 e em `docs/decisions.md`.
