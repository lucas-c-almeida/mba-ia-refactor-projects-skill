# Rodada 6 (limpa) — a skill final, o gate respondido por pessoa, os três projetos

- **Data:** 2026-10-12 a 2026-10-13
- **Complementa** [`round6-report.md`](round6-report.md): aquele relatório documenta as seis execuções
  em `--yes` e as duas emendas do D27. Esta é a **rodada limpa** que ele recomendou: a skill final, nas
  três codebases, uma vez cada, com o gate da Fase 2 **respondido por pessoa**.
- **Skill:** `a55d997` (D27 com as emendas 1 e 2), commitada sobre o código original em cada worktree.
- **Branches de evidência (remoto):** `round6/clean-p1`, `round6/clean-p2`, `round6/clean-p3`.
- **Tags de partida (D3):** `run/code-smells-project/iter6`, `run/ecommerce-api-legacy/iter6`,
  `run/task-manager-api/iter8`. Cada tag é o commit "skill final sobre o código original".

## Como a rodada foi executada — e o que ela não é

- **Um subagente por projeto, em worktree próprio, contexto zerado.** O subagente roda a Fase 1 e a
  Fase 2, grava o relatório em `reports/` e **para no gate**, devolvendo o relatório à sessão
  orquestradora. A sessão apresentou cada gate ao usuário, **um de cada vez**, e o usuário respondeu
  numa pergunta direta no terminal. A resposta foi repassada ao subagente **citada literalmente**, e
  cada relatório carrega `Confirmation: y (human-reviewed, answer relayed by the orchestrating session
  from the user's direct reply)`.
- **As três respostas foram `y`.** Nenhum finding foi alterado pelo usuário no gate. No projeto 3
  havia uma classificação ambígua exposta ao usuário (`GET /reports/user/<id>`); ele escolheu `y`
  sem ressalva, portanto a rota foi guardada como o subagente havia classificado.
- **Não é a sessão interativa direta do autor.** A sessão orquestradora fica no meio. Dois efeitos:
  (a) as aprovações de permissão do harness **não foram contadas por ninguém**: o agente não as vê e
  a sessão orquestradora também não; (b) a leitura do relatório do gate pelo usuário passou por um
  resumo do orquestrador (com o arquivo completo disponível). Isto é gate humano, mas não é o gate da
  rodada 5, em que o autor respondeu o prompt dentro da própria sessão da skill.
- **Isolamento:** container (docker 28.5.2) nos três. Sufixo `clean-pN` em containers, snapshots e
  arquivos de scratch (consequência da rodada anterior).
- **Regras de comando (D25):** 0 `cd` e 0 encadeamentos nas três execuções, pela contagem de cada
  subagente.
- **Interrupção:** o subagente do projeto 3 foi cortado uma vez por limite de uso da API, no meio da
  Fase 3 (depois de o gate ser respondido), e foi retomado a partir do próprio estado (container
  remanescente conferido pelo rótulo e removido pelo nome, baseline reaproveitado após conferência,
  replay final refeito). Declarado no relatório do projeto.

## Critérios de aceite (`instructions.md`)

| Critério | code-smells-project | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Fase 1 detecta a stack | ✓ Python 3.13 · Flask 3.1.1 · SQLite | ✓ Node 24 · Express 4.22.1 · sqlite3 | ✓ Python 3.13 · Flask 3.0.0 · SQLite |
| Fase 2 encontra ≥ 5 findings | ✓ 30 | ✓ 21 | ✓ 27 |
| Fase 2 tem ≥ 1 CRITICAL/HIGH | ✓ 11 C · 9 H | ✓ 3 C · 9 H | ✓ 7 C · 7 H |
| Fase 3: a aplicação funciona | ✓ 34 PASS, 0 REGRESSION | ✓ 9 PASS, 0 REGRESSION | ✓ 54 PASS, 0 REGRESSION |

3/3 em todos os critérios.

## Resumo por projeto

| | code-smells-project | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Findings (C/H/M/L) | 30 (11/9/7/3) | 21 (3/9/4/5) | 27 (7/7/9/4) |
| Replay | 34 PASS / 0 REG | 9 PASS / 0 REG | 54 PASS / 0 REG |
| Entradas de segurança | 10 FIXED | 4 FIXED | 11 FIXED |
| Resolvidos / propostos / não resolvidos | 24 / 6 / 0 | 16 / 5 / 0 | 22 / 5 / 0 |
| Linha da re-auditoria (D14) | `⚠` parcial (Tier C do AP-14 não consultado) | `○` | `○` |
| Passadas de re-auditoria | 2 | 1 | 2 |
| `missed-in-phase-2` na re-auditoria | 1 (AP-11, proposto) | 0 | 1 (AP-19, corrigido) |
| Containers subidos/derrubados | 8 / 8 | 12 / 12 | 18 / 18 |
| Commit | `435e8c8` | `040c89d` | `f209ec3` |

