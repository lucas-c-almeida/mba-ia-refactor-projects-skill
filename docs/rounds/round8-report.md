# Rodada 8 — tomar ou bloquear conta é operação privilegiada (D29)

> Datas: 2026-11-10/11. Skill: `feat/round8` em `8081a23` (D1–D29). Lista de mudanças congelada antes
> da implementação: [`round8-changes.md`](round8-changes.md) (S1–S8). Origem: o comentário do avaliador
> sobre AP-04 na entrega da rodada 7. **Contaminação declarada:** o autor conhece os três alvos, e o caso
> que motivou a regra veio de um deles. A mudança é uma regra de decisão, não um sinal novo de detecção.

## 1. Como a rodada rodou

- **Ponto de partida:** o código original dos três projetos (`7ef5932`), com a skill da rodada 8 por
  cima. Um worktree e um branch por projeto: `round8/clean-p1..p3`. Tags de execução:
  `run/code-smells-project/iter8`, `run/ecommerce-api-legacy/iter8` e `run/task-manager-api/iter10`.
- **Isolamento (D3):** um subagente novo por projeto, sem nenhum contexto além da invocação da skill.
- **Gate:** cada subagente parou no `[y/n]`. A sessão orquestradora repassou a pergunta ao autor
  literalmente e a resposta dele de volta. Respostas: P1 `y D1 = Business`, P2 `y`, P3 `y, D1=Business`.
  Nenhuma execução usou `--yes`.
- **Interrupções:** os três subagentes pararam por limite de taxa da API (HTTP 429) e foram retomados
  na mesma sessão, com a instrução de conferir primeiro os containers vivos. O P3 parou também no
  reinício da sessão orquestradora. No P2, a retomada achou um container pronto e sem nenhuma
  requisição, removido pelo nome exato.
- **Depois da Fase 3:** o orquestrador explicou ao autor as decisões que os agentes tomaram depois do
  gate (transcripts em `docs/runs/p1-iter8.md`, `p2-iter8.md` e `p3-iter10.md`). O autor aceitou as do P1,
  pediu a opção B para a entrada de valor do P2 (§4.3) e religou o Docker para o P3 fechar a verificação.

## 2. Resultados

| | P1 `code-smells-project` | P2 `ecommerce-api-legacy` | P3 `task-manager-api` |
|---|---|---|---|
| Findings Fase 2 (C/H/M/L) | 34 (12/10/8/4) | 21 (9/5/2/5) | 31 (10/6/10/5) |
| Resposta no gate | `y D1 = Business` | `y` | `y, D1=Business` |
| Replay | 37 PASS, 0 REGRESSION | 8 PASS, 0 REGRESSION, 1 UNVERIFIED | 54 PASS, 0 REGRESSION |
| Entradas de segurança | 18 FIXED | 3 FIXED | 6 FIXED |
| Entrada malformada | 242 ROBUST / 12 operações | 57 ROBUST / 3 operações | 405 ROBUST / 16 operações |
| Valores | 9 HOLDS | 1 HOLDS | 10 HOLDS |
| Resolvidos / propostos / não resolvidos | 25 / 9 / 0 | 15 / 6 / 0 | 22 / 9 / 0 |
| `missed-in-phase-2` | 1 (proposto) | 1 (proposto) | 0 |
| Defeitos introduzidos (achados na re-auditoria) | 0 | 1, corrigido | 0 |
| Processos | 7/7 | 22/22 | 13/13 |
| Comandos (`cd`, encadeamento) | 0 / 0 | 0 / 0 | 0 / 0 |

O UNVERIFIED do P2 é a entrada de segurança do JSON malformado (AP-18): o original já respondia 400,
então o harness não consegue mostrar a correção pelo status. Detalhe por projeto: seção C do
[`README.md`](../../README.md) e `reports/audit-project-{1,2,3}.md`.

## 3. O que a D29 mudou na prática

**Só o P3 tem uma operação que cai no sinal novo:** `PUT /users/<id>` muda nome, e-mail, senha, papel e
estado de qualquer conta escolhida pelo id. O P1 não tem rota de edição de conta, e o P2 só tem checkout
e exclusão, que a D27 já guardava.

| | Rodada 7 | Rodada 8 |
|---|---|---|
| Quem decidiu | O autor, no gate (D2), com uma condição dele | A skill, pela regra (sem pergunta no gate) |
| `role` / `active` | Guardados por credencial de operador | Guardados |
| `password` / `email` | **Propostos** (sem modelo de identidade) | **Guardados** |
| `name` | Aberto | Aberto |
| Reenvio do valor guardado | `PASS` | `PASS` |

No replay do P3:
- anônimo mudando `email`, `password`, `role` ou `active`: 403, quatro entradas `FIXED`;
- anônimo mudando só `name`, e anônimo reenviando os valores guardados: `PASS`;
- operador mudando `role`: `PASS`.

O relatório afirma que a recusa acontece antes de qualquer escrita, mas nenhuma entrada do replay manda
um pedido que misture um campo comum e um privilegiado para confirmar isso.

