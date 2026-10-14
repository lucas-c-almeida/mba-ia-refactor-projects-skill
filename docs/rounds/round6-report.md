# Rodada 6 — operação privilegiada (D27) nos três projetos-alvo

- **Data:** 2026-10-08 a 2026-10-10
- **Origem:** mensagem de correção do avaliador sobre a entrega da rodada 5. Os relatórios marcam
  AP-04 como CRITICAL nos 3 projetos, mas a Fase 3 só o propunha: no `code-smells-project`,
  `POST /admin/reset-db` continuava apagando as quatro tabelas e `POST /admin/query` continuava
  executando o SQL do corpo, para qualquer chamador anônimo. Pedido: (1) ajustar o teste de uso
  legítimo para que rotas administrativas ou destrutivas sem uso anônimo legítimo sejam protegidas ou
  removidas na Fase 3; (2) rodar a skill de novo nos três.
- **Branch com a skill e o código refatorado:** `feat/round6` (local, `e40b5f3`; skill final em
  `a55d997`). **Não está neste `main`.** Este relatório é o único artefato da rodada commitado aqui.
- **Branches de evidência (locais, uma por execução):** `round6/p1`, `round6/p2`, `round6/p3`
  (primeira execução), `round6/p1-iter2`, `round6/p3-iter2`, `round6/p3-iter3`.
- **Partida (D3):** todas as execuções partiram de `7ef5932` (tag `run/code-smells-project/iter5`),
  em worktrees git novos, um por execução. As tags `run/p<N>/iter<K>` desta rodada não foram criadas:
  o isolamento ficou nos branches acima.

## ⚠ Contaminação declarada (D12)

O autor leu os relatórios da rodada 5, que citam as rotas concretas, e o texto da D27 foi escrito e
emendado duas vezes **depois de ver** execuções reais dos alvos (ver "Como o texto da D27 mudou").
A mudança é uma regra de decisão (quem é rejeitado), não uma varredura nova: o que a auditoria
procura não muda; muda o que a Fase 3 faz com um finding de AP-04 que já era detectado. O recall
não é afetado. O que muda é a razão `resolved` / `proposed`, e é só isso que esta rodada mede.

## Como a rodada foi executada

- **Subagentes isolados, em paralelo na primeira execução.** Cada projeto rodou em um subagente
  novo (contexto zerado), em um worktree próprio, com a skill copiada para a raiz do worktree e para
  o subdiretório do projeto. Nenhum subagente leu relatórios de outra execução.
- **`--yes` nas seis execuções.** Subagente não consegue responder o gate da Fase 2. Os relatórios
  registram o texto literal da skill para esse modo (`--yes (auto-approved, not human-reviewed)`).
  **Estas execuções não são equivalentes às da rodada 5, em que o autor respondeu o gate.**
- **Isolamento:** container (docker 28.5.2, `python:3.13-slim` e `node:24.12.0`) nos seis casos.
- **Regras de comando (D25):** passadas por escrito a cada subagente. Resultado: 0 `cd` e 0
  encadeamentos nas seis execuções, pela contagem do próprio subagente.
- **Quatro execuções além do necessário:** três por causa de ambiguidade do texto (abaixo), e uma
  retomada depois de um limite de uso da API que interrompeu a terceira execução do projeto 3 no meio
  (reconciliada pelo próprio subagente: containers conferidos pelo rótulo, baseline parcial de 63
  entradas completado para 67, declarado no relatório da execução em "Run continuity").

## Mudança na skill (D27, emenda à D15)

**A falha de raciocínio na D15.** A pergunta "quem recebe a nova rejeição?" era respondida com "todo
cliente atual" sempre que não havia modelo de identidade. Isso vale para operações que clientes comuns
existem para chamar; não vale para uma operação cujo único chamador legítimo é um operador. Ali, quem
chama anonimamente é, por definição, o atacante, e o bloqueio só muda o que o uso ilegítimo observa —
o mesmo raciocínio que torna parametrizar uma query seguro.

**Texto final (em `04-architecture-guidelines.md` §6, espelhado em `SKILL.md`, RP-04, AP-04 e
`06-validation-protocol.md`):**

