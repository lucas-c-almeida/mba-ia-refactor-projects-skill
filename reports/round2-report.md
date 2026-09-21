# Rodada 2 — `/refactor-arch` nos três projetos-alvo

- **Data:** 2026-09-21
- **Branch com o código refatorado:** [`round2`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/tree/round2)
- **Estado da skill:** `catalog/round2` (`744388c`, branch `feat/round2`), sem ajustes entre as
  rodadas. As mudanças em relação à rodada 1 estão em
  [`docs/round2-changes.md`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/blob/feat/round2/docs/round2-changes.md)
  (lista congelada antes do gabarito) e nas decisões D15–D18.
- **Tags de partida (D3):** `run/code-smells-project/iter2`, `run/ecommerce-api-legacy/iter2`,
  `run/task-manager-api/iter2`. As três apontam para `744388c`, que contém o código original dos
  projetos.

## Como a rodada foi executada

- **Isolamento de contexto, mais forte que na rodada 1.** Na rodada 1 os subagentes rodaram dentro
  do repositório e poderiam ter lido o `CLAUDE.md`, o relatório anterior ou o gabarito. Desta vez
  cada subagente recebeu um **sandbox fora do repositório**, com apenas o projeto original e a skill
  em `<projeto>/.claude/skills/refactor-arch/` (o layout de entrega da D2.2). Cada sandbox era um
  repositório git próprio, com as regras de ignore do repositório aplicadas via `.git/info/exclude`.
  Não havia nada mais para ler.
- **O que os subagentes receberam:** o caminho do alvo, a instrução de ler o `SKILL.md` e executá-lo
  com `--yes`, e três restrições operacionais: trabalhar só no alvo e no diretório temporário que a
  skill mandar criar; usar uma faixa exclusiva de portas (5201–5209, 5211–5219, 5221–5229), porque os
  três rodaram em paralelo; e escrever um log com os blocos das fases, os comandos executados e uma
  seção *Skill friction*. Nenhuma informação sobre o projeto, a rodada 1 ou o gabarito.
- **Confirmação da Fase 2 (D10):** `--yes` nas três rodadas, pelo mesmo motivo da rodada 1. Os três
  relatórios registram `Confirmation: --yes (auto-approved, not human-reviewed)`. **Continua sendo
  uma rodada de calibração, não uma revisão humana.**
- **Escopo aplicado:** todas as severidades, com o gate de contrato ativo (D7, D15, D18).
- **Verificação upstream (D13):** modo completo nos três projetos. Houve consulta viva a OSV.dev e aos
  registries, e os warnings de deprecation foram forçados numa cópia do original (D16).
- **Conferência independente:** refiz a comparação de cada projeto a partir dos arquivos salvos
  (`probe.py compare --baseline … --current …`) e os três resultados bateram com os relatados.
  Conferi 8 citações `File:` contra o código original; todas apontam para o trecho descrito.

## Critérios de aceite (`instructions.md`)

| Critério | code-smells-project | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Fase 1 detecta a stack | ✓ Python 3.13 · Flask 3.1.1 · SQLite | ✓ Node 24 · Express 4.22.1 · sqlite3 (em memória) | ✓ Python 3.13 · Flask 3.0.0 · Flask-SQLAlchemy 3.1.1 · SQLite |
| Fase 2 encontra ≥ 5 findings | ✓ 33 | ✓ 18 | ✓ 28 |
| Fase 2 tem ≥ 1 CRITICAL/HIGH | ✓ 11 C · 8 H | ✓ 7 C · 4 H | ✓ 9 C · 5 H |
| Fase 3: a aplicação funciona | ✓ boot + 45 PASS, 1 REGRESSION (ver abaixo) | ✓ boot + 13 PASS | ✓ boot + 59 PASS |

A única `REGRESSION` da rodada é a própria correção de SQL injection do code-smells-project:
`GET /produtos/busca?q='` antes quebrava o SQL e não retornava nada; agora a aspa é tratada como
texto e encontra um produto cujo nome contém `''`. A entrada hostil foi cadastrada como entrada de
contrato, e o protocolo proíbe mudar o inventário depois do baseline, então ela ficou como
`REGRESSION` e a linha do replay saiu com `✗`. É o comportamento honesto previsto pela skill, e
também uma lacuna dela (problema R2-5 abaixo).