Nenhum projeto imprimiu `✓ Zero anti-patterns remaining`: correto pela D14, já que todos restaram com
itens `PROPOSED, NOT APPLIED`.

## ⭐ O que a D27 fez — e se convergiu

| Rota | Classificação | Ação |
|---|---|---|
| P1 `POST /admin/reset-db` | privilegiada | **removida**, 404 (baseline 200, `FIXED`) |
| P1 `POST /admin/query` | privilegiada | **removida**, 404 (baseline 200, `FIXED`) |
| P1 `GET /relatorios/vendas` | privilegiada (agregado financeiro) | **guarda**, 403 sem `OPERATOR_TOKEN` |
| P2 `GET /api/admin/financial-report` | privilegiada | **guarda** |
| P2 `DELETE /api/users/:id` | privilegiada (apaga conta, sem identidade) | **guarda** |
| P3 `GET /reports/summary` | privilegiada (rollup por usuário) | **guarda** |
| P3 `GET /reports/user/<id>` | privilegiada (rollup por usuário nomeado) | **guarda** |
| P3 `DELETE /users/<id>` | privilegiada (apaga conta; token emitido nunca verificado) | **guarda** |

Em todas as rotas guardadas: anônimo `403` (baseline `200`, `FIXED`), e a chamada com `X-Operator-Token`,
exercitada no replay com a credencial por `--env`, volta com o status e o shape do baseline (`PASS`).
Sem a variável, as rotas respondem `403` (fechadas por padrão). O checkout, o login, o cadastro, as
listagens e os CRUD de domínio permaneceram **propostos** nos três, sem ambiguidade aberta de
classificação, exceto as duas abaixo.

**Convergência com a rodada 6 anterior (a pergunta que esta rodada existe para responder).** O texto
final do D27 produziu, em três projetos, as mesmas rotas removidas ou guardadas que a melhor execução
anterior de cada um: P1 igual à `p1-iter2`; P2 igual à `p2`; P3 igual à `p3-iter3`, acrescentando
`GET /reports/user/<id>` como guardada (na `p3-iter3` ela havia ficado proposta). **A divergência do
P3 entre execuções não ressurgiu no `DELETE /users/<id>`**, que é o que a emenda 2 corrigiu.

Duas leituras ainda dependem de julgamento, e os subagentes as registraram como incidentes de
classificação, não de processo:

1. **`GET /reports/user/<id>` (P3).** "Atividade por usuário" é privilegiada pelo texto, mas a rota
   também se lê como "o relatório do próprio usuário". O subagente guardou, pelo texto literal; o
   usuário foi consultado e escolheu `y`. A decisão está explícita, mas a skill ainda não diz como
   tratar uma consulta de um registro só cujo conteúdo é um rollup.
2. **`PUT /users/<id>` (P3)**, que aceita `active=false` e `role`: proposta, por "na dúvida, propõe".

## Achados que valem registro

- **Falso positivo parcial atribuível à skill (P2).** O finding de código morto (AP-17) listava
  `audit_logs` "escrita e nunca lida". Uma trilha de auditoria é write-only por natureza. O subagente
  retirou o subitem e o relatório registra a retirada; para o scorecard, conta como falso positivo
  parcial do finding. Candidato para o catálogo: AP-17 precisa excluir tabelas de auditoria e logs.
- **Recall da Fase 2 (P1, P3).** Em cada um houve um `missed-in-phase-2` na re-auditoria. No P1
  (limite de tamanho de corpo e array) o subagente admite que o sinal estava na lista verificada e
  não virou finding. No P3, o aviso LOW do flask 3.0.0 estava só na tabela de cobertura e foi
  corrigido depois.
- **Mudança de valor invisível ao replay (P1).** `GET /produtos/busca?q=%27` agora encontra o
  produto com aspa; o original devolvia `[]` por causa do SQL concatenado. Correto, mas a comparação
  por shape não acusa nem poderia acusar. Idem para a conversão de dinheiro para centavos (P2, P3).
