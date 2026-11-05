# Rodada 7 — verificação gerada, não escrita (D28)

> Datas: 2026-11-04/05. Skill: `feat/round7` em `19c215c` (D1–D28). Lista de mudanças congelada
> antes da implementação: [`round7-changes.md`](round7-changes.md) (R1–R12). Insumo:
> [`round6-skill-results.md`](round6-skill-results.md) (G1–G10) e a Parte 2 do gabarito
> ([`../gabarito.md`](../gabarito.md)). **Contaminação declarada:** a lista foi escrita depois de ler o
> gabarito e o relatório dos verificadores independentes.

## 1. Como a rodada rodou

- **Ponto de partida:** o código original dos três projetos (`7ef5932`), com a skill da rodada 7 por
  cima. Um worktree e um branch por projeto: `round7/clean-p1..p3`. Tags de execução:
  `run/code-smells-project/iter7`, `run/ecommerce-api-legacy/iter7` e `run/task-manager-api/iter9`.
- **Isolamento (D3):** um subagente novo por projeto, sem nenhum contexto além da invocação da skill.
- **Gate:** cada subagente parou no `[y/n]`. A sessão orquestradora repassou a pergunta ao autor
  literalmente e a resposta dele de volta, sem responder por ele. Nenhuma execução usou `--yes`.
- **Interrupções:** P1 e P2 pararam por limite de taxa da API no meio da Fase 3. Foram retomados na
  mesma sessão do subagente, depois do reset, sem novo contexto.

## 2. Resultados

| | P1 `code-smells-project` | P2 `ecommerce-api-legacy` | P3 `task-manager-api` |
|---|---|---|---|
| Findings Fase 2 (C/H/M/L) | 33 (12/9/8/4) | 19 (8/5/1/5) | 32 (12/8/8/4) |
| Resposta no gate | `y` | `y` | `y D1=business D2=privileged` + condição |
| Replay | 39 PASS, 0 REGRESSION, 1 UNVERIFIED | 11 PASS, 0 REGRESSION | 69 PASS, 0 REGRESSION |
| Entradas de segurança | 12 FIXED | 4 FIXED | 5 FIXED |
| Entrada malformada | 242 ROBUST / 12 operações | 59 ROBUST / 3 operações | 401 ROBUST / 16 operações |
| Valores | 6 HOLDS | 2 HOLDS | 13 HOLDS |
| Resolvidos / propostos / não resolvidos | 22 / 10 / 1 | 15 / 4 / 0 | 20 / 12 / 0 |
| `missed-in-phase-2` | 2 (1 corrigido, 1 proposto) | 0 | 0 |
| Defeitos introduzidos (achados na re-auditoria) | 0 | 2, corrigidos | 0 |
| Processos | 12/12 | 12/12 | 20/20 |
| Comandos (`cd`, encadeamento) | 0 / 0 | 0 / 0 | 0 / 0 |

Detalhe por projeto: seção C do [`README.md`](../../README.md) e `reports/audit-project-{1,2,3}.md`.

## 3. O que a D28 mudou na prática

**Matriz de robustez (R1–R3).** As 702 variantes geradas saíram `ROBUST` nos três projetos. O efeito
aparece nos baselines:
- **P3:** o original tinha 105 respostas 500 no baseline, e o replay final não tem nenhuma.
- **P2:** um `card` com tipo errado derrubava o processo em cinco variantes. Agora as cinco respondem 400.

São exatamente as classes que a verificação independente da rodada 6 achou e o replay não via (G1/G2).

**Asserções de valor (R5).** Dinheiro, relatórios e campos mascarados viraram entrada `value` nos três
projetos, com 21 `HOLDS` no total. O que o harness não alcança foi declarado `UNVERIFIED by the
harness` no bloco DEGRADED, e não contado como prova:
- **P1:** o hash da senha em repouso e o e-mail fora do log.
- **P2:** a máscara do cartão no log e o formato da senha.
- **P3:** o header de rede privada, o `PRAGMA foreign_keys` e o rehash de MD5 legado.

**Segredos (R8).** `surface.json` usa `{{env:NOME}}` nas três execuções. Antes do commit, um `grep` nos
`reports/` achou só referências e shapes. As duas senhas literais no P1 (`senha-que-nao-confere`,
`qualquer`) são senhas erradas de propósito.

**Classificação no gate (R9).** O P1 e o P2 não tinham caso ambíguo, e o relatório diz "none" com o
motivo. O P3 levou dois casos ao gate:
- **D1, `GET /reports/user/<id>`:** o autor respondeu business, e a operação foi proposta.
- **D2, `PUT /users/<id>`:** o autor respondeu privileged, com uma condição. Exige-se a credencial de
  operador só quando `role` ou `active` mudam para um valor diferente do guardado. O replay cobre os
  três caminhos: sem credencial 403, com credencial `PASS`, reenvio do valor guardado `PASS`.

Na rodada 6, a mesma skill tinha decidido D1 de jeitos diferentes em duas execuções (T7). Agora a
decisão é de uma pessoa e fica no cabeçalho do relatório.

**Resíduo de operador (R10).** Rotacionar segredo que ficou no histórico e resetar senha legada de
quem nunca loga foram classificados como `proposed`, com o passo operacional e o SQL, nos três
projetos. Na rodada 6, isso era `unresolved` ou ficava fora do relatório.

**`.gitignore` (R7c).** Os três projetos saíram com arquivo de exclusão que cobre segredo local, banco,
caches e dependências instaladas (T2).

## 4. Defeitos e desvios desta rodada

