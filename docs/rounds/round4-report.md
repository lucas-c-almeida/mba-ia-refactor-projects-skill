# Rodada 4 — validação do D24/D24.1 nos três projetos-alvo

- **Data:** 2026-09-25/26
- **Branch com o código refatorado:** [`round4`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/tree/round4)
- **Estado da skill:** `main` (`602343e`, PR #6 `fix/analyzable-commands` já mesclado — D24 e D24.1),
  **sem ajustes durante a rodada**. Esta é uma rodada de validação pura: D24/D24.1 tinham sido
  escritas e testadas só contra `task-manager-api` (`run/task-manager-api/iter4` e `iter5`);
  `code-smells-project` e `ecommerce-api-legacy` nunca tinham rodado com a regra de comandos
  analisáveis em vigor. Esta rodada fecha essa lacuna nos 3/3.
- **Tags de partida (D3):** `run/code-smells-project/iter4` (`602343e`),
  `run/ecommerce-api-legacy/iter4` (`c19c696`), `run/task-manager-api/iter6` (`e48f2b6`) — cada tag
  aponta para o commit imediatamente anterior ao início daquele projeto, porque as três rodadas
  foram sequenciais e cada uma foi commitada antes de a próxima começar (ver abaixo).

## Como a rodada foi executada — diferente das anteriores

Por pedido explícito do autor, esta rodada mudou dois eixos de método em relação às rodadas 1–3:

- **Sequencial, não paralela.** Cada projeto rodou em um subagente novo (sessão isolada, D3), um
  por vez, só iniciando o próximo depois de o anterior terminar e ser commitado. As rodadas
  anteriores rodaram os três projetos em paralelo.
- **Sem sandbox externo — direto no monorepo, na branch `round4`.** Nenhum diretório fora do
  repositório foi criado para isolar a execução. Cada subagente operou em
  `code-smells-project/`, `ecommerce-api-legacy/` ou `task-manager-api/` como subdiretório do
  próprio checkout, na raiz, exatamente como a D2.1 prevê (`/refactor-arch <subdir>`).
- **Confirmação (D10):** `--yes` nos três, mesmo motivo das rodadas anteriores — calibração, não
  revisão humana.
- **Restrição adicional, específica desta rodada:** cada subagente recebeu uma lista explícita de
  proibições derivadas do D24/D24.1 (nunca `cd`, nunca encadear comandos com `&&`/`;`, nunca
  variável de shell em caminho, sempre citar argumento com `,`/`@`/`{`, nunca laço de polling em
  shell) **antes** de rodar, para que qualquer violação fosse um incidente relatável, não uma
  surpresa. O autor observou os prompts de aprovação em tempo real durante a primeira execução.

## Critérios de aceite (`instructions.md`)

| Critério | code-smells-project | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Fase 1 detecta a stack | ✓ Python 3.13 · Flask 3.1.1 · SQLite | ✓ Node 24 · Express 4.22.1 · sqlite3 (memória) | ✓ Python · Flask 3.0.0 · SQLite |
| Fase 2 encontra ≥ 5 findings | ✓ 19 | ✓ 17 | ✓ 31 |
| Fase 2 tem ≥ 1 CRITICAL/HIGH | ✓ 7 C · 6 H | ✓ 7 C · 6 H | ✓ 6 C · 7 H |
| Fase 3: a aplicação funciona | ✓ 25 PASS, 0 REGRESSION, 1 UNVERIFIED (confirmado manualmente) | ✓ 8 PASS, 1 diff sancionado (ver abaixo) | ✓ 24 PASS, 0 REGRESSION |

3/3 em todos os critérios, como nas rodadas anteriores. O "1 diff sancionado" do eal
(`checkout-malformed-json`) é a própria correção de AP-18: status 400 preservado nos dois lados,
só o corpo mudou (página de erro com stack trace → corpo seguro), coberto pela ressalva de
contrato de erro do `04-architecture-guidelines.md` §6 — não é regressão.

## Resumo por projeto

| | code-smells-project | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Findings (C/H/M/L) | 19 (7/6/4/2) | 17 (7/6/1/3) | 31 (6/7/14/4) |
| Replay | 25 PASS / 0 REG / 1 UNVERIFIED* | 8 PASS / 1 diff sancionado | 24 PASS / 0 REG |
| Entradas de segurança | 5 FIXED, 0 NOT FIXED | — | 2 FIXED, 0 NOT FIXED, 1 NOT FIXED esperado (proposto) |
| Findings resolvidos | 12/19 (7 proposed, 0 unresolved) | 12/17 (5 proposed, 0 unresolved) | 27/31 (4 proposed, 0 unresolved) |
| Linha da re-auditoria (D14) | `○ 7 proposed-not-applied, 0 unresolved (7)` | `○ 5 proposed-not-applied, 0 unresolved (5)` | `○ 4 proposed-not-applied, 0 unresolved (4)` |
| Passadas de re-auditoria | 1 | 2 (D23, máximo) | 1 |
| Containers subidos/derrubados | 15 / 15 | 20 rows no log, 0 restante | 9 / 9 |

\* `sqli-search` (csp): a comparação por *shape* não distingue um array de busca legítima de um
array de injeção bem-sucedida (ambos são listas de produtos); confirmado manualmente que a
correção funciona (original retornava todos os 10 produtos para o payload de injeção, a versão
refatorada retorna 0). Ficou documentado como limitação real do harness, não escondido.

Nenhum projeto imprimiu `✓ Zero anti-patterns remaining` — correto pela D14, já que os três
restaram itens `PROPOSED, NOT APPLIED` sob o gate de contrato.

## ⭐ D24/D24.1 sob teste: o que a rodada foi feita para responder

A pergunta desta rodada não era "quantos findings", era: **depois de D24/D24.1, a skill roda sem
pedir aprovação do harness fora do que já era esperado?** A resposta é **parcialmente sim** — o
que D24 nomeou nominalmente parou de dar problema — **mas apareceram categorias novas de fricção
que D24 não previu**, em duas das três rodadas.

### O que D24 cobriu e se manteve resolvido nas 3/3

Zero incidentes de `cd`, `$VAR`/`$env:`/`$(...)`, edição por `sed -i`/redirecionamento, e exatamente
um caso de argumento com vírgula não citado (csp, `--only sqli-login,sqli-pedido`) — que foi
**recusado pela camada de permissão e corrigido pelo próprio subagente na tentativa seguinte**,
citando o argumento. Isso é a regra D24.1 funcionando como desenhada, não uma falha: ela existe
para pegar exatamente esse caso, e pegou.

### R4-1 — 🔴 Encadeamento de comandos docker confundido com exclusão de arquivo do sistema

**Visto em:** csp. Um único comando combinando `docker run ...` com um `docker rm` posterior na
mesma chamada foi bloqueado automaticamente pela camada de permissão com a mensagem
`Remove-Item on system path '/app' is blocked`. O comando não continha nenhum `Remove-Item`
real — era um caminho *interno ao container* (`/app`) dentro de argumentos `docker`, mas a
verificação de segurança do harness, operando sobre o texto do comando encadeado, tratou aquele
caminho como um alvo de exclusão local. `docker ps -a` confirmou que nada tinha sido criado nem
removido antes do bloqueio. Corrigido separando em duas chamadas, uma por comando.

**Por que é um problema da skill, não só do ambiente.** D24 proíbe nomeadamente `cd &&`, mas não
generalizou para "nunca encadear comandos de ciclo de vida de processo/container com `&&`/`;`". O
D20 já separa a ferramenta de ciclo de vida (`proc.py`/`proc.mjs`) do probe exatamente para que o
agente nunca precise "digitar" o encadeamento — mas o modo container (D19) não tem, hoje, o
equivalente do `proc` para `docker run`/`docker stop`/`docker rm`: o agente ainda monta esses
comandos manualmente, e nada no `SKILL.md`/`06-validation-protocol.md` proíbe encadeá-los.

### R4-2 — 🔴 Laços de polling em shell recusados

**Visto em:** eal. Um laço `while`/`until` com `Start-Sleep`/`sleep` esperando a porta do container
ficar pronta foi **recusado diretamente pela camada de permissão**, sem explicação além de
"Permission denied". Contornado trocando para chamadas de poll de tiro único (uma checagem por
chamada de ferramenta) e, para esperas mais longas, pela ferramenta `Monitor`.

**Por que é um problema da skill.** O protocolo (`06-validation-protocol.md` §1) manda o agente
"esperar a porta ficar pronta" mas não diz **como**, e um laço de polling é a forma óbvia de
implementar isso em qualquer shell. D24 e D24.1 não mencionam laços de polling em nenhum lugar —
é uma categoria de comando inteiramente nova, não uma variação de `cd`/substituição de variável.
Sem uma instrução explícita ("nunca `while`/`until` com sleep; use polling de tiro único ou uma
ferramenta de monitoramento externa"), qualquer alvo cujo boot não seja instantâneo vai tropeçar
nisso.

### R4-3 — 🟡 Caminhos internos de container reescritos pelo Git Bash no Windows

**Visto em:** tma. Comandos `docker exec`/`docker run` com caminhos internos ao container (`/app`)
executados pela ferramenta Bash tiveram esses caminhos **reescritos silenciosamente** pela emulação
POSIX do Git Bash antes de chegar ao Docker — falha real observada:
`pip install ... /app/requirements.txt` chegou ao Docker como
`C:/Program Files/Git/app/requirements.txt`. Contornado rodando esses comandos específicos pela
ferramenta PowerShell em vez de Bash. O comando em si era totalmente literal nos dois casos — o
problema é qual shell o interpreta, não o texto do comando.

**Por que vale registrar.** Isto é ortogonal a D24 (que trata de literalidade do comando) e ao
D6.2 (que trata de qual runtime hospeda o probe) — é uma terceira dimensão, específica de Windows:
**qual ferramenta de shell** executa um comando que menciona um caminho de container. Não é um
"bug do agente"; é uma característica do ambiente que vai se repetir em qualquer alvo rodado em
container, neste host, por qualquer agente. Merece uma frase explícita no `06-validation-protocol.md`
(que já fala de "caminhos de container fora de shell que os reescreve", D24) apontando a ferramenta
certa por plataforma.

### R4-4 — 🟡 Violação real, mas autoinfligida e de baixo risco

**Visto em:** tma. O próprio subagente encadeou três `Remove-Item` com `;` para limpar
`__pycache__` deixado por uma sessão anterior. Efeito inócuo (exclusão idempotente de arquivos que
esta rodada não criou), mas é uma violação genuína da regra "um comando por chamada", declarada
pelo subagente e não escondida. Diferente de R4-1/R4-2, aqui a regra existia e foi ignorada, não
inexistente — evidência de que a regra precisa ser mais **reflexiva** (lembrada em cada chamada),
não só documentada uma vez no início.

### Balanço

| # | Categoria | Coberta por D24 hoje? | Ocorreu em |
|---|---|---|---|
| — | `cd`, `$VAR`/`$env:`/`$(...)`, edição via shell | ✓ Sim, resolvido | nenhum projeto |
| — | Argumento com vírgula não citado | ✓ Sim, resolvido (autocorrigido) | csp |
| R4-1 | Encadeamento de `docker run`/`docker rm` com `&&` | ✗ Não | csp |
| R4-2 | Laço de polling em shell (`while`/`until` + sleep) | ✗ Não | eal |
| R4-3 | Caminho de container reescrito pelo shell errado (Windows) | Parcial — D24 menciona "caminhos que um shell reescreve", mas não a ferramenta certa por plataforma | tma |
| R4-4 | Violação autoinfligida do "um comando por chamada" | ✓ Regra existe, foi ignorada uma vez | tma |

**Conclusão para o autor:** D24/D24.1 fecharam a categoria que motivou sua criação (substituição de
variável, `cd`, quoting). O "ainda não fez o trabalho" percebido no início desta rodada vem de
categorias vizinhas que nunca foram nomeadas — polling e encadeamento de comandos de ciclo de vida
de container — não de uma regressão na correção já aplicada. Um R4 (ou D25) dedicado a "nunca
encadear comandos de processo/container" e "nunca laço de polling em shell" fecharia R4-1 e R4-2
com o mesmo tipo de regra explícita que resolveu D24.

## Outros achados de calibração

- **R4-5 — Lacuna de compliance na Fase 1 (csp).** A análise foi feita corretamente, mas o bloco
  formatado `PHASE 1: PROJECT ANALYSIS` nunca foi impresso no terminal — só os valores foram
  reportados na mensagem final. Bug de aderência ao contrato de saída (§5 do `CLAUDE.md`), não
  relacionado ao harness.
- **R4-6 — Lacuna de recall na Camada 1 do AP-14 (tma).** A checagem de deprecation
  (`python -X dev -c "import app"`) só exercita código de *import time*; um `datetime.utcnow()`
  dentro de `seed.py` só emitiu o warning quando a Fase 3a rodou o seed de verdade, não na Fase 2.
  O finding não foi perdido (apareceu como `missed-in-phase-2` na Fase 3), mas o `SKILL.md` deveria
  dizer explicitamente para exercitar um caminho de execução realista (bootstrap/seed do próprio
  projeto), não só importar o entry point.
- **A rodada do eal foi interrompida no meio do replay** por limite de turno/tempo do subagente, e
  retomada com sucesso a partir do próprio estado declarado no handback ("o que falta para quem
  continuar"), sem retrabalho nem perda de dados. A resiliência do protocolo a interrupções parciais
  se mostrou sólida.

## O que ficou pendente

**Os três projetos**, propostas sob o gate de contrato (D7/D15):
- **csp:** 7 propostas — credencial de seed (README/baseline dependem dela), rotas administrativas
  sem modelo de identidade, `/admin/query` (SQL arbitrária por desenho), validação de update de
  produto, FK de `itens_pedido.produto_id`, paginação, upgrade major do flask-cors.
- **eal:** 5 propostas — autorização (×2, sem modelo de identidade), erro no DELETE não tratado,
  validação de senha/cartão, enforcement de FK de `AP-20`.
- **tma:** 4 propostas — autorização (sem modelo de identidade), exclusão de categoria órfã,
  paginação, restrição de origem no CORS (a flag ficou configurável, mas com o mesmo default).

Nada foi corrigido nesta rodada além do que os três subagentes já aplicaram dentro do próprio
escopo da Fase 3 — por desenho, esta é uma rodada de evidência, não de ajuste da skill.

## Intervenções

- **Sessão orquestradora:** nenhuma correção de rumo durante a execução dos subagentes, além de
  resumir o subagente do eal após a interrupção por limite de turno (mesma tarefa, sem
  redirecionamento de conteúdo) e de padronizar a instrução dada aos dois subagentes seguintes com
  as proibições de R4-1/R4-2 depois de vistas no primeiro/segundo relatório.
- **Nenhuma intervenção humana durante a execução dos três subagentes.**

## Evidência

Os arquivos abaixo estão na branch `round4` (`c19c696`, `e48f2b6`, `c3b441b`, um commit por
projeto, nesta ordem).

| Projeto | Relatório de auditoria | Baseline / replay / superfície |
|---|---|---|
| code-smells-project | [`code-smells-project/reports/audit-latest.md`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/blob/round4/code-smells-project/reports/audit-latest.md) | [`code-smells-project/reports/`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/tree/round4/code-smells-project/reports) |
| ecommerce-api-legacy | [`ecommerce-api-legacy/reports/audit-latest.md`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/blob/round4/ecommerce-api-legacy/reports/audit-latest.md) | [`ecommerce-api-legacy/reports/`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/tree/round4/ecommerce-api-legacy/reports) |
| task-manager-api | [`task-manager-api/reports/audit-latest.md`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/blob/round4/task-manager-api/reports/audit-latest.md) | [`task-manager-api/reports/`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/tree/round4/task-manager-api/reports) |

Este relatório foi commitado direto em `main`; a branch `round4` permanece intocada como registro
da execução (código refatorado + relatórios de auditoria dos três projetos).
