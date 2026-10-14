# Rodada 6 — resultado das skills e insumo da rodada 7

- **Data:** 2026-10-13 · **Código avaliado:** `release/delivery-r6` (`46c39a3`), que traz o código da
  rodada limpa (`round6/clean-p1..p3`) · **Skill:** `a55d997` (D1–D27, sem emendas depois).
- **Para quê serve este documento:** é o insumo da rodada 7. Reúne tudo o que as skills fizeram e
  **tudo o que deu errado**, de três origens, e diz para cada erro o que a skill precisa passar a fazer.
  Meta declarada pelo autor: *a skill deve ser capaz de lidar com todos os erros listados*; a rodada 7
  será a entrega limpa.
- **Fontes:** `reports/audit-project-{1,2,3}.md` (a skill), `docs/rounds/round6-*.md`,
  `docs/verification/delivery-test-report.md` (três verificadores independentes) e a Parte 2 do
  [`gabarito`](../gabarito.md).
- **Limites:** os verificadores testaram por amostragem (~243 requisições no P1, ~140 pares no P3, fluxo
  completo no P2). Não há scorecard item a item da rodada 6. Onde este documento diz "provável lacuna",
  o casamento foi feito por título e arquivo, **não** pela rubrica.

## 1. Resultado numérico

| | P1 `code-smells-project` | P2 `ecommerce-api-legacy` | P3 `task-manager-api` |
|---|---|---|---|
| Findings da Fase 2 (C/H/M/L) | 30 (11/9/7/3) | 21 (3/9/4/5) | 27 (7/7/9/4) |
| Resolvidos / propostos / não resolvidos | 24 / 6 / 0 | 16 / 5 / 0 | 22 / 5 / 0 |
| Replay do harness | 34 PASS, 0 REGRESSION | 9 PASS, 0 REGRESSION | 54 PASS, 0 REGRESSION |
| Entradas de segurança | 10 FIXED | 4 FIXED | 11 FIXED |
| Linha da re-auditoria | `⚠` | `○` | `○` |
| Verificador independente | 0 regressão de uso legítimo | 0 regressão | 0 regressão |
| **Defeitos achados fora do replay** | **4** (2 introduzidos) | **3** (1 introduzido) | **6** |

O replay disse 0 REGRESSION nos três e o verificador independente confirmou a ausência de regressão
**de uso legítimo**. Mas o verificador achou 13 defeitos que o replay não podia ver (seção 3). Dois
deles são regressões reais de borda (X1.8, X1.9), introduzidas pela própria correção.

## 2. O que funcionou (manter)

- **D27 (operação privilegiada).** `POST /admin/reset-db` e `POST /admin/query` do P1 foram removidas
  (404 em todos os métodos; o original executava o reset até em `//admin/reset-db`). Os agregados
  gerenciais e a exclusão de conta dos três projetos ficaram atrás de uma guarda de operador, fechada por
  padrão, sem contorno por caixa, barra final, `HEAD`, `%31`, `Authorization: Bearer` ou token parcial.
  Os verificadores tentaram contornar e não conseguiram.
- **Parametrização de SQL.** Login com injeção deixou de autenticar (200 → 401); aspas em nome,
  descrição e e-mail deixaram de dar 500.
- **Entrada malformada → 4xx.** Em dezenas de rotas, 500 e queda de processo viraram 400.
- **Migração de dados.** No P3, subir a entrega sobre o banco do original preservou 7 usuários, 18
  tarefas e 6 categorias, criou os `CHECK` e migrou o hash legado no login.
- **Honestidade do relatório.** `proposed`/`unresolved`/`introduced`/`missed-in-phase-2`, a linha `⚠`
  da re-auditoria e o `Verification Coverage` declararam quase tudo que os verificadores depois
  confirmaram como limite.

## 3. Erros e o que a skill precisa passar a fazer

Cada linha: o erro, a evidência, a causa (**V** = verificada, **H** = hipótese) e a mudança **genérica**
(sem nome de rota, arquivo ou tabela dos alvos, CLAUDE.md §2). `Gabarito` aponta a Parte 2.