- Uma operação é **privilegiada** quando: executa consulta ou código vindo da requisição; destrói ou
  reinicia dados em massa; apaga ou desativa uma **conta** por id da requisição em aplicação sem
  modelo de identidade; é de manutenção ou diagnóstico; ou devolve um **agregado gerencial**
  (valores financeiros ou rollups por cliente/usuário).
- **Modelo de identidade = verificação, não emissão.** Só há identidade quando alguma operação
  verifica uma credencial apresentada. Token emitido e nunca conferido, papel lido do corpo e "usuário
  atual" nunca estabelecido não contam.
- **Não** é privilegiada, por mais destrutiva ou ampla que pareça: criar/editar/apagar registro de
  domínio ordinário; listagem ou consulta simples (inclusive de contas); contagem de registros por
  estado; login, cadastro, checkout. Ambíguo, propõe.
- **Correção, em ordem de preferência:** *remover* da superfície quando a operação é insegura por
  construção (executa entrada arbitrária, reinicia dados); senão *proteger* com credencial de operador
  lida de configuração, comparação em tempo constante, **fechada por padrão** (403 sem a variável).
  Não é modelo de identidade: não inventa usuários, papéis nem política.
- **Validação:** a chamada anônima de uma operação privilegiada vira entrada `security`
  (`rejected`), nunca `REGRESSION`; o caminho do operador é verificado com a credencial no replay, ou
  rotulado como verificado à mão.

### Como o texto da D27 mudou durante a rodada

| Versão | Motivo | Evidência |
|---|---|---|
| Original | resposta ao avaliador | P1 `round6/p1`, P2 `round6/p2`, P3 `round6/p3` |
| Emenda 1 | os subagentes leram os casos cinzentos de formas diferentes: exclusão de conta foi privilegiada no P3 e de negócio de produto no P1; "agrega todos os principais" foi lido como listagem num projeto e como relatório noutro | P1 `round6/p1-iter2`, P3 `round6/p3-iter2` |
| Emenda 2 | a repetição do P3 divergiu da primeira: o app emite um token no login que nenhuma rota verifica, e "modelo de identidade" era definido como "login, sessão ou token", então `DELETE /users/<id>` ficou proposto | P3 `round6/p3-iter3` |

A emenda 2 também afinou o agregado: uma primeira redação ("carrega dado por principal") teria
rebaixado o relatório de vendas do projeto 1 para negócio e desfeito a proteção que o avaliador pediu;
foi corrigida antes de ser usada, para "valores financeiros ou rollups por cliente/usuário".

## Critérios de aceite (`instructions.md`) — última execução de cada projeto

| Critério | code-smells-project (`p1-iter2`) | ecommerce-api-legacy (`p2`) | task-manager-api (`p3-iter3`) |
|---|---|---|---|
| Fase 1 detecta a stack | ✓ Python 3.13 · Flask 3.1.1 · SQLite | ✓ Node 24 · Express 4.22.1 · sqlite3 | ✓ Python 3.13 · Flask 3.0.0 · SQLite |
| Fase 2 encontra ≥ 5 findings | ✓ 29 | ✓ 21 | ✓ 30 |
| Fase 2 tem ≥ 1 CRITICAL/HIGH | ✓ 12 C · 5 H | ✓ 5 C · 9 H | ✓ 9 C · 7 H |
| Fase 3: a aplicação funciona | ✓ 37 PASS, 0 REGRESSION | ✓ 9 PASS, 0 REGRESSION | ✓ 57 PASS, 0 REGRESSION |

3/3 em todos os critérios.

## Resumo por execução

| | P1 it1 | P1 it2 | P2 it1 | P3 it1 | P3 it2 | P3 it3 |
|---|---|---|---|---|---|---|
| Texto D27 | original | emenda 1 | original | original | emenda 1 | emenda 2 |
| Findings (C/H/M/L) | 27 (10/8/6/3) | 29 (12/5/9/3) | 21 (5/9/2/5) | 32 (9/7/10/6) | 30 (7/8/12/3) | 30 (9/7/8/6) |
| Replay | 36 PASS | 37 PASS | 9 PASS | 39 PASS | 48 PASS | 57 PASS |
| Regressões | 0 | 0 | 0 | 0 | 0 | 0 |
| Entradas de segurança | 12 FIXED | 11 FIXED | 3 FIXED | 9 FIXED | 16 FIXED | 10 FIXED |
| Resolvidos | 20/27 | 23/29 | 17/21 | 25/32 | 24/30 | 23/30 |
| Propostos / não resolvidos | 7 / 0 | 6 / 0 | 4 / 0 | 7 / 0 | 6 / 0 | 6 / 1 |
| Linha da re-auditoria (D14) | `⚠` | `○` | `○` | `○` | `○` | `⚠` |
| Passadas de re-auditoria | 2 | 2 | 2 | 2 | 2 | 2 |
| Containers subidos/derrubados | 11 / 11 | 15 / 15 | 19 / 19 | 19 / 19 | 16 / 16 | 17 / 17 |