## Resumo por projeto

| | code-smells-project | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Superfície | 19 rotas HTTP | 3 rotas HTTP | 22 rotas HTTP |
| Entradas no inventário | 51 (5 de segurança) | 16 (3 de segurança) | 72 (13 de segurança) |
| Findings (C/H/M/L) | 33 (11/8/11/3) | 18 (7/4/4/3) | 28 (9/5/9/5) |
| Rodada 1, para comparação | 27 (8/10/7/2) | 17 (5/6/3/3) | 18 (4/5/7/2) |
| Replay | `✗` 45 PASS, 1 REGRESSION | `✓` 13 PASS | `✓` 59 PASS |
| Entradas de segurança | 5 FIXED, 0 NOT FIXED | 3 FIXED, 0 NOT FIXED | 13 FIXED, 0 NOT FIXED |
| Findings resolvidos | `○` 24/33 (9 proposed, 0 unresolved) | `○` 14/18 (4 proposed, 0 unresolved) | `○` 22/28 (5 proposed, 1 unresolved) |
| Linha da re-auditoria (D14) | `○ 9 proposed-not-applied, 3 unresolved (12)` | `○ 4 proposed-not-applied, 1 unresolved (5)` | `○ 5 proposed-not-applied, 2 unresolved (7)` |
| `missed-in-phase-2` | 3 | 1 | 1 |

Nenhum projeto recebeu `✓ Zero anti-patterns remaining`, e isso está correto: nos três restaram
itens `PROPOSED, NOT APPLIED`.

## Comparação com o gabarito

O gabarito (`docs/gabarito.md`, também copiado para a seção A do README) tem 25, 21 e 23 itens. O casamento foi feito por **categoria + arquivo**, como o próprio gabarito
recomenda, porque ele agrupa ocorrências e a skill às vezes as separa.

| Métrica (D8) | csp | eal | tma |
|---|---|---|---|
| Recall da Fase 2, rodada 2 | **22/25** | **19/21** | **18/23** |
| Recall da Fase 2, rodada 1 (retroativo, estimado) | ≈ 20/25 | ≈ 17/21 | ≈ 16/23 |
| Achados além do gabarito, rodada 2 | 3 | 3 | 4 |
| Findings inventados (amostra de 8 citações) | 0 | 0 | 0 |
| Regressões pós-refactor | 1 (a correção de injeção) | 0 | 0 |
| Intervenções humanas durante a rodada | 0 | 0 | 0 |

**Como ler os números.** O recall da rodada 2 foi conferido pela descrição de cada finding nos itens
duvidosos. O da rodada 1 foi estimado só pelo título e pelo intervalo `File:` dos relatórios da
branch `round1`, então tem margem de ±1 por projeto. A melhora vem principalmente de duas mudanças:
AP-18 passou a capturar CORS aberto e debug ligado, que a rodada 1 não registrava ou registrava como
magic value; e o finding de autorização do ecommerce passou a cobrir o checkout que age sobre uma
conta existente só pelo e-mail.

**O que a skill não encontrou na Fase 2:**
- **csp:** esquema sem restrições de integridade (e-mail sem `UNIQUE`, sem FKs), valores monetários
  em `float`, e o relatório de vendas com cinco queries onde um `GROUP BY` basta. O primeiro apareceu
  na re-auditoria como `missed-in-phase-2`.
- **eal:** *callback hell* (o padrão superado não virou finding de AP-14) e o banco em memória.
- **tma:** relatórios com dezenas de `COUNT`, exclusão de categoria deixando tarefas órfãs,
  serialização `to_dict` duplicada, `print` como log e condicionais verbosas.

**Achados além do gabarito.** São problemas reais que o gabarito não listou:
- **Credenciais em seeds** (csp, tma): o gabarito decidiu não listar ("são dados de exemplo"); a
  skill, pela regra nova de AP-01, tratou como credenciais reais no datastore de runtime.