### G1 — Validação de borda aplicada só onde a Fase 2 olhou

- **Erro.** Tipos errados e valores extremos ainda dão 500 em campos que a refatoração tocou:
  `itens` numérico (X1.10), `tags` objeto (X3.5), `active:"maybe"` (X3.6), nome em lista (X3.7), `usr`/`eml`
  não string aceitos (X2.6), aninhamento profundo (X1.11), id inteiro gigante (X3.8).
- **Causa (V).** A regra "tipo errado → 4xx é seguro" (D7/D15, AP-11, RP-11) existe e foi aplicada, mas
  campo a campo, nos campos que a Fase 2 citou. Os verificadores acharam campos vizinhos, com o mesmo
  padrão, sem a checagem. O original dava 500 nos mesmos casos; só o X1.8/X1.9 são novos.
- **Mudança.** Em `04-architecture-guidelines.md` §6 e RP-11: a Fase 3 monta um **inventário
  entrada → destino**: todo valor derivado da requisição (corpo, query, caminho, header) que chega a uma
  operação sensível ao tipo (chamada ao driver, aritmética, método de string/lista, `len`, indexação,
  desserialização) recebe checagem de **tipo e faixa** na borda. O item não depende de a Fase 2 o ter
  citado.
- **Aceite.** Para cada campo lido na borda do alvo refatorado, a matriz (omitido, `null`, string,
  número, booleano, lista, objeto vazio, objeto aninhado) nunca responde 5xx nem derruba o processo.

### G2 — Regressão introduzida por correção (parametrização, validação de tipo sem faixa)

- **Erro.** X1.8: com a query parametrizada, inteiro fora da faixa do driver virou 500 (o original, por
  concatenar, respondia 404/201). X1.9: `1e999` passou de 500 a 201, com `estoque` "inf".
- **Causa (V para X1.8 como sintoma; H para o mecanismo exato).** A correção troca concatenação por
  parâmetro e a validação de tipo aceita "é número", mas ninguém limita faixa nem rejeita não finito. O
  replay não tinha entrada para esses valores.
- **Mudança.** (a) RP-02: ao parametrizar, acrescentar à borda o limite de faixa do tipo de coluna e a
  rejeição de não finito. (b) `06-validation-protocol.md`: o inventário da superfície passa a incluir,
  para cada parâmetro numérico, as entradas **de valor limite** (zero, negativo, máximo de 64 bits,
  máximo + 1, não finito) com `expect` "sem 5xx"; se o original respondia 2xx/4xx e a entrega responde
  5xx, é `REGRESSION`, nunca `FIXED`.
- **Aceite.** Reexecutar a verificação do X1.8/X1.9 e nenhum 5xx onde o original respondia não-5xx.

### G3 — O replay compara forma, não valor

- **Erro.** A busca com aspa passou a achar o produto (correto, mas invisível ao replay); migração para
  centavos, máscara de credencial, upgrade de hash e ordem do relatório foram verificados "à mão" e só
  em prosa nos relatórios (T8).
- **Mudança.** Protocolo: um tipo de entrada `kind: "value"` com asserções sobre caminhos do JSON
  (`equals`, `matches`, `absent`) para o que a transformação mexe em **valor** (dinheiro, ordenação, campo
  mascarado, campo removido). A conferência "à mão" vira entrada executável ou é rotulada `UNVERIFIED`
  no resumo, nunca só prosa.
- **Aceite.** Cada afirmação "verificado à mão" de um relatório tem uma entrada `value` ou aparece como
  `UNVERIFIED` na linha de replay.

### G4 — Lacuna provável de recall e sinal "verificado" que não vira finding