1. **P3, afirmação não observada na Fase 2.** O finding AP-20 dizia ter observado uma tarefa órfã ao
   apagar uma categoria. O ORM zera o `category_id`, então isso nunca aconteceu. A re-auditoria
   checou contra o original e corrigiu a afirmação ao lado do finding, deixando o relatório do gate
   intacto. Pela rubrica (D8), é um finding com descrição falsa.
2. **P3, mudança de header que o replay não cobre.** Com o `flask-cors` 6.0.0, o preflight de rede
   privada responde `Access-Control-Allow-Private-Network: false`, e o original respondia `true`. O
   baseline não mandava o header de pedido, então nenhuma entrada viu a diferença. O agente observou à
   parte e declarou `UNVERIFIED`, mas o upgrade foi aplicado como se o replay cobrisse a mudança de
   comportamento (D18). Para um cliente de navegador numa rede privada, é mudança de contrato.
3. **P2, reinício do original no mesmo container.** O original caiu 6 vezes durante o baseline e foi
   reiniciado dentro do mesmo container, e não numa cópia nova (protocolo §3.1). O banco é em memória e
   a aplicação não escreve arquivo, então o efeito é provavelmente nulo. Está declarado no relatório.
4. **P1, dois `missed-in-phase-2` no mesmo sinal.** A linha do livro de sinais para "invariante de
   domínio não aplicada" examinou só a criação de pedidos:
   - status de pedido inexistente respondia 200, e foi corrigido para 404;
   - transições livres de status, e foram propostas.

   O livro de sinais (R6) mostra onde o agente procurou, e foi por ele que deu para ver o furo. Mas ele
   não garante cobertura.
5. **P1, uma entrada de segurança `UNVERIFIED`.** O payload `'` por acaso era SQL válido no original. A
   entrada foi substituída, e não editada, por outra capturada contra o original. É o comportamento
   pedido pelo protocolo.
6. **Boots em foreground.** Os três agentes rodaram pelo menos um boot com `exec` em primeiro plano, e
   não com `exec -d`:
   - P1 e P3, para ler os warnings forçados no stderr, com o `exec` limitado por `timeout` ou mantido
     por tarefa de fundo;
   - P2, para ler o erro do upgrade que não subia.

   O handle continuou sendo o container, removido pelo nome exato, e o P1 e o P3 declararam o desvio.
   É um sinal de que o protocolo não diz como ler o stderr de um processo destacado.

## 5. Critério de saída (de `round7-changes.md`)

| Critério | Estado |
|---|---|
| Zero 5xx em entrada malformada **no verificador independente**, e zero `NOT ROBUST`/`REGRESSION` na matriz | **Parcial.** A matriz está limpa nos três (702 variantes). O verificador independente **não rodou** sobre esta entrega. |
| Zero defeito introduzido | **Atendido na entrega final**, pelo que a skill mede: os 2 introduzidos no P2 foram achados e corrigidos antes do replay final. Não há verificação externa. |
| Todos os itens da Parte 2 detectados pela Fase 2 ou, se de origem `V`, tratados | **Não medido.** O casamento com a Parte 2 não foi feito. |
| `git status` limpo e sem segredo nos artefatos | **Atendido.** Worktrees commitados; `grep` nos artefatos limpo. |
| Nenhuma execução com `--yes`; três sessões novas; gate humano | **Atendido**, com a ressalva de que a resposta foi repassada pela sessão orquestradora. |

## 6. Itens transversais da Parte 2 (T1–T9)

| # | Problema | Rodada 7 |
|---|---|---|
| T1 | Artefatos gravam senhas e tokens | Resolvido nas três execuções (`{{env:…}}`) |
| T2 | A skill não gera nem preserva `.gitignore` | Resolvido nas três execuções |
| T3 | `proc start` falha em imagem slim | Não se repetiu; o container é o handle, e o caminho via `/proc` está no teste de conformidade |
| T4 | Identificador de execução só por timestamp | Resolvido: run id `<timestamp>-<8 hex>` nos rótulos e no scratch |
| T5 | AP-17 reporta trilha de auditoria | Não se repetiu no P2, o projeto que tem tabela de auditoria |
| T6 | Sinal listado como verificado e não reportado | Livro de sinais presente nos três; o P1 mostra que a cobertura dele ainda pode ser rasa (§4.4) |
| T7 | Classificação privilegiada/negócio diverge entre execuções | Resolvido por desenho: o caso ambíguo vai ao gate |
| T8 | O replay compara forma, não valor | Entradas `value` nos três; o que não tem entrada é `UNVERIFIED` |
| T9 | AP-11 "subconjunto seguro" incompleto | Matriz `ROBUST` nos três |

## 7. Pendências e candidatos para a próxima rodada

- **Repetir a verificação independente** (`docs/verification/delivery-test-plan.md`, com os valores-limite
  da G2) sobre esta entrega. É o critério de saída que falta.
- **Scorecards da rodada 7** (`docs/evals/run-p<N>-iter<K>.md`), com o recall sobre a Parte 1 e sobre a
  Parte 1 + 2, separados, conforme a regra da Parte 2.
- **Header de pedido em preflight.** Quando o upgrade mexe em `Access-Control-*`, o baseline deveria
  exercitar também os headers de pedido opcionais (rede privada, credenciais). Hoje a D18 compara os
  headers de resposta, mas só sobre os pedidos que o agente escreveu (§4.2).
- **Leitura de stderr com processo destacado.** O protocolo deveria dizer como ler warnings forçados sem
  manter um `exec` em primeiro plano (§4.6).
- **Campo `Root cause of:`** no finding, para ligar um sintoma (operação aberta) à causa (ausência de
  modelo de identidade), na linha discutida durante o gate do P3. É candidato e ainda não foi decidido.