- **Advisories verificados** (csp: flask e flask-cors; eal: transitivas do express; tma: flask e
  flask-cors): o gabarito suspeitava de alguns, mas não listou porque não tinha fonte viva. A skill
  consultou OSV.dev e citou fonte e data. No tma, o advisory do flask-cors foi **observado**: o
  original respondeu a um preflight de rede privada com `Access-Control-Allow-Private-Network: true`.
- **Página de erro padrão do Express vazando stack trace e caminhos absolutos** (eal), observada.
- **Entrada com tipo errado derrubando o processo** (eal), observada no baseline como erro de
  transporte e depois `FIXED`.
- **CRUD de categorias dentro de `report_routes`** (tma).

**Ressalva sobre o gabarito.** A sessão que o escreveu carregou o `CLAUDE.md` do repositório (ela
mesma declara isso). Portanto não rodou na worktree cega de `6d1ce62`. Ela afirma não ter lido o
catálogo nem os relatórios de rodada. O `CLAUDE.md` cita três exemplos genéricos que coincidem com
itens do gabarito (P1 #4, P2 #5, P1 #11), todos óbvios o bastante para serem achados de qualquer
forma.

## Os 13 problemas da rodada 1: o que aconteceu

| # | Problema da rodada 1 | Rodada 2 |
|---|---|---|
| 1 | Porta fixa no original | ✓ Resolvido. Launcher fora da árvore no csp e no eal; o original não foi editado. No tma o override usado (`flask run --port`) também desliga o debug, então o debug console não foi observado rodando (R2-3) |
| 2 | Runtime sem as dependências declaradas | ✓ Resolvido. Os três instalaram as dependências declaradas no snapshot e registraram isso. Faltou dizer onde fica o ambiente da aplicação **refatorada** (R2-2) |
| 3 | Escrita na Fase 2 fora de `reports/` | ✓ Resolvido. Nenhum arquivo de runtime apareceu nos alvos; os três snapshots foram apagados |
| 4 | Crash no baseline virava `UNVERIFIED` | ✓ Resolvido. No eal, duas requisições derrubavam o original; foram recapturadas por §3.1 e terminaram `FIXED (baseline: transport error)` |
| 5 | Corpo em texto puro comparado como `opaque` | ✓ Resolvido. As respostas em texto do eal foram comparadas pelo esqueleto |
| 6 | Contradição sobre autorização | ✓ Resolvido. Os três aplicaram o teste do uso legítimo da mesma forma: sem modelo de identidade, a autorização foi proposta |
| 7 | Sem entrada para configuração insegura | ✓ Resolvido. AP-18 usada nos três |
| 8 | Sem entrada para dependência vulnerável | ✓ Resolvido. AP-19 usada nos três. Mas as regras dela têm arestas (R2-6) |
| 9 | Entradas de ataque marcadas como `REGRESSION` | ◐ Em grande parte. 21 entradas de segurança terminaram `FIXED`. Continua sem lugar a entrada hostil cuja correção muda a resposta sem rejeitá-la (R2-5) |
| 10 | Upgrade de dependência versus contrato | ◐ A regra foi aplicada com os headers comparados, mas o RP-18 contradiz o §6 das guidelines (R2-6) |
| 11 | Finding parcialmente resolvido | ✓ Resolvido. O resto de um finding parcial virou `unresolved` (tma) ou `proposed` (eal) |
| 12 | Superfície não cresce depois do baseline | ✓ Resolvido. eal e tma capturaram entradas tardias contra o original (§4.3) |
| 13 | Recall da Fase 2 | ◐ Melhorou. Seeds com credenciais e a página de erro padrão foram achadas na Fase 2. Ainda restaram 5 `missed-in-phase-2`, quase todos da mesma família (R2-8) |
| — | Subagente escrevendo no git | ✓ Resolvido. Nenhum comando git de escrita nos três; o índice dos sandboxes ficou vazio |

## Problemas da skill revelados nesta rodada

Insumos para a iteração 3. **Nenhum foi corrigido nesta rodada**, porque a skill ficou congelada.
Consolidam as seções *Skill friction* dos três logs (14, 16 e 15 itens).

| # | Problema | Visto em |
|---|---|---|
| R2-1 | **Encerrar processos sem regra de segurança.** No tma, o subagente rodou `taskkill /F /IM python.exe`, que pode matar qualquer processo Python da máquina, não só o seu. Depois passou a encerrar só processos cuja linha de comando continha o caminho do snapshot. A skill manda "subir e derrubar a aplicação", mas não diz como derrubar só o que ela subiu | tma |
| R2-2 | **Ciclo de vida do snapshot incompleto.** O passo 3c.6 apaga o snapshot antes da re-auditoria (3d), que ainda precisa de runtime. Não diz onde ficam as dependências da aplicação refatorada, que agora podem ter outras versões. A aplicação refatorada roda no alvo e cria banco e `__pycache__` ali | csp, eal, tma |
| R2-3 | **Opções de porta com efeitos colaterais.** O launcher do §1.2 supõe que o original exporta o objeto da aplicação (no eal ele não exporta nada) e não diz se copia as flags de debug e bind. O override de porta do framework pode desligar o debug, e aí a evidência de AP-18 não é observada | csp, eal, tma |
| R2-4 | **Campos da Fase 1.** `Target: <path relative to CWD>` é impossível quando o alvo está em outro drive. O bloco não tem campo para comando de boot, porta e ambiente, que o `01` manda registrar. O `01` §5 manda escrever `surface.json` na Fase 1, que é só de leitura. A regra de exclusão de arquivos não menciona `.claude/` | csp, eal, tma |
| R2-5 | **Entradas de segurança que não cabem em "rejeitada".** Não há estado para entrada hostil cuja correção muda a resposta sem rejeitá-la (a injeção na busca virou `REGRESSION`). O harness só envia corpo JSON, então não dá para testar corpo malformado. Não há mecanismo para isolar uma entrada destrutiva | csp, eal |
| R2-6 | **Arestas de AP-19/RP-18.** O RP-18 manda ficar na mesma major e propor quando a correção está só na major seguinte, enquanto o §6 aceita major se o replay cobrir o que muda. "Versão corrigida mais baixa" engana quando a correção é opt-in. A regra de sobreposição com AP-14 diz que o advisory sempre domina, mesmo quando é só de instalação. "Sem lockfile" não diz o que fazer com pins exatos, e o pip não tem comando de lock. A escala não tem degrau para advisory LOW em pacote de runtime. AP-14 exige sucessor nomeado mesmo quando o upstream não nomeia nenhum | csp, eal, tma |
| R2-7 | **Contradições no gate de contrato.** O §6 das guidelines chama de mudança de contrato alterar o shape da resposta de erro; o RP-17 chama de seguro trocar a página de erro padrão. Não diz se mascarar um valor vazado mantendo o campo é seguro. Um finding `missed-in-phase-2` que precisa de decisão de produto é forçado a `unresolved`, e não a `proposed`. Não há regra para correção que exige dependência nova (servidor de produção) | csp, eal, tma |
| R2-8 | **Família recorrente de achados perdidos: integridade de dados.** Unicidade de e-mail (csp, eal), itens duplicados no pedido, transições de status livres (csp), limite de tamanho de requisição (tma). Todos apareceram só na re-auditoria. No gabarito, a mesma família aparece em itens que a skill não achou (esquema sem restrições, órfãos). O catálogo tem sinais de invariantes de domínio em AP-11, mas nada sobre restrições do esquema | csp, eal, tma |
| R2-9 | **Template do relatório.** `audit-latest.md` deixa de ser cópia do relatório com timestamp, porque só ele recebe a Fase 3. O prompt de confirmação aparece no template, mas não deve ser impresso com `--yes`. `## Proposed, Not Applied` aparece duas vezes. O `File:` pede intervalo que não seja o arquivo inteiro, o que conflita com God Module | csp, eal, tma |
| R2-10 | **Laço de correção indefinido.** O playbook manda fazer replay depois de cada transformação e o SKILL.md tem um replay só. Não diz se o que a re-auditoria encontra pode ser corrigido na mesma rodada. Os três decidiram de formas diferentes | csp, eal, tma |
| R2-11 | **Bugs do harness.** As mensagens dos probes citam "protocol 3.2", mas a seção é a §3.1. O aviso de "vários erros de transporte" conta erros que já estavam no arquivo mesclado com `--merge`. O `capture --only --merge` imprime o total do arquivo, e não o que capturou agora. O teste de conformidade não cobria `--merge` com erros preexistentes | eal, tma |
| R2-12 | **Regras de escalonamento concorrentes.** AP-03 e AP-05 escalam em direções opostas para módulos de rota com um único conceito, e o número de findings depende de qual se escolhe | tma |

## Desvios dos subagentes

- **eal:** comparou também valores das respostas, com um script próprio, além do protocolo. Tudo
  bateu, exceto a ordem de um array que o original não garantia. Escreveu dois arquivos temporários
  fora do diretório permitido e os apagou em seguida. Removeu `sqlite3.verbose()`.
- **csp:** um arquivo auxiliar caiu na pasta do sandbox e foi movido para o snapshot no mesmo passo.
  Mascarou `senha` e `secret_key` como `"********"` mantendo o campo, e considerou isso seguro (R2-7).
- **tma:** fez uma segunda rodada de validação e checagens manuais (header de rede privada, migração
  de senhas MD5 no login, recusa de subir sem `SECRET_KEY`). Atualizou o README. Não rodou
  `pip list --outdated`.

## O que ficou pendente

**Os três projetos:**
- **Rotacionar credenciais.** Saíram do código, mas continuam no histórico do git.
- **Proposto, não aplicado: autenticação e autorização.** Nenhum dos três tem modelo de identidade;
  é o caso de proposta da D15.

**Por projeto:** a lista completa, com justificativas, está nos relatórios de auditoria. Destaques:
- **csp:** 9 propostas, entre elas as rotas administrativas, as contas do seed e a paginação.
- **eal:** 4 propostas: autorização, remoção da senha padrão, substituição do driver `sqlite3`
  (deprecated upstream, sem sucessor nomeado) e a política de exclusão de usuários com dados
  vinculados.
- **tma:** 5 propostas: autorização, remoção do hash de senha das respostas, flask-cors 6.x,
  restrição de CORS e paginação. O servidor de desenvolvimento continua como comando de start, o
  que conta como `unresolved`.

## Intervenções

- **Sessão orquestradora:** nenhuma correção de rumo durante as rodadas.
- **tma:** o `taskkill` amplo (R2-1). Não há evidência de que tenha derrubado outro processo (a
  rodada do csp, também em Python, terminou normalmente), mas não é possível descartar.

## Evidência

Os arquivos abaixo estão na branch `round2`.

| Projeto | Relatório de auditoria | Transcript | Baseline / replay |
|---|---|---|---|
| code-smells-project | [`reports/audit-project-1.md`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/blob/round2/reports/audit-project-1.md) | [`runs/code-smells-project-iter2.md`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/blob/round2/runs/code-smells-project-iter2.md) | [`code-smells-project/reports/`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/tree/round2/code-smells-project/reports) |
| ecommerce-api-legacy | [`reports/audit-project-2.md`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/blob/round2/reports/audit-project-2.md) | [`runs/ecommerce-api-legacy-iter2.md`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/blob/round2/runs/ecommerce-api-legacy-iter2.md) | [`ecommerce-api-legacy/reports/`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/tree/round2/ecommerce-api-legacy/reports) |
| task-manager-api | [`reports/audit-project-3.md`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/blob/round2/reports/audit-project-3.md) | [`runs/task-manager-api-iter2.md`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/blob/round2/runs/task-manager-api-iter2.md) | [`task-manager-api/reports/`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/tree/round2/task-manager-api/reports) |