- **Erro.** Itens da Parte 1 **sem finding correspondente** na rodada limpa (provável, por título):
  CORS aberto (P1 #17, P3 #16), `print` como log (P1 #20, P3 #21), schema e seed misturados (P1 #19),
  relatório com várias queries (P1 #23), *callback hell* (P2 #9), banco em memória (P2 #16), `this`/`self`
  (P2 #19), condicionais verbosas (P3 #23). E itens da Parte 2 que só a re-auditoria achou: corpo sem
  limite (X1.6), conjunto fechado sem `CHECK` (X1.7), advisory do framework (X3.2) (T6).
- **Causa (V para T6, H para os demais).** A Fase 2 declara o sinal como "verificado" sem registrar o que
  examinou; o advisory do `flask` foi para a tabela de cobertura e não virou finding.
- **Mudança.** `03-report-template.md`: a Fase 2 emite um **livro de sinais**, uma linha por sinal do
  catálogo com `arquivos examinados` e `ocorrências`; todo sinal com ocorrência vira finding ou aparece
  como "descartado: <motivo>". Regra de coerência: nada que apareça na tabela de cobertura (advisory,
  hit de varredura) pode ficar fora dos findings. A re-auditoria que acha `missed-in-phase-2` conta
  como defeito de recall e entra no scorecard.
- **Aceite.** Sobre os três alvos, recall da Parte 1 ≥ o da rodada 5 (80%/76%/83% estrito) **e** zero
  `missed-in-phase-2` por sinal já presente no catálogo.

### G5 — Defaults e artefatos introduzidos pela refatoração

- **Erro.** `.env.example` com `OPERATOR_TOKEN=change-me` (X2.7). `.env.example` entregue sem nenhum
  carregador de `.env` (os verificadores dos projetos 1 e 3 notaram: o app não lê o arquivo). No P3, a
  dependência que carregaria `.env` foi removida como "não usada". Os `.gitignore` dos projetos 1 e 3
  sumiram na rodada limpa (T2). `python app.py` fora do diretório do projeto cria o banco no CWD (X3.10).
- **Mudança.** Guidelines §6 / RP-01 / RP-17: (a) valor de exemplo de segredo é **vazio ou inválido por
  construção**, e a guarda **rejeita** o placeholder; (b) se a Fase 3 gera `.env.example`, ou liga um
  carregador (dependência nova = proposta), ou o README diz "exporte as variáveis" e o arquivo é rotulado
  como lista de variáveis, não como arquivo carregado; (c) a Fase 3 cria ou preserva `.gitignore` do alvo
  cobrindo `.env`, banco, caches, ambiente virtual e dependências instaladas; (d) caminhos persistidos
  vindos de configuração se resolvem contra a raiz do projeto, não contra o CWD.
- **Aceite.** `git status` limpo depois de provisionar e rodar a entrega; nenhum literal de segredo em
  arquivo de exemplo; `python app.py` de qualquer CWD usa o mesmo banco.

### G6 — Segredos do alvo copiados para os artefatos da skill

- **Erro.** `surface.json` e `baseline.json` embutem as senhas do seed original e o token de fixture
  (T1; confirmado pelo verificador do P3).
- **Mudança.** Protocolo: no momento da captura, todo campo cujo nome casa o padrão de segredo é
  substituído por marcador e reinjetado pelo harness a partir de `--env`; relatório declara as fixtures
  que sobraram.
- **Aceite.** Grep por literais de segredo em `reports/` do alvo retorna só marcadores.

### G7 — Classificação privilegiada/negócio ainda depende de sorte

- **Erro.** `GET` de rollup de um único principal foi guardado numa execução e proposto noutra (T7); a
  edição de conta (`active`/`role`) ficou proposta. As duas emendas da D27 só convergiram o P3 no fim.
- **Mudança.** O gate da Fase 2 passa a listar as **ambiguidades de classificação** (rota, critério
  considerado, as duas decisões possíveis) e a pessoa decide ali; a Fase 3 aplica a decisão e a registra.
  O desempate "ambíguo → propõe" fica como padrão só no modo `--yes`.
- **Aceite.** Duas execuções do mesmo alvo com as mesmas respostas no gate produzem a mesma lista de
  rotas protegidas.

### G8 — Falso positivo e resíduo mal classificado

- **Erro.** AP-17 reportou uma tabela de auditoria como "escrita e nunca lida" (T5, X2.9). O hash legado
  que só migra no login foi `unresolved` numa execução (X3.9), embora exija decisão do operador.
- **Mudança.** Catálogo AP-17: tabela ou coluna de trilha de auditoria/log append-only não é código
  morto; exigir "sem leitor **e** sem propósito declarado". D14.1/RP-08: resíduo que só uma ação de
  operador resolve (reset de senhas, janela de migração) é `proposed`, com o comando ou passo
  operacional descrito, não `unresolved`.
- **Aceite.** Zero falso positivo nos três alvos pela rubrica; resíduos de operador sempre em `proposed`.

### G9 — Ferramenta de ciclo de vida em imagem enxuta e isolamento simultâneo

- **Erro.** `proc start` falha em imagem `slim` ("could not read the start time") nos três projetos; os
  agentes improvisaram com `docker exec` (T3). Rótulo de container e scratch só com timestamp colidiram
  em execuções simultâneas (T4).
- **Mudança.** `06-validation-protocol.md` §ciclo de vida: caminho documentado e coberto pelo teste de
  conformidade para processo sem hora de início (o handle é o container removido pelo nome exato, nunca
  padrão); identificador de execução aleatório em rótulo, scratch e nome de arquivo.
- **Aceite.** `python tests/probe-conformance/run.py` cobre o caminho sem hora de início; duas execuções
  simultâneas não compartilham nome algum.

### G10 — Defeitos pré-existentes que o gate de contrato segurou (aceitos, mas explícitos)

`DELETE` de id inexistente responde 200 (X2.8); e-mails duplicados aceitos (P1 #16); autorização de
negócio (D15). Continuam `proposed` por desenho. A rodada 7 **não** deve tentar fechá-los; deve mantê-los
visíveis. O que muda é o G1: o que for entrada malformada (e não regra de produto) tem que ser 4xx.

## 4. Itens que ninguém testou (carregar para a rodada 7)

Boot com ambiente totalmente vazio e com o `.env.example` literal; concorrência (pedidos simultâneos no
P1, checkouts com o mesmo e-mail no P2); segundo boot sobre banco já migrado e migração que viola
`CHECK` (P3); upgrade de hash legado no P1; 500 interno real no P2; valores do relatório de vendas do P1
contra o original (o reset destrutivo zerou o banco do original antes da comparação).

## 5. Plano para a rodada 7 (entrega limpa)

1. **Congelar a lista de mudanças** em `docs/rounds/round7-changes.md` (G1–G9), antes de editar a skill,
   no padrão das rodadas anteriores, com a contaminação declarada: o autor conhece os três alvos, e a
   Parte 2 do gabarito nasceu das execuções.
2. **Teste do Quarto Projeto obrigatório** em cada mudança (§2). As propostas acima já estão escritas como
   sinal e raciocínio; o texto da skill não pode citar rota, arquivo ou tabela dos alvos.
3. **Alvo reservado.** Os três alvos estão "queimados" para medir generalização. Para a métrica ⭐
   (achados além do gabarito) valer algo, rodar também um **quarto projeto nunca visto** (de outra stack,
   se possível) e reportar o resultado separado.
4. **Execução.** Três projetos, gate humano, na sessão do autor. Depois, **repetir o plano de verificação
   independente** (`docs/verification/delivery-test-plan.md`) com as entradas de valor limite do G2
   acrescentadas ao bloco E.
5. **Scorecards.** Escrever `docs/evals/run-p<N>-iter<K>.md` contra a Parte 1 **e** a Parte 1 + 2,
   reportados separados.
6. **Critério de saída da rodada 7:**
   - zero 5xx em entrada malformada no verificador independente;
   - zero defeito `introduzido` (X1.8, X1.9, X2.7, T2);
   - todos os itens da Parte 2 detectados pela Fase 2 ou, se de origem `V`, tratados;
   - `git status` limpo e sem segredo nos artefatos (G5, G6);
   - nenhuma execução com `--yes` na evidência.