- **Um `REGRESSION` encontrado e corrigido durante a Fase 3 (P3).** O corpo do 400 para JSON
  indecodificável mudou de texto ao desligar o debug; foi corrigido e o replay final voltou a zero.
- **Mudanças de comportamento fora da API (P2).** O cartão negado agora é decidido antes de qualquer
  escrita (não deixa usuário criado), o checkout roda em transação e o erro de auditoria faz rollback.
- **Pacotes.** P1: flask-cors 5→6.0.5 aplicado, coberto pelo replay com `Origin` e `OPTIONS`. P2:
  sqlite3 5→6 **não** aplicado (as notas da versão não descrevem o que muda no motor SQLite).
  P3: flask-cors 4.0.2 aplicado; os avisos que só a 6.0.0 corrige ficaram propostos.

## Incidentes e limitações

- **Aprovações de permissão não contadas** (acima). Não se pode afirmar, desta rodada, que as
  regras D24/D25 reduziram os prompts do harness; só que os comandos foram analisáveis.
- **`proc start` falha na imagem slim** nos dois projetos Python ("could not read the start time"),
  como já havia falhado nas execuções em `--yes` da rodada 6. Os subagentes usaram `docker exec`, um
  launcher fora da árvore ou o container como handle, tudo declarado no `Execution Log`. É
  improvisação do agente repetida em todas as execuções Python desta rodada e o candidato mais forte
  para a próxima mudança da skill.
- **Cópia de execução reaproveitada entre boots (P2).** Fora do "cópia nova por execução" estrito do
  protocolo; declarado.
- **Verificado só à mão:** upgrade de hash de senha no primeiro login (P1 não exercitou no replay),
  campo `senha` mascarado em `/usuarios` (P1), CHECK constraints em banco legado (P3), `JSON malformado`
  sem stack trace (P2, não é contrato).
- **Não verificado:** camada 1 de deprecation sobre as entradas destrutivas e sobre o app refatorado
  em parte dos casos; consulta Tier C (docs oficiais Flask/Python) no P1; a checagem de banco legado do
  P3 foi derrubada pelo host por falta de memória depois de rodar e não foi reiniciada.
- **Segredos no histórico:** os segredos tirados do código continuam no git. Os relatórios dizem para
  rotacionar a chave de pagamento, a senha do banco, a senha SMTP, o `SECRET_KEY` e as senhas do seed.
- **Tokens de teste em `surface.json`:** `OPERATOR_TOKEN` fixo do replay, nos três.

## Candidatos para depois da entrega (a skill, não executados)

1. Caminho documentado para `proc start` em imagem sem start time (cair para `docker exec` com saída
   capturável), em vez da improvisação de cada agente.
2. AP-17: excluir tabelas de auditoria e de log do sinal "escrito e nunca lido".
3. D27: dizer como tratar uma consulta de um registro só cujo conteúdo é um rollup por usuário.
4. Rótulos de container e scratch com identificador de execução (já aplicado como prompt, falta na skill).
5. Upgrade de hash para contas que nunca logam: declarar o resíduo como proposta (RP-08).
6. A Fase 2 deve abrir como finding qualquer advisory que a tabela de cobertura registra.

## Intervenções

- **Orquestrador:** retomar o P3 duas vezes após limite de uso; apresentar três gates ao usuário.
- **Humano:** três respostas ao gate (`y`, `y`, `y`) e uma decisão explícita sobre a rota ambígua do P3.
  Nenhuma durante as Fases 1 e 2 além da leitura do relatório, e nenhuma durante a Fase 3.

## Evidência

Branches no remoto: `round6/clean-p1`, `round6/clean-p2`, `round6/clean-p3`. Cada um tem o commit
"skill final sobre o código original" e o commit da refatoração. Relatórios de auditoria em
`<projeto>/reports/audit-latest.md` (estado final) e `audit-20261012-*.md` (congelado no gate),
junto de `surface.json`, `baseline.json` e o replay.

| Projeto | Branch | Commit da refatoração |
|---|---|---|
| code-smells-project | `round6/clean-p1` | `435e8c8` |
| ecommerce-api-legacy | `round6/clean-p2` | `040c89d` |
| task-manager-api | `round6/clean-p3` | `f209ec3` |

**Estado da entrega.** Este relatório está na `main`; o código refatorado da rodada limpa **não** está
na `main` nem na `feat/round6`. A `feat/round6` ainda guarda o código das execuções em `--yes`. A
escolha de qual versão vai para o `release/delivery` (a limpa, que tem gate humano) é decisão do autor.
