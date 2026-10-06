# Rodada 5 — lista de mudanças congelada

- **Data do congelamento:** 2026-09-30
- **Origem:** os problemas R4-1 a R4-6 de [`round4-report.md`](round4-report.md) e as falhas de
  checklist encontradas ao escrever a seção C do README a partir da rodada 4
  (scorecards em [`docs/evals/`](../evals/)).
- **Regra:** na rodada 5, a skill só muda em pontos atribuíveis a um item desta lista.
- **Restrição permanente (CLAUDE.md §2):** toda correção é escrita como sinal observável e
  raciocínio, nunca como a instância da rodada 4, e precisa passar no Teste do Quarto Projeto.

## ⚠ Contaminação declarada (D12)

O autor desta lista leu o gabarito, os relatórios da rodada 4 **e** os scorecards que casam um com
o outro. Por isso esta lista **não mexe no catálogo nem na varredura de sinais**. Os ✗ dos scorecards
que apontam para a skill (P2: *callback hell* e dependências deprecated no lockfile, sinais que o
AP-14 já descreve e a varredura não aplicou) ficam **adiados de propósito**:

- corrigi-los agora inflaria o recall da rodada 5 por construção, e a comparação rodada 4 → rodada 5
  deixaria de medir variância de execução para medir o ajuste feito em cima do gabarito;
- ficam registrados como candidatos para depois da entrega (§"Fora desta rodada").

Tudo abaixo é operacional (como os comandos rodam) ou de conformidade de formato (o que o
checklist do enunciado cobra). Nada muda o que a auditoria procura.

## Já aplicado antes do congelamento

| Item | Decisão |
|---|---|
| R4-1, R4-4 | **D25 — nunca `cd`, nunca encadear** (commit `762d3d5`). Regra inviolável no topo do `SKILL.md` e §0 do `CLAUDE.md`; encadeamento dentro de `sh -c` incluído; instalação e boot no container viram chamadas separadas; linha `Commands:` no bloco de validação. Aplicada antes desta lista a pedido explícito do autor, e declarada aqui. |

## Mudanças planejadas (D26)

### W1 — Espera de prontidão sem laço no shell (R4-2)
Arquivos: `scripts/proc.py`, `scripts/proc.mjs`, `tests/probe-conformance/proc_check.py`,
`SKILL.md`, `06-validation-protocol.md`.

| # | Mudança |
|---|---|
| R4-2 | Subcomando novo **`proc wait --port <n> [--timeout <s>]`** nas duas implementações: espera a porta responder em loopback e sai com `0` (pronto) ou `4` (não ficou pronto). Não inicia nem encerra nada. O laço fica dentro da ferramenta, onde ninguém precisa lê-lo, e não no shell. |
| R4-2 | Modo container: a prontidão é **uma** chamada, `<runtime> exec <name> <runtime do alvo> /skill/proc.<ext> wait --port <n>`. O `scripts/` já está montado e o runtime do alvo já existe na imagem (D6.2). Modo host: `proc start` já espera. |
| R4-2 | Proibição explícita: nunca `while`/`until`/`for` com `sleep` no shell para esperar algo; nunca `Start-Sleep` em laço. Uma checagem por chamada, ou `proc wait`. |
| R4-2 | Teste de conformidade: `wait` numa porta que responde (`0`), numa porta fechada com timeout curto (`4`), mesmas chaves de saída nas duas implementações. |

### W2 — Shell certo para caminho de container (R4-3)
Arquivos: `06-validation-protocol.md`.

| # | Mudança |
|---|---|
| R4-3 | O item "keep container paths out of a shell that rewrites them" ganha o **sinal** para reconhecer esse shell (host Windows com shell de emulação POSIX: `uname` com `MINGW`/`MSYS`/`CYGWIN`, paths no formato `/c/...`) e a regra: comandos com caminho interno de container vão pelo shell nativo do host. É decidido **uma vez**, na Fase 1, junto com o modo de isolamento, e registrado. |

### W3 — Bloco da Fase 1 sempre impresso e guardado (R4-5)
Arquivos: `SKILL.md`, `03-report-template.md`.