Nenhuma execução imprimiu `✓ Zero anti-patterns remaining`: correto pela D14, já que todas restaram com
itens `PROPOSED, NOT APPLIED`.

## ⭐ O que a D27 fez, por projeto (resposta direta ao avaliador)

| Rota | Classificação | Ação |
|---|---|---|
| P1 `POST /admin/reset-db` | privilegiada (reinicia dados + namespace administrativo) | **removida**, agora 404 |
| P1 `POST /admin/query` | privilegiada (executa consulta vinda da requisição) | **removida**, agora 404 |
| P1 `GET /relatorios/vendas` | privilegiada (agregado financeiro) | **guarda**, 403 sem `OPERATOR_TOKEN` |
| P2 `GET /api/admin/financial-report` | privilegiada (agregado financeiro por aluno) | **guarda**, 403 sem `OPERATOR_TOKEN` |
| P2 `DELETE /api/users/:id` | privilegiada (apaga conta, sem identidade) | **guarda**, 403 sem `OPERATOR_TOKEN` |
| P3 `GET /reports/summary` | privilegiada (rollup por usuário) | **guarda** (na it3), 403 sem `OPERATOR_TOKEN` |
| P3 `DELETE /users/<id>` | privilegiada (apaga conta; token emitido nunca verificado) | **guarda** (it1 e it3; ficou proposta na it2) |

Em todas as execuções, a chamada anônima das rotas guardadas voltou 403 (`FIXED`, baseline 200) e o
caminho do operador, exercitado no próprio replay com `X-Operator-Token`, voltou o mesmo status e shape
do baseline (`PASS`). As rotas removidas do P1 voltam 404 (`FIXED`).

**Continuam propostas, por desenho:** AP-04 de operações de negócio nos três (sem modelo de identidade,
todo cliente atual receberia 401), senhas de seed documentadas no README, dev server de produção
(dependência nova), CORS, chaves estrangeiras e regra de exclusão, paginação, limites e formatos de
validação, e a major do flask-cors quando o changelog não cobre a mudança.

## Divergências entre execuções do mesmo projeto

| Projeto | Divergência | Causa | Tratamento |
|---|---|---|---|
| P3 it1 × it2 | `DELETE /users/<id>`: guardada × proposta | texto dizia "sem identidade = sem login, sessão **ou token**"; o app emite token que nenhuma rota verifica | emenda 2 |
| P3 it1 × it2 | `GET /tasks/stats`: aberta × proposta (negócio) | "agregado" sem critério de conteúdo | emenda 2 |
| P1 it1 × P3 it1 | exclusão de registro de domínio: negócio × privilegiada | "apaga conta ou registro" no mesmo item | emenda 1 |
| P3 it1 × it3 | MD5 do usuário: resolvido (scrypt + upgrade no login) × `unresolved` (PBKDF2 só em contas novas; MD5 legado mantém a verificação) | variância de execução, não de texto | **não tratado**; ver pendências |

O P1 convergiu entre as duas execuções (as mesmas rotas, a mesma classificação). O P3 só convergiu
**depois** de duas emendas, e a it3 é a única execução que usa o texto final. **O P1 it2 usou a emenda
1 e o P2 it1 usou o texto original**; para o P2, o resultado não muda sob o texto final (relatório
financeiro e exclusão de conta são privilegiados em qualquer versão), mas nenhuma execução do P1 e do
P2 usa o texto final.

## Incidentes e limitações

- **Gate humano ausente.** `--yes` nas seis execuções. O gate foi exercitado por pessoa na rodada 5, não
  nesta.
- **`proc start` falha em imagem slim** (P1 it1/it2, P3 it1/it2/it3): "could not read the start time".
  Os subagentes recorreram a `docker exec`, a um launcher fora da árvore ou ao processo principal do
  container; a captura de warnings do servidor ficou `DEGRADED` no P3, declarada.