O caso não voltou ao gate como ambíguo. O único item de classificação do P3 foi `GET /reports/user/<id>`,
que é leitura de domínio, decidida como negócio.

## 4. Defeitos e desvios desta rodada

1. **Linha da re-auditoria com contagem errada (P1 e P2).** Os dois agentes contaram como `unresolved`
   um item `missed-in-phase-2` que eles mesmos tinham registrado em `Proposed, Not Applied`. A D14.1 diz
   que um resto que depende de decisão de produto é `proposed`.
   - **P1:** a linha diz `6 proposed-not-applied, 1 unresolved` e o bloco `Findings resolved` diz
     `0 unresolved`. O mesmo relatório se contradiz. O item é o limite do corpo e do tamanho de `itens`
     (AP-11). Não foi corrigido, para o relatório ficar como o agente o deixou.
   - **P2:** a linha dizia `5 proposed-not-applied, 2 unresolved`. Foi corrigida na retomada (§4.3) para
     `7 proposed-not-applied, 0 unresolved`.
   - **Candidato para a skill:** o template deveria dizer que a linha soma os mesmos itens listados em
     `Proposed, Not Applied`, e que `unresolved` é só `failed`/`introduced` sem proposta.
2. **P1, classificação de contrato revista depois do gate.** O índice único de e-mail e a checagem de
   existência do usuário ao criar pedido foram apresentados no gate como "seriam propostos" e aplicados
   na Fase 3 como seguros (RP-19). O relatório registra a revisão em "Contract classifications revised in
   Phase 3", mas a pessoa que respondeu ao gate não viu essa classificação. O autor aceitou as duas
   depois. **Candidato:** uma revisão de classificação depois do gate deveria voltar à pessoa, ou ser
   proibida.
3. **P2, entrada de valor dependente de ordem.** A entrada do relatório financeiro comparava listas por
   posição. O original monta o relatório com callbacks assíncronos, e a ordem varia. A segunda captura
   do próprio original já dava `VIOLATED`. Comparar ordem não determinística viola a D6.5. Por decisão do
   autor (opção B), a entrada foi trocada por uma que confere só pertencimento a um conjunto, capturada
   contra o original reconstruído com `git archive 62f5e63` e conferida no replay: `HOLDS`.
   - **Limite que sobrou:** o probe não tem comparação por chave, ordenada ou de conjunto, e `matches` só
     aceita string. `revenue` e `paid` por curso ficaram `UNVERIFIED`. **Candidato:** um operador de
     comparação sem ordem (por chave, ou ordenando antes de comparar) no protocolo e nos dois probes.
4. **P1, arredondamento de preço não coberto pelo replay.** Um preço com mais de duas casas passa a ser
   gravado arredondado ao centavo (10.555 → 10.56). O agente declarou `UNVERIFIED`; o autor aceitou.
5. **Interrupções por limite de taxa nos três projetos.** Nenhuma deixou container vivo depois da
   retomada. O container encontrado vivo no P2 não tinha recebido nenhuma requisição.
6. **P3, publicação acidental.** O subagente publicou uma página privada com o relatório, o que a skill
   não pede e o prompt não autorizava. A página foi apagada a pedido do autor.
7. **P3, Docker parado no fim da execução.** A listagem final de containers só rodou depois que o autor
   religou o Docker. Estava vazia, e as remoções anteriores estavam confirmadas uma a uma no log.
8. **P1, `python -c` com `;`.** Três chamadas usaram `;` entre instruções Python, num único processo. Não
   é encadeamento de shell; o próprio agente declarou.

## 5. Critério de saída (de `round8-changes.md`)

| Critério | Estado |
|---|---|
| Nenhuma operação num sinal privilegiado termina `proposed` por falta de identidade | **Atendido.** No P3, e-mail e senha saíram de `proposed` para guardados. P1 e P2 não têm operação no sinal novo. |
| Cada operação de S1 tem entrada anônima `FIXED` e caminho do operador `PASS` | **Atendido** (P3: 4 `FIXED`, operador `PASS`). |
| Edição comum sem credencial continua `PASS` | **Atendido** (`update-user-name` e `update-user-resend-stored`). |
| `0 REGRESSION`, `0 NOT ROBUST`, comandos sem `cd` nem encadeamento | **Atendido** nos três. |
| O caso de privilégio de conta não reaparece como ambíguo | **Atendido.** O gate do P3 teve só D1, uma leitura de domínio. |

## 6. Pendências e candidatos para a próxima rodada

- **Contagem da linha da re-auditoria** (§4.1).
- **Revisão de classificação depois do gate** (§4.2).
- **Comparação de valor sem ordem no probe** (§4.3).
- Herdadas do [`round7-report.md`](round7-report.md) §7 e ainda abertas: verificação independente sobre
  a entrega, scorecards, header de pedido em preflight, leitura de stderr com processo destacado, campo
  `Root cause of:`.