| # | Mudança |
|---|---|
| R4-5 | O bloco `PHASE 1: PROJECT ANALYSIS` é impresso **antes** de qualquer passo da Fase 2, e não em resumo no fim. |
| R4-5 | O relatório da Fase 2 abre com o bloco da Fase 1 **copiado literalmente** (`## Phase 1 — Project Analysis`). A Fase 1 continua sem escrever nada; quem grava é a Fase 2, em `reports/`. Assim, o checklist "domínio descrito corretamente" pode ser verificado depois da sessão. |

### W4 — Camada 1 de deprecation num caminho de execução real (R4-6)
Arquivos: `SKILL.md`, `02-antipattern-catalog.md` (AP-14, só o procedimento da camada 1, não os sinais).

| # | Mudança |
|---|---|
| R4-6 | Com os detectores ligados, a camada 1 exercita **o que a aplicação executa de fato**: o boot pelo comando derivado, os scripts de bootstrap/seed/migração que o próprio projeto documenta, e cada entrada da superfície pública (ou ao menos uma por módulo). Importar o entry point não basta: só exercita o código de import time. |
| R4-6 | A cobertura do AP-14 no `## Catalog Coverage` lista o que foi exercitado. |

### W5 — Conformidade do relatório com o checklist (seção C)
Arquivos: `03-report-template.md`, `SKILL.md`.

| # | Mudança |
|---|---|
| C-1 | **Ordenação verificada antes de gravar.** Na rodada 4, um MEDIUM ficou depois dos LOW já no relatório congelado no gate (P3). Antes de gravar, o agente confere a ordem CRITICAL → HIGH → MEDIUM → LOW. Um finding acrescentado depois do gate entra na posição da sua severidade no `audit-latest.md`, nunca no fim. |
| C-2 | **Intervalo de arquivo inteiro termina na última linha real.** `1-<N>`, com N igual ao número de linhas que a ferramenta de leitura mostra; a quebra de linha final não cria uma linha. Na rodada 4, os três intervalos de arquivo inteiro passaram uma linha do fim. |

## Método da rodada 5 (não muda a skill)

| # | Decisão |
|---|---|
| M-1 | **Sequencial**, um subagente novo por projeto (D3), na ordem csp → eal → tma. Cada projeto é commitado antes de o próximo começar. |
| M-2 | **Sem `--yes`.** O gate da Fase 2 é exercitado de verdade: o subagente para no prompt `[y/n]`, o orquestrador leva o resumo do relatório ao autor, e **o autor responde**. A resposta volta ao mesmo subagente. O relatório registra `human-confirmed`. É o item do checklist que a rodada 4 não cobriu. |
| M-3 | **Transcript** de cada projeto em `docs/runs/p<N>-iter<K>.md`: o bloco da Fase 1, o total do gate, a resposta dada e o bloco final da Fase 3, como o subagente os imprimiu. |
| M-4 | O subagente recebe a skill e o alvo. Diferente da rodada 4, **não** recebe uma lista extra de proibições: a D25 e a W1 agora estão na skill, e a rodada mede se a skill sozinha basta. |
| M-5 | Aprovações de comando são contadas **pelo autor**, que observa a sessão (D24.1). O subagente reporta só a linha `Commands:`. |
| M-6 | Branch de execução `round5`, criada a partir de `feat/round5` depois do commit da D26. Tags `run/code-smells-project/iter5`, `run/ecommerce-api-legacy/iter5`, `run/task-manager-api/iter7`. |

## Fora desta rodada

- Varredura do AP-14 registrando os três sinais (camada 1, camada 2 **e** construções
  estruturalmente superadas) e checando dependências transitivas marcadas como deprecated no
  lockfile. Vem dos ✗ do P2 e fica adiada pela contaminação declarada acima.
- ✗ de legibilidade e performance dos scorecards (`print` como log, mapeamento duplicado,
  condicionais verbosas, agregação com vários `COUNT`). Nenhum deles é CRITICAL ou HIGH.
- Entrada de segurança para validações aplicadas em projetos sem entrada desse tipo no inventário (P2).