- **Scratch compartilhado entre sessões simultâneas.** Arquivos de consulta OSV com nome genérico
  foram sobrescritos por outro subagente (P1 it2) ou já existiam (P3 it2). Os resultados usados vieram
  dos corpos escritos na hora; as execuções seguintes receberam um sufixo por execução nos nomes.
- **Colisão de rótulo de container.** O rótulo de execução baseia-se só no timestamp; duas execuções
  simultâneas compartilharam o rótulo (P1 e P3, 2026-10-08 15:00). Nenhuma tocou no container da outra.
  As execuções seguintes receberam um sufixo.
- **Commit com a cópia da skill.** O primeiro lote de commits dos subagentes incluiu a cópia da skill
  dentro do alvo e as edições da raiz do worktree (`git add -A`). Corrigido nas repetições com um stage
  restrito ao alvo.
- **Tokens de teste em `surface.json`** (`OPERATOR_TOKEN` fixo do replay) nos três projetos. São
  valores de fixture, declarados nos relatórios, mas um scanner de segredos os marcaria.
- **Verificado só à mão, não pelo replay** (a comparação é por shape): mascaramento de senha,
  upgrade de hash no login, migração de preço para centavos, caminho de operador com token errado.
- **Não verificado:** camada 1 de deprecation sobre as entradas destrutivas e sobre o app refatorado em
  parte das execuções; migração de banco legado com pedidos ou e-mails duplicados; OSV.dev não
  consultado no P2 (usou `npm audit`/`npm view`); changelogs de major do flask-cors.
- **Erro do orquestrador, durante o sync para esta branch.** Usei `robocopy /MIR` para trazer o
  código refatorado e ele apagou um `.venv` local não versionado de `task-manager-api`. Regenerável
  (`python -m venv .venv` e `pip install -r requirements.txt`); nada versionado foi perdido além do
  que a refatoração substitui por desenho.

## Candidatos para depois da rodada (a skill, não executados aqui)

1. **`proc start` em imagem slim sem start time:** cair para `docker exec` com saída capturável é
   hoje improvisação de cada subagente; merece um caminho documentado no protocolo.
2. **Rótulo de container e scratch com identificador de execução** (não só timestamp), para execuções
   simultâneas.
3. **Instrução de commit nos worktrees:** stage restrito ao alvo, sem a cópia da skill.
4. **Upgrade de hash de senha (AP-08):** a skill deve dizer o que fazer com contas que nunca logam,
   ou declarar o resíduo como proposta (P3 it3 deixou `unresolved`).
5. **Classificação parcial de AP-11:** o P3 it2 reconheceu ter marcado o finding inteiro como
   contract-changing quando um subconjunto era seguro pela linha 4 da tabela; a it3 acertou depois de
   instrução explícita no prompt. Falta texto na skill que force a separação.

## Intervenções

- **Orquestrador:** três intervenções de método, todas registradas acima — redigir a emenda 1 e a
  emenda 2 depois de ver divergências, e retomar a it3 do P3 após o limite de uso.
- **Humano:** duas decisões, ambas sobre o texto — escolher "esclarecer" em vez de "estreitar" a
  fronteira (opção B), e repetir os projetos 1 e 3. Nenhuma durante a execução dos subagentes.

## Evidência

Tudo na branch local `feat/round6` (`e40b5f3`) e nos branches `round6/*`; **nada foi enviado ao
remoto**. O relatório de auditoria de cada projeto está em `reports/audit-project-N.md` e em
`<projeto>/reports/audit-latest.md`, junto de `surface.json`, `baseline.json` e `replay*.json`/
`current.json`.

| Projeto | Execução usada na entrega | Commit |
|---|---|---|
| code-smells-project | `round6/p1-iter2` | `f19b8e5` |
| ecommerce-api-legacy | `round6/p2` | `ac04dcc` |
| task-manager-api | `round6/p3-iter3` | `af440d3` |

A skill final está em `.claude/skills/refactor-arch/` de `feat/round6` e, ao fim, copiada para os três
projetos. A mudança de texto está em `docs/rounds/round6-changes.md` e no ADR D27 em
`docs/decisions.md`, ambos em `feat/round6`.
