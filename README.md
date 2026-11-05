# Skill `refactor-arch` — Refatoração Arquitetural Automatizada

Entrega do desafio **Criação de Skills** do MBA FullCycle. O enunciado original está preservado,
sem alterações, em [`instructions.md`](instructions.md) (era o `README.md` do repositório base;
foi renomeado para liberar o `README.md` para esta documentação).

## O que é este repositório

O entregável **é a skill, não o código refatorado**.

`refactor-arch` é uma skill do Claude Code que analisa, audita e refatora *qualquer* codebase em
direção a uma arquitetura em camadas — com MVC como instância concreta — em três fases sequenciais:

```
FASE 1  Análise        →  entender o alvo. Somente leitura.
FASE 2  Auditoria      →  relatório de findings. Escreve só em <alvo>/reports/. Termina num gate bloqueante.
FASE 3  Refatoração    →  reestruturar + validar. Só roda depois do gate.
```

Os três projetos do repositório base são **campo de prova**, não o produto:

| Projeto | Stack | Nível de organização |
|---|---|---|
| `code-smells-project/` | Python / Flask | Monolito desestruturado |
| `ecommerce-api-legacy/` | Node.js / Express | Desestruturado |
| `task-manager-api/` | Python / Flask | Parcialmente organizado (camadas nominais) |

O código refatorado dos três é **subproduto** da execução da skill: serve como evidência de que ela
funciona, e os critérios de aceite exigem sucesso nos **3/3**. Mas a pergunta que este projeto tenta
responder não é "esses três projetos ficaram melhores?", e sim **"esta skill funcionaria num quarto
projeto que eu nunca vi?"**. Praticamente todas as decisões de design descritas na seção B existem
por causa dessa segunda pergunta.

O raciocínio completo por trás de cada decisão — incluindo as alternativas rejeitadas, os custos
aceitos e duas reversões — está em [`docs/decisions.md`](docs/decisions.md). O `CLAUDE.md` é a
especificação viva do projeto.

---

## Estrutura do repositório

```
mba-ia-refactor-projects-skill/
│
├── README.md                              # esta documentação de entrega (A · B · C · D)
├── instructions.md                        # enunciado original, preservado intacto
├── CLAUDE.md                              # especificação viva do projeto (D1–D28)
│
├── .claude/skills/refactor-arch/          # ← A SKILL (fonte única da verdade, D2)
│   ├── SKILL.md                           #   orquestração das 3 fases
│   ├── references/
│   │   ├── 01-project-analysis.md         #   heurísticas de detecção (Fase 1)
│   │   ├── 02-antipattern-catalog.md      #   catálogo de 20 anti-patterns (Fase 2)
│   │   ├── 03-report-template.md          #   formato normativo do relatório (Fase 2)
│   │   ├── 04-architecture-guidelines.md  #   arquitetura alvo e gate de contrato (Fase 3)
│   │   ├── 05-refactoring-playbook.md     #   19 transformações antes/depois (Fase 3)
│   │   └── 06-validation-protocol.md      #   protocolo normativo de validação (Fase 3)
│   └── scripts/
│       ├── probe.py                       #   harness de referência — Python stdlib
│       ├── probe.mjs                      #   harness de referência — Node, zero deps
│       ├── proc.py                        #   ciclo de vida de processos (D20) — Python stdlib
│       └── proc.mjs                       #   ciclo de vida de processos (D20) — Node, zero deps
│
├── docs/                                  # artefatos de processo (nossos, fora do exigido)
│   ├── decisions.md                       #   registro ADR das decisões D1–D28
│   ├── gabarito.md                        #   análise manual (cópia na seção A)
│   ├── rounds/                            #   relatório consolidado de cada rodada
│   ├── runs/                              #   transcript de cada rodada (D3)
│   └── evals/                             #   rubrica e scorecards por rodada (D8)
│
├── tests/probe-conformance/               # teste de conformidade entre os probes (D6.3)
│
├── code-smells-project/                   # Projeto 1 — campo de prova
├── ecommerce-api-legacy/                  # Projeto 2 — campo de prova
├── task-manager-api/                      # Projeto 3 — campo de prova
│
├── reports/                               # saída da Fase 2 de cada projeto
│   ├── audit-project-1.md
│   ├── audit-project-2.md
│   └── audit-project-3.md
```

**O que o enunciado exige** é o bloco de cima somado a `reports/` e à cópia da skill dentro dos três
projetos. **O que é artefato de processo nosso** são `instructions.md`, `CLAUDE.md` e tudo sob
`docs/` — descritos em `CLAUDE.md` §7.1. Eles não substituem nada da estrutura exigida;
existem para que a seção C deste documento seja verificável em vez de afirmada.

Sobre a cópia da skill: a versão canônica vive **uma única vez**, na raiz. A exigência do enunciado
(`.claude/skills/refactor-arch/` dentro de cada um dos três projetos) é cumprida por um passo de
sincronização executado **uma vez, ao final** da calibração (D2.2). Manter uma cópia só durante o
desenvolvimento é uma garantia estrutural: não existe "a versão do projeto 2" para ajustar sob
pressão quando uma rodada vai mal — o que transformaria anti-overfitting de disciplina em acidente.

---

## A) Análise Manual

Revisão manual dos três projetos, feita lendo integralmente o código-fonte de cada um (sem
`node_modules/`, `.venv/` e bancos gerados), **depois** de o catálogo da skill estar congelado e
commitado (D12). A severidade segue a escala do enunciado, aplicada ao **impacto real no contexto**
de cada projeto. Esta análise é o **gabarito** contra o qual a skill é medida (D8). A cópia
original está em [`docs/gabarito.md`](docs/gabarito.md).

Itens marcados **(confirmado)** foram reproduzidos executando uma **cópia** do código fora do
repositório; nenhum arquivo versionado foi alterado.

> **Grau de independência.** A sessão que produziu esta análise não leu o catálogo de
> anti-patterns, os relatórios de auditoria nem os relatórios de rodada. Ela rodou, porém, na raiz
> do repositório, e não na worktree isolada prevista: carregou o `CLAUDE.md`, que cita como
> exemplos genéricos uma chave hardcoded, uma God Class em `AppManager.js` e uma query N+1 em
> pedidos. Esses três achados aparecem abaixo (A.1 #4, A.2 #5, A.1 #11); seriam encontrados de
> qualquer forma, mas a independência não é total. Ver A.5.

> **Granularidade.** Ocorrências do mesmo problema estão agrupadas numa linha (ex.: todas as
> concatenações SQL do projeto 1 são um item). Para medir recall contra os relatórios da skill,
> casar por **categoria + arquivo**, não por contagem de itens.

### A.1 — `code-smells-project/` (Python / Flask)

| # | Severidade | Problema | Arquivo:linhas | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | SQL Injection generalizado: todas as queries são montadas por concatenação de strings com entrada do usuário | `models.py:47-50`, `models.py:57-61`, `models.py:109-111`, `models.py:126-129`, `models.py:279-281`, `models.py:289-297` (e concatenação também em `28`, `68`, `92`, `140`, `148-151`, `155-166`, `174`, `188`, `192`, `220`, `224`) | Em `login_usuario` o e-mail `admin@loja.com' --` autentica como admin sem senha **(confirmado)**. Busca, cadastro de produto/usuário e troca de status aceitam strings arbitrárias no SQL. Os `id` de rota passam pelo conversor `<int:>` e não são exploráveis, mas o padrão é o mesmo em todo o arquivo. |
| 2 | CRITICAL | Endpoint que executa SQL arbitrário enviado pelo cliente, sem autenticação | `app.py:59-78` | `POST /admin/query` com `{"sql": "..."}` lê ou altera qualquer tabela. É um console de banco exposto na rede (`host="0.0.0.0"`). |
| 3 | CRITICAL | Endpoint destrutivo sem autenticação | `app.py:47-57` | `POST /admin/reset-db` apaga todas as tabelas. Qualquer cliente pode zerar a loja. |
| 4 | CRITICAL | Credencial hardcoded e vazada pela API | `app.py:7`, `controllers.py:284-289` | A `SECRET_KEY` está no código-fonte **e** é devolvida no JSON do `/health`, junto com `db_path`, `debug` e `ambiente: producao` **(confirmado)**. Quem conhece a chave forja sessões/cookies assinados. |
| 5 | CRITICAL | Senhas armazenadas em texto puro e devolvidas pela API | `database.py:31`, `database.py:75-83`, `models.py:79-86`, `models.py:95-102`, `models.py:110`, `models.py:127-128` | `GET /usuarios` lista a senha de todos os usuários, inclusive `admin123` do admin **(confirmado)**. O login compara senha em texto puro direto no SQL. |
| 6 | HIGH | Nenhuma autenticação/autorização em rota alguma; o login não emite sessão nem token | `app.py:11-30`, `controllers.py:167-186` | O login só "confirma" credenciais: nenhuma rota exige identidade. Qualquer cliente cria/altera/apaga produtos, vê todos os pedidos e muda status de qualquer pedido. |
| 7 | HIGH | Modo debug ligado e servidor escutando em todas as interfaces | `app.py:8`, `app.py:88` | `debug=True` com `host="0.0.0.0"` expõe o debugger interativo do Werkzeug (execução de código, protegida só por PIN) e tracebacks completos. |
| 8 | HIGH | Criação de pedido sem integridade: quantidade negativa aceita, itens repetidos burlam o estoque e não há transação | `models.py:139-146`, `models.py:154-168`, `controllers.py:195-201` | Dois itens do mesmo produto (5+5 com estoque 8) passam na checagem e deixam o estoque em `-2`; quantidade `-3` gera pedido com total negativo e **aumenta** o estoque **(confirmado)**. Checagem e baixa de estoque em laços separados, sem lock: pedidos concorrentes fazem *overselling*. Exceção no meio do segundo laço deixa escrita parcial na conexão compartilhada, que o próximo `commit` de outra requisição efetiva. |
| 9 | HIGH | Conexão SQLite única, global e mutável, compartilhada entre threads | `database.py:4-10` | `check_same_thread=False` desliga a proteção do driver sem colocar lock no lugar. Requisições concorrentes compartilham cursor/transação: um `commit` de uma requisição efetiva a escrita pendente de outra. |
| 10 | HIGH | Sem separação de camadas: `models.py` é um módulo único com acesso a dados, regra de negócio e formatação de 4 domínios; `app.py` mistura config, roteamento e SQL | `models.py:1-314`, `app.py:1-88` | Regras de negócio (baixa de estoque, faixas de desconto) ficam dentro das funções de acesso a dados; rotas administrativas executam SQL direto em `app.py`. Nada é testável isoladamente, e qualquer mudança toca o arquivo de todos os domínios. |
| 11 | MEDIUM | Queries N+1 na listagem de pedidos | `models.py:177-199`, `models.py:209-231` | Para cada pedido, uma query de itens; para cada item, uma query de produto: 1 + P + I queries. Também repetido em `criar_pedido` (`models.py:139-141` e `154-156` consultam o mesmo produto duas vezes). |
| 12 | MEDIUM | Tratamento de erro duplicado em cada controller e vazando detalhes internos | `controllers.py:10-12`, `21-22`, `60-62`, `95-96`, `108-109`, `125-126`, `133-134`, `143-144`, `164-165`, `185-186`, `218-220`, `226-227`, `234-235`, `254-255`, `261-262`, `291-292`; `app.py:77-78` | Mesmo `try/except Exception` copiado em 16 funções, devolvendo `str(e)` ao cliente (mensagens do SQLite, nomes de coluna). Não existe error handler central. |
| 13 | MEDIUM | Validação de entrada ausente ou inconsistente | `controllers.py:43-54` vs `controllers.py:87-90`; `controllers.py:169-170`; `controllers.py:239-240`; `controllers.py:195-201` | `atualizar_produto` não valida tamanho do nome nem categoria, embora `criar_produto` valide. Não há checagem de tipo (`preco: "abc"` vira `TypeError` → 500). `login` e `atualizar_status_pedido` quebram com 500 quando o corpo não é JSON. Itens de pedido não são validados (`produto_id` ausente → `KeyError`). |
| 14 | MEDIUM | Atualização de status sem verificar existência e sem efeito colateral anunciado | `models.py:275-283`, `controllers.py:245-250` | `PUT /pedidos/999/status` retorna 200 "Status atualizado" para pedido inexistente **(confirmado)**. Cancelar imprime "Devolver estoque" mas o estoque nunca é devolvido. Não há regra de transição (um pedido `entregue` volta para `pendente`). |
| 15 | MEDIUM | Lógica de negócio e efeitos colaterais no controller | `controllers.py:52-54`, `controllers.py:208-210`, `controllers.py:247-250`, `controllers.py:264-274` | Envio de e-mail/SMS/push simulado com `print`, lista de categorias válidas e o `health_check` fazendo SQL direto no controller, fora do model. |
| 16 | MEDIUM | Esquema sem restrições de integridade | `database.py:26-53` | `email` sem `UNIQUE` (cadastros duplicados), sem chaves estrangeiras entre `pedidos`/`itens_pedido`/`produtos`/`usuarios`, colunas sem `NOT NULL`. Deletar produto deixa itens de pedido órfãos. |
| 17 | MEDIUM | CORS liberado para qualquer origem | `app.py:9` | `CORS(app)` sem restrição de origem, numa API sem autenticação e com endpoints administrativos. |
| 18 | MEDIUM | Valores monetários em ponto flutuante | `database.py:19`, `database.py:41`, `database.py:51`, `models.py:146` | `REAL` + soma em `float` acumula erro de arredondamento (o próprio teste gerou `-269.70000000000005`). |
| 19 | LOW | Criação de schema e seed misturados em `get_db()` | `database.py:7-86` | Toda obtenção de conexão carrega a responsabilidade de migração e de dados de exemplo (com senhas reais-parecidas). Sem mecanismo de migração. |
| 20 | LOW | `print` como log, incluindo dados pessoais | `controllers.py:8`, `57`, `106`, `161`, `179`, `182`, `208-210`, `219`; `app.py:56` | Sem níveis nem formato; e-mails de usuários vão para stdout em login e cadastro. |
| 21 | LOW | Magic numbers e listas mágicas | `models.py:256-262`, `controllers.py:47-50`, `controllers.py:52`, `controllers.py:242` | Faixas de desconto (10000/5000/1000, 10%/5%/2%), limites de nome e listas de status/categorias soltos no código. |
| 22 | LOW | Mapeamento linha→dict duplicado | `models.py:12-21`, `models.py:31-40`, `models.py:304-313`; `models.py:79-86` vs `95-102`; `models.py:177-199` vs `209-231` | O mesmo bloco de serialização copiado; `get_pedidos_usuario` e `get_todos_pedidos` são praticamente idênticos. |
| 23 | LOW | Relatório de vendas com 5 queries onde uma agregação basta | `models.py:239-254` | `COUNT`/`SUM` separados por status; um `GROUP BY status` resolve. |
| 24 | LOW | Config hardcoded e imports mortos | `database.py:5`, `app.py:88`, `database.py:2`, `models.py:2` | Caminho do banco e porta fixos no código; `import os` e `import sqlite3` não usados. |
| 25 | LOW | Nomes que sombreiam builtins e coluna ignorada | `controllers.py:56`, `controllers.py:160`; `database.py:22` vs `models.py:65-70` | Variável `id` sombreia o builtin. A coluna `ativo` existe mas a exclusão é física e a listagem não filtra inativos. |

### A.2 — `ecommerce-api-legacy/` (JavaScript / Node.js + Express)

| # | Severidade | Problema | Arquivo:linhas | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | Credenciais de produção hardcoded | `src/utils.js:1-7` | Senha de banco (`senha_super_secreta_prod_123`), chave *live* do gateway de pagamento e usuário SMTP versionados no código. |
| 2 | CRITICAL | Número de cartão e chave do gateway escritos no log | `src/AppManager.js:45` | Cada checkout registra o PAN completo e a chave de pagamento em stdout. Violação direta de PCI-DSS; logs costumam ir para sistemas com acesso amplo. |
| 3 | CRITICAL | "Hash" de senha trivialmente reversível e com colisões massivas | `src/utils.js:17-23`, `src/AppManager.js:68` | O resultado depende só dos 2 primeiros caracteres do base64 da senha, repetidos 5×: `senhaforte`, `senha123` e `se` geram o mesmo valor `c2c2c2c2c2` **(confirmado)**. Sem senha, o usuário é criado com a senha padrão `123456`. |
| 4 | CRITICAL | Endpoints administrativos e destrutivos sem autenticação | `src/AppManager.js:80-129`, `src/AppManager.js:131-137` | `GET /api/admin/financial-report` expõe nomes de alunos e valores pagos a qualquer um; `DELETE /api/users/:id` apaga qualquer usuário sem autorização. |
| 5 | CRITICAL | God Class: `AppManager` concentra conexão, schema, seed, roteamento, regra de negócio e pagamento | `src/AppManager.js:4-139` | Exatamente o caso do enunciado (BD + lógica + roteamento no mesmo arquivo). Impossível testar checkout sem subir Express e SQLite. |
| 6 | HIGH | Checkout associa compra a conta existente só pelo e-mail, sem verificar senha | `src/AppManager.js:40`, `src/AppManager.js:66-75` | Qualquer pessoa matricula (e gera pagamento em nome de) outro usuário informando apenas o e-mail dele. A senha enviada é ignorada quando o usuário já existe. |
| 7 | HIGH | Checkout sem transação: matrícula, pagamento e auditoria em escritas independentes | `src/AppManager.js:50-61` | Se o insert de pagamento falha, a matrícula já foi gravada (curso liberado sem pagamento). Erro do log de auditoria é ignorado (`57-58`). Sem checagem de matrícula duplicada: o mesmo aluno compra o mesmo curso N vezes. |
| 8 | HIGH | Aprovação de pagamento simulada dentro da rota | `src/AppManager.js:46-48` | "Cartão começando com 4 = pago" é regra fake misturada com a rota, sem abstração de gateway que permita trocar por integração real ou testar. |
| 9 | MEDIUM | *Callback hell* em vez de async/await | `src/AppManager.js:37-77`, `src/AppManager.js:83-128` | 5 níveis de aninhamento no checkout; o relatório controla concorrência com contadores manuais. Padrão superado pelo `async/await` desde o Node 8. |
| 10 | MEDIUM | Queries N+1 no relatório financeiro | `src/AppManager.js:89-106` | 1 query de cursos + 1 de matrículas por curso + 2 por matrícula (usuário e pagamento). Um único `JOIN` resolve. |
| 11 | MEDIUM | Erros de banco ignorados; um deles derruba o processo | `src/AppManager.js:92-93`, `104`, `106`, `133-135` | Em `92` o `err` é ignorado e `enrollments.length` sobre `undefined` lança exceção dentro do callback, fora de qualquer handler: o processo Node cai. `DELETE` responde sucesso mesmo com erro ou id inexistente. |
| 12 | MEDIUM | Exclusão de usuário deixa matrículas e pagamentos órfãos; schema sem chaves estrangeiras | `src/AppManager.js:12-16`, `src/AppManager.js:131-137` | A própria resposta admite: "as matrículas e pagamentos ficaram sujos no banco". O relatório passa a listar alunos `Unknown`. `email` também não é `UNIQUE`. |
| 13 | MEDIUM | Estado global mutável e cache sem limite | `src/utils.js:9-15`, `src/utils.js:25`, `src/AppManager.js:59` | `globalCache` cresce uma chave por usuário sem expiração (vazamento de memória) e ninguém o lê. `totalRevenue` é exportado como primitivo (cópia), então nunca poderia ser atualizado por quem importa. |
| 14 | MEDIUM | Validação de entrada ausente | `src/AppManager.js:35` | Senha não é obrigatória, e-mail e cartão não têm formato validado, `c_id` não tem tipo checado. |
| 15 | MEDIUM | Dependências transitivas deprecated trazidas por `sqlite3` | `package.json:11`; `package-lock.json:827-831` (`glob`), `1074-1078` (`inflight`, "leaks memory"), `2113-2117` (`tar`), `1569-1573` (`prebuild-install`) | O próprio lockfile marca como deprecated pacotes que a árvore instala, dois deles com aviso explícito de vulnerabilidades conhecidas. |
| 16 | MEDIUM | Banco em memória: todo dado se perde a cada reinício | `src/AppManager.js:7` | Matrículas e pagamentos desaparecem no restart. Aceitável em demo, inadequado para o fluxo de checkout que a API se propõe a ter. |
| 17 | LOW | Nomes crípticos em variáveis e no contrato da API | `src/AppManager.js:29-33`, `api.http:8-12` | `u`, `e`, `p`, `cid`, `cc` internamente; `usr`, `eml`, `pwd`, `c_id` no corpo da requisição. |
| 18 | LOW | Respostas inconsistentes (texto puro vs JSON) e sem error handler central | `src/AppManager.js:35`, `38`, `41`, `48`, `60`, `135` | Cliente precisa tratar dois formatos; nenhuma middleware de erro registrada em `src/app.js`. |
| 19 | LOW | Mistura de `this` e `self` para o mesmo objeto | `src/AppManager.js:26`, `src/AppManager.js:50-54` | Necessário só por causa de `function` vs arrow no callback; confunde a leitura e é fonte clássica de bug. |
| 20 | LOW | Magic numbers/strings e configuração fixa | `src/AppManager.js:46`, `src/AppManager.js:68`, `src/utils.js:6`, `src/utils.js:19` | Prefixo `"4"`, senha padrão, porta 3000 e 10000 iterações sem constante nomeada nem variável de ambiente. |
| 21 | LOW | Import não usado e log de cache sem propósito | `src/AppManager.js:2` (`totalRevenue`), `src/utils.js:13` | Código morto e ruído no log. |

### A.3 — `task-manager-api/` (Python / Flask + Flask-SQLAlchemy)

| # | Severidade | Problema | Arquivo:linhas | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | Hash de senha exposto em todas as respostas de usuário | `models/user.py:16-25`; usado em `routes/user_routes.py:33`, `85`, `129`, `209` | `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e o login devolvem o campo `password`. Como é MD5 sem salt, `81dc9bdb…` é `1234` por consulta direta **(confirmado)**. |
| 2 | CRITICAL | Sem autenticação real, e qualquer um se cadastra como admin | `routes/user_routes.py:52`, `71-72`, `119-122`, `210` | O "token" é `fake-jwt-token-<id>` (previsível e nunca verificado). `POST /users` aceita `role: "admin"` de um cliente anônimo **(confirmado)**; `PUT` permite promover qualquer conta. Nenhuma rota checa identidade. |
| 3 | CRITICAL | Credenciais hardcoded | `app.py:13`, `services/notification_service.py:7-10` | `SECRET_KEY` e usuário/senha SMTP versionados no código. `python-dotenv` está nas dependências mas não é usado. |
| 4 | HIGH | Senhas com MD5 sem salt e política de senha de 4 caracteres | `models/user.py:27-32`, `routes/user_routes.py:64`, `routes/user_routes.py:115` | MD5 é rápido e sem salt: quebra por tabela pronta. Mínimo de 4 caracteres agrava. |
| 5 | HIGH | Regra de negócio inteira nas rotas; camada de serviço existe mas não é usada | `routes/task_routes.py:85-154`, `routes/task_routes.py:156-223`, `routes/user_routes.py:134-151`, `routes/report_routes.py:12-101` | Validação, cascata de exclusão e cálculo de relatórios vivem nos handlers. `services/` só tem um serviço que ninguém importa. A organização em pastas é nominal, não arquitetural. |
| 6 | HIGH | Modo debug ligado e servidor em todas as interfaces | `app.py:34` | Mesmo risco do debugger Werkzeug exposto na rede. |
| 7 | MEDIUM | Queries N+1 | `routes/task_routes.py:41-57`, `routes/user_routes.py:22`, `routes/report_routes.py:55-56`, `routes/report_routes.py:161-163` | Por tarefa, uma query de usuário e uma de categoria; por usuário, carga *lazy* de `tasks`; por categoria, um `COUNT`. Os relacionamentos já estão mapeados em `models/task.py:20-21` e não são usados. |
| 8 | MEDIUM | Relatórios com dezenas de `COUNT` e agregação em Python sobre a tabela inteira | `routes/report_routes.py:15-51`, `routes/task_routes.py:275-287` | 12+ queries para contar por status/prioridade (um `GROUP BY` basta) e `Task.query.all()` carregado em memória só para contar atrasadas. |
| 9 | MEDIUM | Validação de tipos ausente: entradas inválidas viram 500 | `routes/task_routes.py:113`, `routes/task_routes.py:167-184`, `routes/task_routes.py:261`, `routes/task_routes.py:264`, `routes/report_routes.py:196-202`, `routes/user_routes.py:124-125` | `priority: "2"` → `TypeError` → 500; `/tasks/search?priority=x` → `ValueError` → 500 **(confirmado)**. Corpo JSON `null` em `PUT /categories` quebra. `active` e `color` aceitam qualquer valor. |
| 10 | MEDIUM | Lógica de "atrasada" duplicada em 6 lugares, ignorando o método do model | `models/task.py:50-60` vs `routes/task_routes.py:30-39`, `71-80`, `283-287`; `routes/user_routes.py:171-180`; `routes/report_routes.py:33-37`, `132-135` | `Task.is_overdue()` existe e nunca é chamado. Mudar a regra exige 6 edições consistentes. |
| 11 | MEDIUM | Validação de tarefa duplicada e divergente; helpers prontos não usados | `utils/helpers.py:57-108`, `utils/helpers.py:110-116` vs `routes/task_routes.py:92-144`, `routes/task_routes.py:166-213`; `models/task.py:38-48` | `process_task_data`, `VALID_STATUSES` e `validate_status/priority` existem e as rotas reimplementam tudo. As versões divergem: o helper aceita data `dd/mm/YYYY`, as rotas não. |
| 12 | MEDIUM | APIs deprecated em uso | `routes/task_routes.py:42`, `51`, `67`, `117`, `122`, `158`, `188`, `195`, `227`; `routes/user_routes.py:29`, `94`, `136`, `155`; `routes/report_routes.py:105`, `192`, `213` (`Query.get`) — `models/user.py:14`, `models/task.py:15-16`, `52`, `routes/task_routes.py:31`, `72`, `215`, `285`, `routes/report_routes.py:35`, `42`, `45`, `71`, `133`, e outros (`datetime.utcnow`) | Executando com warnings ligados (Python 3.13, SQLAlchemy 2.0.54): `LegacyAPIWarning` para `Query.get()` → usar `db.session.get(Model, id)`; `DeprecationWarning` para `datetime.utcnow()` → `datetime.now(datetime.UTC)` **(confirmado)**. |
| 13 | MEDIUM | `except:` sem tipo, engolindo qualquer erro sem log | `routes/task_routes.py:62`, `137`, `204`, `236`; `routes/user_routes.py:130`, `149`; `routes/report_routes.py:186`, `207`, `221`; `utils/helpers.py:46`, `49`, `88` | Captura até `KeyboardInterrupt`/`SystemExit` e esconde a causa. Nenhum error handler central. |
| 14 | MEDIUM | Exclusão de categoria deixa tarefas apontando para id inexistente | `routes/report_routes.py:211-223` | SQLite não aplica FK por padrão; as tarefas ficam com `category_id` pendurado. A exclusão de usuário faz cascata manual na rota (`user_routes.py:140-142`), sem consistência entre os dois casos. |
| 15 | MEDIUM | Listagens sem paginação | `routes/task_routes.py:14`, `routes/user_routes.py:12`, `routes/report_routes.py:159` | Retornam a tabela inteira; custo cresce linearmente com os dados. |
| 16 | MEDIUM | CORS liberado para qualquer origem | `app.py:15` | Sem restrição de origem numa API que manipula usuários e papéis. |
| 17 | LOW | Serialização manual duplicada do `to_dict` | `routes/task_routes.py:17-28`, `routes/user_routes.py:162-169` | Reescreve o que `Task.to_dict()` já faz; divergências de formato entre endpoints. |
| 18 | LOW | Código morto: serviço de notificação e helpers nunca usados; dependências não usadas | `services/notification_service.py:1-48`; `utils/helpers.py:9-55`; `requirements.txt:4-6` | `NotificationService`, `sanitize_string`, `generate_id`, `log_action`, `is_valid_color` etc. não são importados. `marshmallow`, `requests` e `python-dotenv` são instalados e não usados. |
| 19 | LOW | Imports não usados | `app.py:7`; `routes/task_routes.py:7`; `routes/user_routes.py:6`; `routes/report_routes.py:7-8`; `utils/helpers.py:3-7`; `models/task.py:3` | Ruído; `hashlib` em rotas sugere lógica de senha fora do model. |
| 20 | LOW | Magic numbers e listas mágicas | `routes/task_routes.py:96-114`; `routes/user_routes.py:64`, `71`; `routes/report_routes.py:24-28`, `84-88`, `129`; `models/task.py:12`, `39` | Faixa de prioridade 1–5, limite 3/200, senha 4, `priority <= 2` = "alta", papéis e status repetidos em vários arquivos, mesmo com constantes definidas em `utils/helpers.py:110-116`. |
| 21 | LOW | `print` como log | `routes/task_routes.py:149`, `153`, `219`, `234`; `routes/user_routes.py:83`, `89`, `147`; `services/notification_service.py:21`, `24` | Sem nível, sem formato, sem destino configurável. |
| 22 | LOW | Config hardcoded e `create_all` na importação | `app.py:11`, `app.py:30-31` | URI do banco fixa; o schema é criado como efeito colateral de importar o módulo (inclusive pelo `seed.py`), sem migrações. |
| 23 | LOW | Condicionais verbosas | `models/user.py:34-38`, `models/task.py:38-60` | `if x: return True else: return False` e ifs aninhados onde uma expressão basta. |

### A.4 — Cobertura mínima exigida pelo enunciado

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | ≥1 C/H | ≥2 M | ≥2 L | ≥5 |
|---|---|---|---|---|---|---|---|---|---|
| code-smells-project | 5 | 5 | 8 | 7 | 25 | ✓ | ✓ | ✓ | ✓ |
| ecommerce-api-legacy | 5 | 3 | 8 | 5 | 21 | ✓ | ✓ | ✓ | ✓ |
| task-manager-api | 3 | 3 | 10 | 7 | 23 | ✓ | ✓ | ✓ | ✓ |

### A.5 — Dúvidas

- **Granularidade dos achados.** Juntei ocorrências do mesmo problema numa linha só (ex.: todas as
  concatenações SQL do projeto 1 são um item). Um relatório que as quebre por função terá mais
  itens sem ter achado nada a mais; para comparação, vale casar por **categoria + arquivo**.
- **A.1 #9 e A.2 #13 (estado global mutável).** O enunciado cita estado global como HIGH. No projeto
  1 mantive HIGH porque a conexão compartilhada tem efeito real entre requisições. No projeto 2
  rebaixei para MEDIUM: o cache só é escrito, nunca lido; o dano é vazamento de memória, não
  comportamento incorreto.
- **A.1 #8 e A.2 #7 (integridade de pedido/checkout).** Classifiquei como HIGH por serem bugs de
  regra de negócio com efeito financeiro. A escala do enunciado é orientada a arquitetura/SOLID e
  não tem um lugar óbvio para "bug de corretude"; dá para defender CRITICAL ("impede o
  funcionamento correto").
- **A.2 #8 (pagamento simulado).** Pode ser intencional num projeto de demonstração. Mantive como
  HIGH pela mistura de regra de pagamento com a rota, não pela simulação em si.
- **A.2 #16 (banco em memória).** Provavelmente escolha de demo (o README do projeto diz que o
  banco é em memória). Deixei como MEDIUM; se a intenção for demo, cai para LOW ou nem é problema.
- **A.3 #4 vs #1.** MD5 isolado seria HIGH; a exposição do hash é que torna o conjunto CRITICAL.
  Mantive separados porque a correção de um não resolve o outro.
- **Versões de dependências com CVE.** Pelo que sei, `requests==2.31.0` e `flask-cors==4.0.0`
  (task-manager-api) têm advisories corrigidos em versões posteriores, e Express 4 já tem sucessor
  (Express 5). **Não listei** porque não verifiquei em fonte viva (sem pesquisa na web nesta
  sessão) e não há evidência no repositório. As deprecações listadas foram todas observadas: pelo
  runtime (A.3 #12) ou declaradas no lockfile (A.2 #15).
- **Seed com senhas fracas** (`database.py:75-79` no projeto 1, `seed.py:19-33` no projeto 3). Não listei à
  parte: são dados de exemplo; o problema real é o armazenamento/exposição, já listado.
- **LIKE sem escapar `%`/`_`** na busca do projeto 3 (`routes/task_routes.py:252-253`). Não é injeção (o
  ORM parametriza), só busca imprecisa. Não listei.

### A.6 — Extensão pós-rodada 6 (Parte 2 do gabarito)

As seções A.1 a A.5 são o gabarito **cego** e continuam sendo o denominador do recall (25 + 21 + 23
itens). Depois da rodada 6, `docs/gabarito.md` ganhou uma **Parte 2** com 31 itens que apareceram depois:
18 achados pela skill na rodada limpa (advisories vivos, listagens sem limite, agregados financeiros
abertos, corpo sem limite, entre outros) e 15 por três verificadores independentes que executaram a
entrega (500 em tipo errado, inteiro fora da faixa e valor não finito, placeholder de token fraco,
entre outros); dois itens contam nas duas origens. Há ainda 9 defeitos da própria skill, fora do
recall. A Parte 2 está **contaminada por
construção** (D12): vários itens existem porque a skill os viu primeiro. Por isso o recall histórico usa
só a Parte 1, e os resultados da skill sobre a Parte 2 estão em
[`docs/rounds/round6-skill-results.md`](docs/rounds/round6-skill-results.md).

---

## B) Construção da Skill

### B.1 — Estrutura dos arquivos e *progressive disclosure*

A skill tem onze arquivos, com uma divisão de papéis deliberada:

| Arquivo | Papel | Quando é lido |
|---|---|---|
| `SKILL.md` | **Orquestra.** Contrato de invocação, sequência das fases, formato exato dos blocos impressos, o gate, as regras invioláveis. | Sempre, inteiro |
| `references/01-project-analysis.md` | Heurísticas de detecção: linguagem, framework, dependências, banco, tipo de aplicação, superfície pública, comando de boot | Início da Fase 1 |
| `references/02-antipattern-catalog.md` | Catálogo de 20 anti-patterns, com sinais observáveis e regras de severidade | Início da Fase 2 |
| `references/03-report-template.md` | Formato normativo do relatório e regras de cada campo | Ao escrever o relatório |
| `references/04-architecture-guidelines.md` | Arquitetura alvo, direção de dependências, teste "camada real ou nominal", gate de contrato público | Ao planejar a Fase 3 |
| `references/05-refactoring-playbook.md` | 19 transformações concretas com código antes/depois | A cada transformação |
| `references/06-validation-protocol.md` | Spec normativa da validação baseline-then-replay | Fase 3a e sempre que a validação degradar |
| `scripts/probe.py`, `scripts/probe.mjs` | Implementações de referência do protocolo | Fase 3a, ou como base para gerar outra |
| `scripts/proc.py`, `scripts/proc.mjs` | Ciclo de vida dos processos: sobe o argv derivado pelo agente, espera a porta, encerra só a árvore registrada (D20) | Sempre que a aplicação original ou refatorada precisa rodar |

**O SKILL.md é um prompt; os arquivos de referência são conhecimento de domínio.** Essa separação
não é estética: o SKILL.md entra inteiro no contexto toda vez que a skill é invocada, enquanto os
arquivos de referência são carregados sob demanda, na fase que precisa deles. Por isso o SKILL.md
tem ~450 linhas e o playbook tem ~1.420: o custo de contexto de cada um é pago em momentos
diferentes. O SKILL.md termina com um mapa explícito de *"leia este arquivo quando…"*, para que o
carregamento seja uma decisão instruída e não um acaso.

A consequência prática é que **nenhuma regra de domínio vive no SKILL.md**. Ele diz *"aplique as
regras de severidade do catálogo"*, não *"God Class é CRITICAL"*. Ajustar a detecção significa
editar um arquivo de referência, nunca o orquestrador — e o orquestrador continua legível como
processo.

**Idioma da skill: inglês integral** (D1), incluindo os rótulos `PHASE 1`, `[CRITICAL]`, `File:`,
`Description:`, `Impact:`, `Recommendation:`. Três razões: (a) os nomes canônicos dos anti-patterns
são em inglês — traduzir *God Class* para *Classe Deus* afasta o leitor da literatura e da busca;
(b) uma skill agnóstica de tecnologia também deveria ser agnóstica do idioma do time que a usa;
(c) o vocabulário do modelo para conceitos de arquitetura é mais preciso em inglês, o que melhora a
detecção. Esta documentação de entrega é em português porque o leitor dela é outro — daí a
divergência deliberada de idioma entre o artefato e o texto que o descreve.

### B.2 — O catálogo: o que entrou e por quê

**20 anti-patterns** (o enunciado exige ≥8), extraídos de literatura — Fowler (*Refactoring*),
Feathers (*Working Effectively with Legacy Code*), os princípios SOLID e o OWASP Top 10 — e não dos
projetos-alvo.

| Severidade default | Ids | Entradas |
|---|---|---|
| **CRITICAL** (4) | AP-01 … AP-04 | Hardcoded Secrets · Injection-Prone Dynamic Query · God Module / God Class · Missing or Bypassable Authorization |
| **HIGH** (5) | AP-05 … AP-09 | Business Logic in the Delivery Layer · Hard-Wired Dependencies / No Composition Root · Mutable Global State · Unsafe Handling of Credentials · Swallowed or Uncentralized Error Handling |
| **HIGH** (2, rodada 2) | AP-18, AP-19 | Insecure Runtime Configuration · Known-Vulnerable Dependency |
| **MEDIUM** (5) | AP-10 … AP-14 | N+1 / Query-Inside-Loop · Missing Boundary Validation · Duplicated Logic · Unbounded Resources and Leaked Handles · Deprecated or End-of-Life API Usage |
| **MEDIUM** (1, rodada 3) | AP-20 | Missing Schema-Level Integrity Constraints |
| **LOW** (3) | AP-15 … AP-17 | Magic Values · Misleading Names and Inconsistent Structure · Dead Code and Commented-Out Code |

**AP-18 e AP-19 entraram depois da rodada 1**, e isso é declarado em vez de escondido: as duas
lacunas apareceram na calibração (configuração de execução insegura e advisories de segurança
classificados de forma improvisada sob outras entradas). Ambas vêm do OWASP Top 10 —
*Security Misconfiguration* e *Vulnerable and Outdated Components* — e deveriam ter estado no
catálogo cego desde o início. A lista de mudanças da rodada 2 foi congelada e commitada antes de
existir o gabarito ([`docs/rounds/round2-changes.md`](docs/rounds/round2-changes.md)).

**AP-20 entrou na rodada 3, já com o autor contaminado pelo gabarito**, e a contaminação está
declarada em [`docs/rounds/round3-changes.md`](docs/rounds/round3-changes.md). A fonte é Karwin
(*SQL Antipatterns*, "Keyless Entry" e "Rounding Errors"): regra que a aplicação confere mas o
banco não garante. A transformação correspondente é RP-19.

A lógica organizadora é a própria escala de severidade do enunciado, lida como uma escala de
**natureza do dano**: segurança e destruição total de separação de responsabilidades no topo;
violações de camada e de SOLID em seguida; padronização, duplicação e performance no meio;
legibilidade embaixo. Os ids são estáveis e servem de chave estrangeira: cada AP aponta para a
transformação RP correspondente no playbook, e cada finding do relatório cita o id. Isso torna
rastreável a cadeia *achado → transformação → diff*, e é o que permite a regra da Fase 3 de que
**todo edit deve ser atribuível a um finding** — mudança que não resolve finding é churn.

**Por que a severidade é impacto-no-contexto e não etiqueta fixa.** Cada entrada define uma
severidade *default* e, explicitamente, as condições de **escalonamento e rebaixamento**. Um
segredo hardcoded num arquivo de exemplo não é o mesmo problema que o mesmo segredo no caminho de
produção; uma API soft-deprecated com substituto *drop-in* não é o mesmo risco que um pacote
deprecated com advisory de segurança aberto. Uma tabela de severidades fixas por categoria produz
relatórios em que o leitor aprende a descontar a severidade mentalmente — e um relatório cuja
severidade precisa ser descontada não está classificando nada. O default existe como ponto de
partida; quando o finding sai dele, o relatório **diz que saiu e por quê**, numa cláusula.

Três regras transversais do catálogo merecem destaque, porque são o que o mantém honesto:

- **Regra de evidência.** Um finding só existe se o agente leu o código que o produz e consegue
  citar `arquivo:início-fim`. Uma categoria que *plausivelmente* se aplica, mas que não foi
  observada, não é um finding. Inventar é pior que deixar passar: destrói a credibilidade do
  relatório inteiro, de uma vez.
- **Regra de sobreposição.** Um mesmo trecho pode casar com várias entradas. Reporta-se aquela cujo
  **impacto domina**, mencionando as demais na descrição, em vez de arquivar quase-duplicatas sobre
  as mesmas linhas.
- **Proibição de expectativa numérica.** O catálogo proíbe escrever que um projeto "deveria ter" N
  findings. O número é o que o código produzir; poucos findings num projeto limpo é um resultado
  correto, não uma falha da auditoria.

O **playbook** espelha o catálogo com **19 transformações** (o enunciado exige ≥8), com exemplos de
código antes/depois em **Python, JavaScript/TypeScript, Go, Ruby e PHP** — deliberadamente, porque
ler a mesma ideia em cinco sintaxes é a prova de que o padrão não é preso a uma stack. Os domínios
dos exemplos (estoque de armazém, reserva de salas, empréstimo de livros, telemetria de sensores,
manutenção de frota) são inventados e neutros: nenhum deles é o domínio de nenhum dos três
projetos-alvo. Cada transformação declara seu **impacto de contrato** (`safe` ou
`contract-changing`), que é o que a Fase 3 consulta para decidir entre aplicar e propor.

### B.3 — Como a agnosticidade foi garantida

Esta é a parte central. "Agnóstica de tecnologia" não é uma propriedade que se obtém escrevendo
"seja agnóstico" no prompt: é o resultado de seis mecanismos concretos, quatro dos quais custaram
alguma coisa.

**1. Ordem de trabalho cega (D12).** A skill inteira — SKILL.md, catálogo, playbook, guidelines,
protocolo — foi escrita **antes de qualquer leitura dos três projetos-alvo**, em sessão que nunca
os abriu. O `CLAUDE.md` e o `docs/decisions.md` foram escritos sob a mesma restrição. Isso não é
cerimônia: é a única forma de o catálogo ser *provavelmente* independente dos alvos em vez de
*alegadamente*. A janela é irrepetível — depois de ler um projeto, não há como desler — e é por isso
que a seção A só foi escrita depois de o catálogo estar congelado.

**2. O Teste do Quarto Projeto.** Critério de aceite interno aplicado a cada linha da skill:
*"isso continuaria correto e útil se o alvo fosse um projeto Ruby/Rails ou Go que eu nunca vi?"*.
Se a resposta fosse não, a linha era generalizada ou removida. É um teste barato e implacável,
porque converte uma qualidade difusa ("está acoplado?") numa pergunta binária por linha.

**3. Detecção por sinal observável, nunca por instância.** A regra de ouro proíbe, dentro da skill,
nome de arquivo, função, rota, tabela ou constante dos projetos-alvo; descrição de um bug concreto;
contagem esperada de findings; e qualquer heurística que só faça sentido numa das codebases. O que
se escreve no lugar é o *sinal* e o *raciocínio*:

| ❌ Acoplado à instância | ✅ Sinal observável |
|---|---|
| "Procure pela chave secreta hardcoded no arquivo de bootstrap" | "Literal string atribuída a identificador cujo nome casa com `(secret\|key\|token\|password\|credential\|api_key\|dsn)`, fora de arquivo de exemplo ou teste" |
| "O gerenciador central é uma God Class" | "Um único módulo concentra ≥3 responsabilidades distintas (persistência, regra de negócio, roteamento/IO, formatação), ou excede ~300 linhas com ≥2 delas" |
| "Corrija a query N+1 do endpoint de pedidos" | "Chamada ao driver de banco dentro de corpo de laço, ou em função chamada dentro de laço" |

O catálogo ainda explicita: onde um sinal precisa de um token concreto, ele é dado como padrão
abrangendo vários ecossistemas, e num ecossistema não listado o agente deve casar o **conceito** —
"a chamada que envia um statement ao driver", "a construção que registra uma rota" — e não o token
literal.

**4. O harness roda no runtime do próprio alvo (D6.2).** A validação da Fase 3 exige código: alguém
precisa emitir as requisições e fazer o diff estrutural. Em que runtime esse código roda, numa skill
que não sabe qual é a stack do alvo? A resposta é um princípio: *se você consegue subir a aplicação,
você tem um runtime no qual consegue escrever um script*. A Fase 1 já detectou a stack antes de o
harness ser necessário — alvo Python usa `probe.py` (só biblioteca padrão), alvo Node usa
`probe.mjs` (zero dependências, `fetch` nativo), e uma stack sem implementação embarcada é resolvida
pelo agente **gerando** uma a partir da spec normativa. A dependência adicional é **zero por
construção**, não por sorte, e o harness tem proibição explícita de instalar qualquer coisa: instalar
altera o conjunto de dependências do alvo, que é ele próprio uma mudança que precisaria ser validada.

**5. Superfície pública em vez de "existe uma porta HTTP" (D11).** A hipótese "o alvo é um serviço
HTTP" estava espalhada pelo desenho inicial. Ela foi substituída por um conceito único:

> **Superfície pública** = o conjunto de pontos de entrada observáveis que o mundo externo usa.

O algoritmo de validação é o mesmo para todos — *enumerar → exercitar → gravar a forma → comparar* —
e só o adaptador muda:

| Tipo de aplicação | Superfície | O que se compara |
|---|---|---|
| Serviço HTTP | rotas (método + path) | status, content-type, shape do corpo |
| CLI | comandos + flags | exit code, shape do stdout |
| Biblioteca | API exportada | assinaturas, shape do retorno |
| Worker / consumidor | mensagens consumidas | mensagens produzidas e efeitos persistidos |

Generalizar assim **reduziu** trabalho em vez de aumentar: eliminou uma hipótese repetida em vários
pontos e a trocou por um conceito com um ponto de extensão. A consequência sobre o alvo
arquitetural está em D11.1 — MVC pressupõe roteamento e apresentação; para uma biblioteca pura não
existe View, e fabricar uma pasta `views/` vazia satisfaz checklist e não ajuda ninguém. As
guidelines definem o alvo como **separação de camadas, com MVC como instância concreta**: havendo
superfície de requisição, MVC literal (o caso dos três projetos, e o que o enunciado cobra); não
havendo, o mapeamento mais próximo (domínio / portas / adaptadores), com o relatório **declarando** a
adaptação e a justificativa.

**6. Consulta viva para conhecimento perecível (D13).** O enunciado exige detecção de APIs
deprecated. Essa exigência colide frontalmente com a agnosticidade, porque todo item útil dessa
categoria é acoplado a um ecossistema **e perece**. A regra fundante da entrada AP-14:

> A skill pode saber **onde perguntar**. Ela não pode saber **a resposta**.
>
> O conhecimento do modelo é gerador de hipótese, nunca evidência. O modelo pode decidir *verificar*
> se algo está deprecated; não pode **reportar** que está.

A distinção operacional é entre fato estável e fato perecível: um endpoint de registry é
infraestrutura e pode ser versionado com segurança, porque diz apenas *para onde mandar a query*;
"o pacote X está deprecated" é perecível e só pode vir de consulta viva, carimbada com a data.
A entrada versiona, portanto, uma **tabela de adaptadores** (OSV.dev — uma API só para npm, PyPI,
Go, crates, Maven, RubyGems e outros; registries de ecossistema; tooling nativo; changelog oficial da
versão em uso) e uma **gradação de evidência** que decide o que pode virar finding:

| Tier | Evidência | Reportável? |
|---|---|---|
| A — observada | warning emitido pelo runtime/compilador numa execução real, com stack trace | Sim, com arquivo e linha |
| B — declarada | metadado de registry/advisory para a versão exata resolvida | Sim, citando fonte + data |
| C — documentada | doc ou changelog oficial da versão em uso | Sim, citando URL + data |
| D — suspeita | conhecimento prévio do modelo | **Não, nunca.** Promove por verificação, ou descarta |

### B.4 — Desafios encontrados e como foram resolvidos

#### Desafio 1 — O harness fixo em Python: overfitting cometido na escolha da ferramenta *(reversão)*

A primeira versão do protocolo de validação fixava o harness em **Python**, com *fallback* para
`curl`. Quando a escolha foi questionada, a resposta honesta foi: **porque dois dos três
projetos-alvo são Flask**.

Duas falhas ficaram expostas. A primeira: não há nada em "auditar uma codebase" que exija Python;
num alvo Go ou Ruby, a escolha vira uma dependência arbitrária que o usuário precisa instalar para
validar um projeto que não tem relação nenhuma com Python. É exatamente o erro que a regra de ouro
proíbe, cometido não no conteúdo do catálogo, mas na **escolha da ferramenta**. O detalhe que torna
o episódio instrutivo é cronológico: o princípio anti-overfitting foi escrito como decisão zero do
projeto e foi violado três decisões depois, pelo próprio autor, sem soar errado na hora.
**Overfitting não se apresenta como uma decisão de acoplar; apresenta-se como a escolha óbvia — e o
que a torna óbvia é a amostra que se tem na cabeça.**

A segunda falha: o "fallback" não era equivalente ao caminho principal. `curl` emite requisições mas
não faz diff estrutural de JSON — isso exigiria `jq`, que é *menos* disponível que Python ou Node. Na
prática, o fallback degradava para paridade de status code: uma verificação muito mais fraca, vendida
com o mesmo nome. Era um **plano C apresentado como plano B**, e o dano não era a fraqueza, era a
fraqueza **não declarada**: a palavra "validado" significaria coisas diferentes conforme o ambiente,
sem que o leitor soubesse qual delas recebeu.

Resolução: o protocolo virou um **documento normativo em Markdown** (`06-validation-protocol.md`), as
implementações viraram traduções finas dele que rodam no runtime do alvo, e o modo mais fraco deixou
de ser fallback para virar **modo piso declarado** — só entra quando não existe nenhum runtime capaz
de processar JSON, e obriga o relatório a carregar, literalmente, o bloco dizendo o que deixou de ser
verificado.

**Lição:** overfitting não mora só no texto do catálogo — mora em toda escolha feita "porque no nosso
caso é assim". E um fallback só pode se chamar fallback se fizer a mesma coisa; se faz menos, é um
resultado diferente com o mesmo rótulo, e precisa de rótulo próprio.

#### Desafio 2 — O apêndice estático de APIs deprecated: conhecimento perecível versionado *(reversão)*

A primeira versão de AP-14 previa um **apêndice datado** de APIs conhecidamente deprecated por
ecossistema, mantido dentro da skill. A proposta foi recusada.

A falha: **conteúdo perecível versionado dentro de uma skill envelhece sem aviso**. Um arquivo de
referência não tem data de validade visível para quem o lê — parece igualmente autoritativo no
primeiro dia e três anos depois. Pior, contamina o resto do catálogo por associação: o leitor (humano
ou agente) não tem como saber que aquela seção específica apodreceu enquanto as outras continuam
válidas. E o apêndice carregaria acoplamento a ecossistemas para dentro exatamente do artefato que a
regra de ouro protege.

Na mesma discussão, a **premissa da camada local também estava errada**. A formulação original —
"observar se o código roda sem warnings de deprecation" — prova muito pouco, porque os runtimes
**escondem** esses warnings por padrão: Python suprime `DeprecationWarning` fora do `__main__`, Node
mantém *pending deprecations* desligadas. "Rodou limpo" com os detectores desligados não é
informação. A camada local passou a **ligar os detectores** antes de concluir qualquer coisa:

```bash
PYTHONWARNINGS=always::DeprecationWarning python -X dev <boot>
node --pending-deprecation --trace-deprecation <boot>
```

Benefício colateral que vale registrar: o warning forçado vem com **stack trace apontando arquivo e
linha** — exatamente o campo `File: <caminho>:<linha>` que o relatório exige. A evidência chega no
formato do entregável.

**Lição, em duas partes.** Primeira: *ausência de sinal não é sinal de ausência* quando o detector
está desligado por padrão — uma verificação que não pode falhar não é uma verificação. Segunda: numa
skill, conhecimento perecível deve ser substituído por **endereço** de conhecimento; versionar a
pergunta é seguro, versionar a resposta não é.

#### Desafio 3 — "Os endpoints continuam respondendo" é uma afirmação vazia

O enunciado pede que a Fase 3 valide que a aplicação continua funcionando. Verificar isso *depois* da
refatoração não prova nada: um endpoint que já devolvia erro 500 antes continua devolvendo 500 depois
e passa como "não quebrei nada".

Resolução (D4): **baseline antes, replay depois** — um *characterization test* no sentido de Feathers.
A skill enumera a superfície estaticamente a partir do código original, sobe a aplicação original,
grava status, content-type e a *forma* das respostas, e só então refatora; depois repete exatamente as
mesmas chamadas contra a aplicação nova e compara. Com a superfície fixada, uma reestruturação
agressiva vira verificável — e uma reestruturação tímida, não verificada, não vira.

Duas consequências finas: compara-se **forma, não valores** (ids, timestamps e ordenação não
determinística produziriam regressão falsa a cada rodada, e *uma validação ruidosa é pior que nenhuma:
custa o mesmo e você para de ler*); e existe um quarto estado, `PRE-EXISTING FAILURE`, para o que já
estava quebrado antes — não é `✓`, porque não funciona, e não é `✗`, porque não foi a refatoração que
quebrou.

#### Desafio 4 — "Zero anti-patterns remaining" versus "não quebrou nada"

O enunciado pede as duas coisas, e elas se tensionam: corrigir tudo inclui correções que mudam o que
o cliente observa.

Resolução (D7): a Fase 3 corrige findings de **todas as severidades**, mas qualquer correção que
alteraria o **contrato público** não é aplicada — é registrada como `PROPOSED, NOT APPLIED`, com
justificativa. Contam como mudança de contrato: renomear ou mover rota, mudar método HTTP, mudar
status de sucesso, mudar o shape do corpo, remover ou renomear campo, tornar obrigatório um parâmetro
antes opcional, apertar validação a ponto de rejeitar requisições antes aceitas. Não contam (e
portanto são aplicadas): parametrizar query, mover segredo para configuração, eliminar N+1, extrair
lógica para camada, renomear identificador interno, centralizar error handling preservando status e
shapes, apagar código morto. **Decidir pelo time o que pode quebrar não é papel de uma ferramenta
automatizada**; tudo que é seguro é corrigido, tudo que é arriscado é proposto com argumento.

Isso resolve o lado de "não quebrou nada", mas deixa a outra metade em aberto: com que direito o
relatório afirma `Zero anti-patterns remaining`? Essa frase não diz "corrigi o que achei" — diz que
**não existe mais nenhum**, uma afirmação universal negativa que só uma nova auditoria completa pode
sustentar. Ter corrigido os 14 achados da Fase 2 não prova a ausência de um 15º que ninguém
procurou. Pior: sob o gate de contrato acima, se um único item ficou em `PROPOSED, NOT APPLIED`,
então restam anti-patterns por construção — e o relatório os lista três linhas abaixo. Imprimir
"zero" ali seria o documento se contradizendo dentro da mesma tela.

Resolução: a **re-auditoria ao final da Fase 3 é passo obrigatório** (3d), e seu resultado sempre
ocupa uma linha no bloco `## Validation` — nunca é omitida, e os findings remanescentes são
separados em `proposed-not-applied` (declinados de propósito, com justificativa) e `unresolved` (a
transformação falhou, ou a refatoração introduziu o problema). São fatos diferentes e o número que
exige ação é o segundo:

```
  ✓ Zero anti-patterns remaining  (re-audit: 0 findings)
  ○ Anti-patterns remaining: 1 proposed-not-applied, 0 unresolved  (re-audit: 1 finding)
  ⚠ Re-audit partial — see Verification Coverage  (3 findings over the checks that ran)
```

A primeira forma exige re-auditoria completa retornando zero — não "zero inesperados". Uma
re-auditoria parcial (sob `--offline`, por exemplo, em que a consulta viva de APIs deprecated não
roda) nunca a produz, porque cobertura reduzida não sustenta afirmação de ausência. Essa é a
afirmação mais forte do relatório e a mais barata de imprimir — exatamente por isso é a que precisa
ser merecida.

A contrapartida é D9: os arquivos originais são **reescritos in-place**, não duplicados. Deixar o
código antigo ao lado do novo — em `legacy/`, ou numa segunda árvore — mantém no repositório uma
segunda implementação do mesmo comportamento, com todos os anti-patterns intactos; a auditoria
seguinte os reencontraria, e com razão. **Código morto é anti-pattern, não backup.** Backup é o que o
git faz, e faz melhor — reforçado pelas tags de rodada (D3).

#### Desafio 5 — Uma cópia da skill em cada projeto versus fonte única da verdade

O enunciado pede a skill dentro dos três projetos. Três cópias vivas durante a calibração seriam três
oportunidades de "só ajustar aqui" quando uma rodada fosse mal — o overfitting entrando pela porta de
manutenção.

Resolução (D2): a skill canônica vive só na raiz, e a skill aceita um **diretório-alvo opcional**,
usando o CWD como padrão (`/refactor-arch code-smells-project`). Isso não foi concessão: um projeto
real é subdiretório de um monorepo com a mesma frequência com que é a raiz de um checkout, e escopar
o alvo explicitamente deixa a skill **mais** genérica — todo path em relatório e validação passa a ser
relativo ao alvo, nunca ao CWD. As cópias exigidas são geradas por um passo de sync ao final.

#### Desafio 6 — O gate obrigatório versus 2–4 iterações por projeto

A pausa da Fase 2 é cobrada em cinco pontos do enunciado, então fica ON por padrão e não pode ser
desligada por default. Mas o próprio enunciado avisa que são normais 2–4 iterações por projeto, e
reconfirmar um relatório já lido é atrito sem valor.

Resolução (D10): existe `--yes`, e o relatório **registra qual modo foi usado** — `human-confirmed: y`,
`human-confirmed: CRITICAL+HIGH only` ou `--yes (auto-approved, not human-reviewed)`. Sem esse
registro, uma rodada auto-aprovada seria indistinguível de uma revisada quando os relatórios fossem
lidos lado a lado depois. A mesma lógica gera D10.1: a terceira opção do gate (`c`, só CRITICAL+HIGH)
é escolha humana e prevalece sobre o escopo default da Fase 3 — mas uma rodada assim **não pode ser
lida como evidência de `Zero anti-patterns remaining`**, e o cabeçalho do relatório tem que declarar o
escopo aplicado.

### B.5 — O princípio emergente: *a skill nunca degrada em silêncio*

> Quando ela verifica menos, ela declara que verificou menos.

Este princípio **não foi desenhado de antemão**. Ele não abriu nenhuma discussão e não foi escrito
como regra antes de ser seguido: foi identificado depois, quando quatro decisões tomadas em momentos
diferentes, sobre problemas diferentes, chegaram à mesma forma de resposta.

| Decisão | Convergência |
|---|---|
| **D4** | `PRE-EXISTING FAILURE` — um estado próprio para o que já estava quebrado, em vez de forçá-lo num binário que não o comporta |
| **D6.4** | Modo piso **declarado** — sem runtime com JSON, a validação cai para paridade de status code e o relatório diz o que deixou de cobrir |
| **D11.1** | Adaptação arquitetural **declarada** — sem View, usa-se o mapeamento mais próximo e explica-se, em vez de fabricar pasta vazia para satisfazer checklist |
| **D13** | Verificação upstream pulada, **declarada** — sem rede, o relatório diz que a consulta não rodou, em vez de deixar a ausência de findings parecer ausência de problemas |

Uma regra que emerge de convergência independente é mais confiável que uma imposta de cima, porque já
chega com quatro casos de uso comprovados. A razão subjacente é a mesma em todos: o leitor de um
relatório calibra confiança pelo histórico. Uma verificação que às vezes significa algo forte e às
vezes algo fraco, sem avisar qual, treina o leitor a não confiar em nenhuma das duas. Daí a
formulação forte, que vale para o projeto inteiro: **uma validação que não pode falhar, ou que falha
pelo motivo errado, é pior que nenhuma validação** — porque a inexistência é honesta e a decoração
não é.

O princípio está escrito no topo do `SKILL.md`, como regra de governo, com seus corolários: nunca
reportar finding que não foi observado; nunca afirmar que um check passou sem tê-lo rodado
(`UNVERIFIED` é resultado legítimo e esperado); nunca afirmar deprecation a partir da memória.

---

## C) Resultados

> **Fonte desta seção: a rodada 7** (2026-11-04/05), com a skill **na versão entregue** (D1–D28, a
> mesma copiada para os três projetos). A rodada 7 responde aos defeitos que a verificação independente
> da rodada 6 achou na entrega (`docs/rounds/round6-skill-results.md`, G1–G10): entrada malformada que
> ainda dava 500, faixa de inteiro e valor não finito introduzidos pela parametrização, segredo gravado
> nos artefatos, verificação "à mão" contada como prova. A resposta é a D28, ver
> [C.8](#c8--rodada-7-verificação-gerada-não-escrita-d28). Relatório da rodada:
> [`round7-report.md`](docs/rounds/round7-report.md). As rodadas anteriores ficam em `docs/rounds/`.
>
> **O gate foi respondido por uma pessoa nos três projetos.** Cada execução rodou num subagente novo,
> sem nenhum contexto além da invocação da skill, a partir do código original (`7ef5932`) com a skill da
> rodada 7. Cada uma parou no prompt `[y/n]`, e a sessão orquestradora repassou a pergunta ao autor
> literalmente e a resposta dele de volta, sem responder por ele. P1 e P2: `y`. P3: `y D1=business
> D2=privileged`, com uma condição que o autor acrescentou (ver C.4). Nenhuma execução usou `--yes`.
>
> **Como cada número foi obtido.**
>
> | Dado | Fonte | Conferência |
> |---|---|---|
> | Findings, severidades, estados da Fase 3 | `reports/audit-project-{1,2,3}.md` (= `<projeto>/reports/audit-latest.md`) | Contagens do `## Summary` batem com os findings listados |
> | Replay, robustez, valores | Bloco `## Validation` de cada relatório, com `baseline.json` e o replay final em `<projeto>/reports/` | Números do próprio agente; **não reclassificados fora da sessão nesta rodada** |
> | Segredos nos artefatos | `grep` nos `reports/` dos três projetos antes do commit | Só referências `{{env:NOME}}` e shapes; nenhuma senha ou token literal |
> | Recall, falsos positivos, achados além do gabarito | Scorecards da rodada 5 em [`docs/evals/`](docs/evals/) | **Não remedidos na rodada 7** (ver C.6) |
> | Verificação independente | [`docs/verification/`](docs/verification/) | **Não repetida na rodada 7**; o último relatório é o da entrega da rodada 6 |

### C.1 — Resumo dos relatórios de auditoria

| Projeto | Stack detectada | Arquivos | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
|---|---|---|---|---|---|---|---|---|
| 1 — `code-smells-project` | Python 3.13 · Flask 3.1.1 · flask-cors 5.0.1 · SQLite | 4 | 12 | 9 | 8 | 4 | **33** | [`reports/audit-project-1.md`](reports/audit-project-1.md) |
| 2 — `ecommerce-api-legacy` | Node.js 24 · Express 4.22.1 · sqlite3 5.1.7 (memória) | 3 | 8 | 5 | 1 | 5 | **19** | [`reports/audit-project-2.md`](reports/audit-project-2.md) |
| 3 — `task-manager-api` | Python 3.13 · Flask 3.0.0 · Flask-SQLAlchemy 3.1.1 · SQLite | 15 | 12 | 8 | 8 | 4 | **32** | [`reports/audit-project-3.md`](reports/audit-project-3.md) |

Modo de cada execução (D10 / D10.1):

| Projeto | `Mode` | `Confirmation` | Escopo aplicado | `Isolation` | `Verification Coverage` (Fase 3) |
|---|---|---|---|---|---|
| 1 | full | `y` (human-confirmed, repassado) | todas as severidades | container (`python:3.13-slim`) | DEGRADED: hash da senha em repouso e e-mail fora do log sem entrada no harness; uma entrada de segurança `UNVERIFIED` (o payload era SQL válido no original) e substituída |
| 2 | full | `y` (human-confirmed) | todas as severidades | container (`node:24.12.0`) | DEGRADED: o original caiu 6 vezes no baseline e foi reiniciado no mesmo container, e não numa cópia nova (desvio do §3.1); máscara do cartão no log e formato da senha sem entrada |
| 3 | full | `y D1=business D2=privileged` (human-confirmed) | todas as severidades | container (`python:3.13-slim`) | Re-auditoria completa; DEGRADED em três efeitos sem entrada (header de rede privada, `PRAGMA foreign_keys`, rehash de MD5 legado), observados à parte e **não** contados como aprovados |

### C.2 — Projeto 1 — `code-smells-project` (Python / Flask)

**Estrutura antes → depois**

```
code-smells-project/                 (antes)
├── app.py              config + registro de rotas + SQL administrativo inline
├── controllers.py      handlers de todas as rotas, 4 domínios
├── models.py           acesso a dados + regras de negócio de 4 domínios
├── database.py         conexão global + schema + seed
├── requirements.txt
└── README.md
```

```
code-smells-project/                 (depois)
├── app.py                composition root (create_app) + entry point
├── requirements.txt      flask 3.1.3, flask-cors 6.0.0
├── .gitignore · README.md
├── config/               settings.py (único leitor do ambiente) · variables.example (lista para exportar)
├── models/               database, erros, pedido, produto, relatorio, senha (scrypt), usuario
├── controllers/          pedido_, produto_, relatorio_, sistema_, usuario_controller · notificador
├── views/                a camada View: rotas por domínio + entrada.py (tipo e faixa de toda entrada)
└── middlewares/          conexao (uma por requisição), operador (guarda), tratamento_de_erros
```

`controllers.py`, `models.py` e `database.py` foram removidos (reescrita in-place, D9).

**Validação (D4 + D28)**

```
  ✓ Application boots without errors
  ✓ Public surface replayed: 39 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 1 UNVERIFIED
    Security entries: 12 FIXED, 0 NOT FIXED
  ✓ Malformed input: 242 ROBUST, 0 NOT ROBUST, 0 REGRESSION over 12 operations
  ✓ Values: 6 HOLDS, 0 VIOLATED, 0 UNVERIFIED
  ○ Findings resolved: 22/33  (10 proposed, 1 unresolved)
  ○ Anti-patterns remaining: 9 proposed-not-applied, 1 unresolved  (re-audit: 10 findings)
    Re-audit passes: 2; fixed after re-audit: 1 (1 of them missed-in-phase-2)
  ✓ Processes: 12 started, 12 stopped through their handles, 0 left running, 0 incidents
    Isolation: container
  ✓ Commands: 0 directory changes, 0 chained commands
```

- **O `UNVERIFIED`** é a entrada `sec-busca-aspas`: o payload `'` por acaso era SQL válido no
  original, então o baseline já se comportava como a busca benigna. O agente a substituiu por
  `sec-busca-aspas-parentese`, capturada contra o original num boot novo (500 → `FIXED`), e não a editou.
- **O `unresolved`** é um AP-16 de nomenclatura (origem `failed`): duas funções de view mantêm nomes em
  inglês entre nomes em português.
- **Dois achados da re-auditoria escaparam da Fase 2** (`missed-in-phase-2`), ambos de AP-11 sobre
  pedidos. A Fase 2 examinou só a criação.
  - Atualizar o status de um pedido inexistente respondia 200 e não fazia nada. Foi corrigido para 404,
    com entrada de segurança capturada antes contra o original.
  - Transições de status livres, e cancelamento que não devolve estoque. Foi proposto, porque muda o
    que um cliente legítimo observa.

**Operações privilegiadas (D27).** `POST /admin/query` e `POST /admin/reset-db` foram **removidas**
(404, `FIXED`). `GET /relatorios/vendas` ficou atrás de `X-Operator-Token`, fechada por padrão
(anônimo 403 `FIXED`; operador `PASS`, e os valores do relatório `HOLD`).

**`PROPOSED, NOT APPLIED` (gate de contrato, D7):** 10.
- **AP-04:** operações de negócio. Não existe modelo de identidade.
- **AP-18 (`/health`):** o segredo foi mascarado. `db_path`, `debug` e `ambiente` fazem parte do shape.
- **AP-01 e AP-08 (resíduo de operador, D28):** o código já não tem senha nenhuma e grava hash.
  - Bancos semeados pelo código antigo ainda têm as contas com senha publicada.
  - Linhas em texto puro de quem nunca loga continuam assim.
  - O relatório descreve o passo operacional, com o SQL.
- **AP-18:** servidor WSGI de produção (dependência nova) e CORS restrito.
- **AP-11:** limite de itens por pedido e grafo de transições de status (`missed-in-phase-2`).
- **AP-20:** dinheiro. O cálculo já usa `Decimal` e centavos; a migração da coluna `REAL` fica proposta.
  Também e-mail único e FKs.
- **AP-13:** paginação.

**Checklist de Validação**

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [x] Linguagem detectada corretamente          (Python; 3.13 do runtime, o alvo não declara versão)
- [x] Framework detectado corretamente          (Flask 3.1.1, do pin exato)
- [x] Domínio da aplicação descrito corretamente (E-commerce: produtos, usuarios, pedidos/itens_pedido, relatório de vendas)
- [x] Número de arquivos analisados condiz com a realidade   (4 arquivos .py)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência (abre com o bloco da Fase 1; livro de sinais)
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados        (33)
- [x] Detecção de APIs deprecated incluída      (camada 1 forçada: nenhum warning; OSV: advisories em flask 3.1.1 e flask-cors 5.0.1)
- [x] Skill pausa e pede confirmação antes da Fase 3 (parou no [y/n]; respondido pelo autor: y)

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC  (models/, views/, controllers/)
- [x] Configuração extraída para módulo de config (config/settings.py + variables.example)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para visualização ou roteamento (views/)
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado               (middlewares/tratamento_de_erros.py)
- [x] Entry point claro                         (app.py, create_app)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente (39 PASS, 0 REGRESSION; 242 ROBUST)
```

### C.3 — Projeto 2 — `ecommerce-api-legacy` (Node.js / Express)

**Estrutura antes → depois**

```
ecommerce-api-legacy/                (antes)
├── src/
│   ├── app.js            entry point
│   ├── AppManager.js     conexão, schema, seed, rotas, regra de checkout e pagamento
│   └── utils.js          config com segredos, cache global, "hash" de senha
├── api.http
├── package.json / package-lock.json
└── README.md
```

```
ecommerce-api-legacy/                (depois)
├── .gitignore · README.md · api.http
├── package.json / package-lock.json  express ^4.22.3; sqlite3 mantido em 5.1.7
└── src/
    ├── app.js                     composition root e entry point
    ├── config/index.js            único leitor do ambiente, validado e congelado
    ├── models/                    database (transações isoladas), schema (UNIQUE, NOT NULL, CHECK, centavos),
    │                              errors, payment, password (scrypt), money, repositórios, financialReport
    ├── controllers/               checkout, report, user
    ├── views/                     routes.js (parse → call → render) · requestParsers.js (tipo e faixa)
    └── middlewares/               requireOperator (guarda), errorHandler, asyncHandler
```

`src/AppManager.js` e `src/utils.js` foram removidos.

**Validação (D4 + D28)**

```
  ✓ Application boots without errors
  ✓ Public surface replayed: 11 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 0 UNVERIFIED
    Security entries: 4 FIXED, 0 NOT FIXED
  ✓ Malformed input: 59 ROBUST, 0 NOT ROBUST, 0 REGRESSION over 3 operations
  ✓ Values: 2 HOLDS, 0 VIOLATED, 0 UNVERIFIED
  ○ Findings resolved: 15/19  (4 proposed, 0 unresolved)
  ○ Anti-patterns remaining: 3 proposed-not-applied, 0 unresolved  (re-audit: 3 findings)
    Re-audit passes: 2; fixed after re-audit: 2 (0 of them missed-in-phase-2)
  ✓ Processes: 12 started, 12 stopped through their handles, 0 left running, 0 incidents
    Isolation: container
  ✓ Commands: 0 directory changes, 0 chained commands
```

- **No original, `card` com tipo errado derrubava o processo.** Foram cinco variantes da matriz mais a
  entrada de segurança. Agora todas respondem 400.
- **A re-auditoria achou dois defeitos que a própria refatoração tinha introduzido** (origem
  `introduced`), e os dois foram corrigidos antes do segundo replay completo:
  - uma transação na conexão compartilhada, em que um rollback podia descartar a escrita de outra
    requisição;
  - uma configuração e um método sem leitor.
- **O upgrade do sqlite3 para 6.0.1 foi tentado e revertido** (D18): o binário pré-compilado exige
  glibc 2.38, que a imagem não tem.

**Operações privilegiadas (D27).** `GET /api/admin/financial-report` e `DELETE /api/users/:id` ficaram
atrás de `X-Operator-Token`, fechadas por padrão: anônimo 403 (`FIXED`); operador `PASS`, e os
valores do relatório financeiro `HOLD`.

**`PROPOSED, NOT APPLIED` (gate de contrato, D7):** 4.
- **AP-04:** o checkout associa compra a qualquer conta existente só pelo e-mail. A senha agora é scrypt
  e poderia ser verificada, mas isso rejeitaria clientes atuais.
- **AP-01 (resíduo de operador):** rotacionar a chave do gateway e a senha do banco que ficaram no
  histórico do git.
- **AP-19:** cadeia de instalação do sqlite3. A saída é o upgrade major, que falhou por glibc.
- **AP-20:** FKs e a regra de exclusão de usuário. `UNIQUE`, `NOT NULL`, `CHECK` e centavos foram
  aplicados.

**Checklist de Validação**

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [x] Linguagem detectada corretamente          (JavaScript, Node.js; o alvo não declara `engines`)
- [x] Framework detectado corretamente          (Express 4.22.1, do lockfile)
- [x] Domínio da aplicação descrito corretamente (venda de cursos: users, courses, enrollments, payments + relatório financeiro)
- [x] Número de arquivos analisados condiz com a realidade   (3 arquivos em src/)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência (abre com o bloco da Fase 1; livro de sinais)
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados        (19)
- [x] Detecção de APIs deprecated incluída      (--pending-deprecation: nenhuma; npm: pacotes deprecated e advisories na cadeia do sqlite3, advisories na do express)
- [x] Skill pausa e pede confirmação antes da Fase 3 (parou no [y/n]; respondido pelo autor: y)

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC  (src/models, src/views, src/controllers)
- [x] Configuração extraída para módulo de config (src/config/index.js; variáveis listadas no README)
- [x] Models criados para abstrair dados        (repositórios por entidade)
- [x] Views/Routes separadas para visualização ou roteamento (src/views)
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado               (src/middlewares/errorHandler.js)
- [x] Entry point claro                         (src/app.js)
- [x] Aplicação inicia sem erros                (com sqlite3 5.x; o upgrade major ficou como proposta)
- [x] Endpoints originais respondem corretamente (11 PASS, 0 REGRESSION; 59 ROBUST)
```

### C.4 — Projeto 3 — `task-manager-api` (Python / Flask)

**Estrutura antes → depois**

```
task-manager-api/                    (antes)
├── app.py              config + app + blueprints + create_all na importação
├── database.py
├── seed.py
├── models/             category, task, user
├── routes/             task_routes, user_routes, report_routes — regra de negócio + persistência
├── services/           notification_service.py — nunca importado, com senha SMTP
├── utils/              helpers.py — quase tudo sem uso
├── requirements.txt
└── README.md
```

```
task-manager-api/                    (depois)
├── app.py                composition root: create_app()
├── database.py           handle do banco, get_by_id (Session.get), commit, foreign keys ligadas no SQLite
├── seed.py               script de operador; senhas de SEED_*_PASSWORD (aleatórias se ausentes)
├── requirements.txt      flask 3.1.3, flask-sqlalchemy 3.1.1, flask-cors 6.0.0, python-dotenv 1.2.2
├── .env.example · .gitignore · README.md
├── config/settings.py    lê o ambiente uma vez
├── models/               category, clock (utc_now), errors, task, user (scrypt + upgrade de MD5 legado)
├── controllers/          category, report, task, user (sem Flask)
├── routes/               a camada View: rotas por domínio, presenters, validation (tipo de toda entrada)
└── middlewares/          error_handler, operator_guard (fechada por padrão)
```

`services/` e `utils/` foram removidos (código morto; um deles guardava a senha SMTP).

**Validação (D4 + D28)**

```
  ✓ Application boots without errors
  ✓ Public surface replayed: 69 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 0 UNVERIFIED
    Security entries: 5 FIXED, 0 NOT FIXED
  ✓ Malformed input: 401 ROBUST, 0 NOT ROBUST, 0 REGRESSION over 16 operations
  ✓ Values: 13 HOLDS, 0 VIOLATED, 0 UNVERIFIED
  ○ Findings resolved: 20/32  (12 proposed, 0 unresolved)
  ○ Anti-patterns remaining: 12 proposed-not-applied, 0 unresolved  (re-audit: 12 findings)
    Re-audit passes: 2; fixed after re-audit: 1 (0 of them missed-in-phase-2)
  ✓ Processes: 20 started, 20 stopped through their handles, 0 left running, 0 incidents
    Isolation: container
  ✓ Commands: 0 directory changes, 0 chained commands
```

- **O baseline do original tinha 105 respostas 500.** O replay final não tem nenhuma.
- **As duas APIs deprecated apareceram como warning forçado, com arquivo e linha:** `datetime.utcnow()` e
  `Query.get()`. As duas foram substituídas, e a re-auditoria com os detectores ligados não emitiu
  nenhum warning.
- **A re-auditoria achou as chaves estrangeiras ainda não exigidas** (origem `failed`). Foram ligadas
  por conexão, e o segundo replay completo saiu limpo.

**As duas decisões de classificação que a Fase 2 levou ao gate (D28).** O relatório listou duas
operações cuja classificação privilegiada/negócio é ambígua, com o critério de cada lado e o efeito de
cada resposta. O autor decidiu:

| Decisão | Operação | Resposta | O que a Fase 3 fez | Replay |
|---|---|---|---|---|
| D1 | `GET /reports/user/<id>` (rollup de um usuário) | **business** | proposta, junto com o modelo de identidade | `PASS` |
| D2 | `PUT /users/<id>` (pode mudar `role` e `active`) | **privileged**, com condição | mudar `role` ou `active` exige `X-Operator-Token`; reenviar o valor guardado não exige | mudar sem credencial: 403 `FIXED` ×2; com credencial `PASS`; reenvio do valor guardado `PASS` e valor `HOLDS` |

A condição foi do autor, e não da skill: exigir credencial em todo `PUT` com `role` no corpo quebraria
quem reenvia o objeto inteiro com o valor que já está lá. Na rodada 6, a mesma operação ficou
proposta numa execução e guardada em outra. Agora a decisão fica registrada no cabeçalho do relatório.

**Também privilegiadas (sem ambiguidade):** `GET /reports/summary` e `DELETE /users/<id>`, atrás de
`X-Operator-Token` (anônimo 403 `FIXED`; operador `PASS`).

**`PROPOSED, NOT APPLIED` (gate de contrato, D7):** 12.
- **AP-04:** não existe modelo de identidade. Isso inclui o relatório por usuário (D1) e a edição
  anônima de senha e perfil de qualquer conta (a parte de D2 que não é `role`/`active`).
- **AP-01 (resíduo de operador, três itens):** a chave de assinatura no histórico, as contas semeadas
  com senha publicada e a senha SMTP do módulo apagado.
- **AP-08 (resíduo de operador):** contas com MD5 legado migram para scrypt no próximo login. Quem nunca
  loga precisa de reset forçado, e o relatório traz o SQL que lista essas contas.
- **AP-18:** servidor WSGI de produção (dependência nova) e CORS restrito. A política já lê
  `CORS_ORIGINS`, com o mesmo default de hoje.
- **AP-11:** regras de produto (formato de cor, limites de tamanho). Tipo e faixa de toda entrada foram
  aplicados.
- **AP-20:** `CHECK` em `status`/`role`, que exige reconstruir a tabela. As FKs foram aplicadas.
- **AP-13:** paginação.

**Um erro da Fase 2, registrado pelo próprio agente.** O finding AP-20 afirmava ter observado uma
tarefa órfã ao apagar uma categoria. Isso nunca foi observado: o ORM zera o `category_id`. A
re-auditoria checou contra o original e corrigiu a afirmação ao lado do finding, deixando o relatório
do gate intacto. Para o scorecard (D8), conta como afirmação não observada, um erro de precisão e não
de recall.

**Camadas existentes: reais ou nominais?** (teste de `04-architecture-guidelines.md` §5). **Nominais**,
como a Fase 1 disse. A refatoração manteve `models/` e `routes/`, criou `controllers/`, `config/` e
`middlewares/`, e removeu `services/` e `utils/` em vez de preenchê-los.

**Checklist de Validação**

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [x] Linguagem detectada corretamente          (Python; 3.13 do runtime, o alvo não declara versão)
- [x] Framework detectado corretamente          (Flask 3.0.0 + Flask-SQLAlchemy 3.1.1)
- [x] Domínio da aplicação descrito corretamente (gestão de tarefas: users, categories, tasks, relatórios)
- [x] Número de arquivos analisados condiz com a realidade   (15 arquivos .py)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência (bloco da Fase 1, livro de sinais, decisões de classificação)
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados        (32)
- [x] Detecção de APIs deprecated incluída      (Tier A, warnings forçados: datetime.utcnow → datetime.now(UTC); Query.get → Session.get)
- [x] Skill pausa e pede confirmação antes da Fase 3 (parou no [y/n] com D1/D2; respondido pelo autor)

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC  (models/, routes/, controllers/)
- [x] Configuração extraída para módulo de config (config/settings.py + .env.example)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para visualização ou roteamento (routes/ + presenters + validation)
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado               (middlewares/error_handler.py)
- [x] Entry point claro                         (app.py, create_app)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente (69 PASS, 0 REGRESSION; 401 ROBUST)
```

### C.5 — Critérios de aceite do enunciado (3/3 obrigatório)

| Critério | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| Fase 1 detecta a stack corretamente | ✓ Python · Flask 3.1.1 · SQLite | ✓ Node · Express 4.22.1 · sqlite3 | ✓ Python · Flask 3.0.0 · SQLAlchemy · SQLite |
| Fase 2 encontra ≥ 5 findings | ✓ 33 | ✓ 19 | ✓ 32 |
| Fase 2 inclui ≥ 1 CRITICAL ou HIGH | ✓ 12 C · 9 H | ✓ 8 C · 5 H | ✓ 12 C · 8 H |
| Fase 3 — aplicação funciona após a refatoração | ✓ 39 PASS, 0 REGRESSION | ✓ 11 PASS, 0 REGRESSION | ✓ 69 PASS, 0 REGRESSION |

**3/3 em todos os critérios**, nas quatro últimas rodadas (4 a 7). O enunciado pede ainda que a Fase 2
reencontre ≥ 5 dos problemas da análise manual do projeto 1. Na rodada 5, a última com casamento
medido, reencontrou **20** com casamento completo, mais 4 parciais, de 25 (C.6).

### C.6 — Métricas de generalização (D8)

> **Estas métricas são da rodada 5 e não foram remedidas nas rodadas 6 e 7.** A Parte 2 do gabarito
> (`docs/gabarito.md`) foi escrita depois da rodada 6 e definiu que, a partir da rodada 7, o recall é
> reportado sobre a Parte 1 e sobre Parte 1 + 2, separados. **Esse casamento não foi feito para a rodada
> 7.** O que existe da rodada 7, sem scorecard, está logo abaixo da tabela.

Scorecards: [`run-p1-iter5`](docs/evals/run-p1-iter5.md), [`run-p2-iter5`](docs/evals/run-p2-iter5.md),
[`run-p3-iter7`](docs/evals/run-p3-iter7.md). Rodada 4, para comparação:
[`run-p1-iter4`](docs/evals/run-p1-iter4.md), [`run-p2-iter4`](docs/evals/run-p2-iter4.md),
[`run-p3-iter6`](docs/evals/run-p3-iter6.md).

| Métrica (rodada 5) | O que responde | P1 | P2 | P3 |
|---|---|---|---|---|
| Recall estrito | Dos problemas que eu sei que existem, quantos ela achou? | 20/25 (80%) | 16/21 (76%) | 19/23 (83%) |
| Recall amplo (✓ + ◐) | Idem, contando os parciais | 24/25 (96%) | 18/21 (86%) | 21/23 (91%) |
| Falsos positivos | Quantos findings apontam para código correto? | 0 | 0 | 0 |
| Findings inventados | Quantos citam arquivo/linha que não existe ou não contém aquilo? | 0 | 0 | 0 |
| **Achados além do gabarito** | Quantos problemas legítimos ela achou que **não** estavam na análise manual? | **3** | **2** (+1 na Fase 3) | **2** |
| Regressões pós-refactor | Quantas entradas divergiram do baseline? | 0 | 0 | 0 |
| Intervenções humanas | Quantas vezes precisei corrigir o rumo? | 0 | 0 | 0 |

**O que a rodada 7 mostra, sem scorecard:**
- **Regressões:** 0 nos três replays, e 0 `NOT ROBUST`/`REGRESSION` em 702 variantes de entrada
  malformada (242 + 59 + 401).
- **Precisão:** uma afirmação não observada no P3, o órfão do AP-20, corrigida pelo próprio agente.
  Pela rubrica, é um finding com descrição falsa.
- **Recall da Fase 2:** 2 `missed-in-phase-2` no P1, os dois em pedidos e no mesmo sinal do catálogo;
  0 no P2 e no P3.
- **Defeitos introduzidos pela refatoração:** 2 no P2, achados pela re-auditoria e corrigidos antes do
  replay final.
- **Contaminação:** o recall da rodada 7 está contaminado por construção, porque a lista de mudanças
  foi escrita depois de ler o gabarito e a verificação independente
  ([`round7-changes.md`](docs/rounds/round7-changes.md)). Um número de recall dela não mediria
  generalização.

### C.7 — Comportamento em stacks diferentes

- **A matriz de robustez não depende da stack.** O agente declara os campos de cada operação. O
  harness gera as variantes (omitido, `null`, tipo trocado, lista, objeto aninhado, zero, negativo,
  int64 no limite e acima dele, `1e999`, fração), e é o mesmo código para Flask e Express. O P2 tem
  menos variantes porque declarou campos em só 3 operações.
- **Isolamento sem regra por stack.** Python rodou em `python:3.13-slim` e Node em `node:24.12.0`
  (glibc, por causa do addon nativo do `sqlite3`). Em container, o handle é o próprio container,
  removido pelo nome exato, e o `proc` lê `/proc` na imagem slim. Isso está coberto pelo teste de
  conformidade, e nenhuma execução repetiu a falha de `proc start` da rodada 6 (T3).
- **O gate de dependência (D18) agiu igual nas duas stacks.**
  - **P1:** `flask-cors` 5 → 6 aplicado, com o replay cobrindo os headers `Access-Control-*`.
  - **P3:** `flask-cors` 4 → 6 aplicado, idem.
  - **P2:** `sqlite3` 5 → 6 tentado e revertido: a aplicação não subiu (glibc 2.38), e o upgrade ficou
    proposto.
- **Deprecation: a evidência depende do caminho exercitado.** No P3, as duas APIs apareceram como
  warning na Fase 2. No P1 e no Node, as rotas exercitadas com os detectores ligados não emitiram nada.
- **Segredos por referência nas três execuções.** `surface.json` usa `{{env:NOME}}` para senha e token
  de operador, e o relatório lista as fixtures pelo nome.
- **O teste "camada real ou nominal" produziu resultados diferentes conforme o ponto de partida.** Os
  dois monolitos ganharam a árvore MVC inteira. O projeto parcialmente organizado manteve `models/` e
  `routes/` e perdeu `services/` e `utils/`, que eram camadas só de nome.
- **Comandos:** a linha `Commands:` ficou em 0 / 0 nas três execuções.

### C.8 — Rodada 7: verificação gerada, não escrita (D28)

**A devolução.** A verificação independente da entrega da rodada 6 rodou a aplicação refatorada com
entradas que o agente não tinha escrito, e achou o que o replay não via (G1–G10 em
[`round6-skill-results.md`](docs/rounds/round6-skill-results.md)):
- tipo errado ainda dava 500 em campos que a refatoração tinha tocado;
- a parametrização do SQL introduziu 500 para inteiro fora da faixa e aceitou `1e999`;
- `surface.json` gravava senhas do seed;
- "verificado à mão" aparecia no relatório como se fosse prova.

**A falha de raciocínio.** O replay só exercitava as entradas que o agente pensou em escrever. Um
defeito que o agente não imagina também não vira entrada, então o replay confirma a imaginação do
agente, e não o comportamento da aplicação.

**A regra (D28):**

| Mudança | O que faz | Estados |
|---|---|---|
| `kind: "robustness"` | O agente declara os campos e tipos de cada operação; o **harness gera** a matriz de entrada malformada e compara só a classe de status | `ROBUST` · `NOT ROBUST` (falhava antes e depois: `unresolved`) · `REGRESSION` |
| `kind: "value"` | Asserções sobre caminhos do JSON (`equals`, `matches`, `absent`, `sameAsBaseline`) para o que a transformação mexe em valor: dinheiro, ordenação, campo mascarado | `HOLDS` · `VIOLATED` · `UNVERIFIED` |
| `{{env:NOME}}` | Segredo por referência; o harness resolve por `--env` e falha com exit 2 se faltar | — |
| Livro de sinais | Uma linha por sinal do catálogo: onde procurou, quantas ocorrências, para qual finding foi ou por que foi descartado | — |
| Decisões de classificação | Privilegiada/negócio ambígua vai ao gate, e a pessoa decide | — |
| Resíduo de operador | O que só uma ação de operador resolve (rotacionar segredo, resetar senha legada) é `proposed`, com o passo descrito | — |

**O que mudou nas execuções:**
- **Robustez e valores:** os três replays têm as linhas `Malformed input` e `Values` e nenhum `NOT
  ROBUST`, `REGRESSION` ou `VIOLATED`.
- **Efeitos sem entrada:** tudo o que o harness não alcança, como log, formato de hash em repouso e
  header que o baseline não enviou, aparece como `UNVERIFIED by the harness` no bloco DEGRADED, e não
  como prova.
- **Classificação no gate:** o P3 levou D1/D2 ao gate em vez de decidir sozinho.

**Limites desta evidência:**
- **O verificador independente não rodou de novo.** Zero 5xx no verificador independente é critério de
  saída da rodada 7 ([`round7-changes.md`](docs/rounds/round7-changes.md)) e continua não demonstrado.
  O que existe é a matriz do próprio harness, que é gerada, mas roda dentro da sessão do agente.
- **Uma mudança de header no P3 que o replay não cobre.** Com o `flask-cors` 6, o preflight de rede
  privada passou a responder `Access-Control-Allow-Private-Network: false` (o original respondia
  `true`). O baseline não enviava o header de pedido, então o replay não viu. O agente observou à parte
  e declarou `UNVERIFIED`. Para um cliente de navegador numa rede privada, é mudança de comportamento.
- **O desvio do P2:** o original caiu seis vezes no baseline e foi reiniciado dentro do mesmo
  container. O protocolo pede uma cópia nova. O banco é em memória e nada foi escrito em disco, então o
  efeito é provavelmente nulo, mas é um desvio, e está declarado.
- **A resposta do gate foi repassada.** Ela veio do autor, mas passou pela sessão orquestradora, e não
  foi digitada no prompt da própria execução.

---

## D) Como Executar

### D.1 — Pré-requisitos

| Requisito | Detalhe |
|---|---|
| **Claude Code** | Instalado e autenticado. É a ferramenta escolhida entre as três aceitas pelo enunciado. |
| **Git** | A skill assume que o alvo está versionado: a reescrita in-place (D9) usa o histórico como rede de segurança. |
| **Runtime do alvo** | Python 3.8+ para alvos Python, Node 18+ para alvos Node. O harness roda no runtime do próprio alvo — **nada é instalado** para validar. |
| **Runtime de container** (opcional, recomendado) | Docker ou equivalente. Com ele, original e refatorada rodam em containers descartáveis (D19). Sem ele, a skill roda no host e o relatório declara `Isolation: reduced (host)`. |
| **Rede** (opcional) | Só para a consulta viva de APIs deprecated (AP-14, camada 2). Sem rede, use `--offline` e leia a ressalva em "Limitações conhecidas". |

A skill **não** requer `jq`, `curl`, nem qualquer dependência adicional no projeto-alvo.

### D.2 — Invocação

Duas formas, equivalentes em resultado.

**A partir da raiz do repositório**, passando o alvo como argumento (é como as rodadas de calibração
foram desenhadas, D2):

```bash
claude
> /refactor-arch code-smells-project
> /refactor-arch ecommerce-api-legacy
> /refactor-arch task-manager-api
```

**De dentro de cada projeto**, após o passo de sync que copia a skill para lá (é a forma que o
enunciado descreve):

```bash
cd code-smells-project
claude "/refactor-arch"
```

Sem argumento, o alvo é o diretório corrente. Com argumento, o alvo é o diretório informado — e
**todo caminho impresso, escrito ou validado passa a ser relativo ao alvo**, nunca ao CWD. Nada fora
do alvo é analisado ou modificado.

**Isolamento entre rodadas (D3).** Cada projeto deve rodar numa **sessão nova**. Rodar os três na
mesma sessão mede a memória do agente, não a qualidade do catálogo — é overfitting em tempo de
execução, e indistinguível de uma skill genuinamente boa a partir do output. Antes de cada rodada,
marque o ponto de retorno:

```bash
git tag run/p2/iter1
claude                                   # sessão NOVA, contexto zerado
> /refactor-arch ecommerce-api-legacy
# ajustou a skill? volte ao ponto e rode de novo:
git reset --hard run/p2/iter1
```

### D.3 — Flags

| Flag | Efeito | O que fica registrado no relatório |
|---|---|---|
| `--yes` | Pula a confirmação da Fase 2 e vai direto para a Fase 3. | `Confirmation: --yes (auto-approved, not human-reviewed)` |
| `--offline` | Pula as consultas upstream (camada 2 de AP-14). | Bloco de verificação degradada nomeando o que não foi checado |

```bash
> /refactor-arch task-manager-api --yes --offline
```

**Quando usar `--yes`:** apenas durante iteração de calibração, quando o relatório daquela rodada já
foi lido. Nunca numa rodada que será apresentada como evidência de revisão humana — e é justamente
por isso que o modo fica carimbado no cabeçalho do relatório.

**Quando usar `--offline`:** quando não há rede, ou quando a política do ambiente proíbe chamadas
externas. A camada 1 (warnings de deprecation forçados no runtime + metadados do manifesto/lockfile)
continua rodando; a camada 2 (OSV.dev, registries, docs oficiais) não. Um item que só poderia ser
confirmado por consulta viva vira `UNVERIFIED` — **nunca** vira finding por memória do modelo.

### D.4 — O gate da Fase 2

A Fase 2 escreve o relatório em `<alvo>/reports/audit-<YYYYMMDD-HHMM>.md`, copia para
`audit-latest.md`, imprime na tela e **para**:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
  y = apply all findings (contract-changing items will be proposed, not applied)
  n = stop here; the report is saved and nothing else was touched
  c = apply CRITICAL and HIGH only
>
```

Até a resposta chegar, **nenhum arquivo fora de `<alvo>/reports/` é criado, alterado ou removido** —
`reports/` é saída de auditoria, não código-fonte. Para a entrega, o `audit-latest.md` de cada projeto
é copiado para `reports/audit-project-N.md` na raiz.

### D.5 — Como validar que a refatoração funcionou

A skill não pede que você acredite nela: ela produz evidência comparável.

**O protocolo (D4, `06-validation-protocol.md`):**

```
enumerar superfície  →  capturar baseline  →  REFATORAR  →  replay  →  comparar
     (Fase 1)              (Fase 3a)                        (Fase 3c)
```

1. A superfície pública é enumerada **estaticamente, a partir do código original**, e gravada em
   `<alvo>/reports/surface.json`.
2. **Antes do primeiro edit**, o agente sobe a aplicação original e o harness a exercita, gravando
   status, content-type e a *forma* de cada resposta. Capturar depois do primeiro edit tornaria a
   comparação tautológica — e a skill declara `UNVERIFIED` em vez de fingir.
3. A refatoração acontece.
4. O agente sobe a aplicação nova **na mesma base URL** e o harness repete exatamente as mesmas
   chamadas, na mesma ordem, a partir do mesmo arquivo de inventário.

O harness nunca sobe a aplicação: subir é específico de stack (`flask run`, `npm start`, `go run`),
sondar é protocolo puro. Para reproduzir a validação por fora da skill:

```bash
# alvo Python
python .claude/skills/refactor-arch/scripts/probe.py capture \
  --surface reports/surface.json --base-url http://127.0.0.1:8081 --out reports/baseline.json

python .claude/skills/refactor-arch/scripts/probe.py compare \
  --surface reports/surface.json --baseline reports/baseline.json --base-url http://127.0.0.1:8081

# alvo Node — mesma CLI, saída byte-compatível
node .claude/skills/refactor-arch/scripts/probe.mjs compare \
  --surface reports/surface.json --baseline reports/baseline.json --base-url http://127.0.0.1:8081
```

Exit code `0` = nenhuma regressão · `1` = pelo menos uma · `2` = erro de uso ou de I/O. Um exit
diferente de zero **não é problema do harness: é o resultado.**

**Os quatro estados, e o que cada um significa:**

| Estado | Condição | Como ler |
|---|---|---|
| `PASS` | status, content-type e shape iguais ao baseline | A entrada se comporta como antes. É o que a refatoração promete. |
| `REGRESSION` | algum dos três difere, e o baseline não era ele próprio uma falha | **Você quebrou isto.** Corrija e repita o replay, ou reporte abertamente. |
| `PRE-EXISTING FAILURE` | o baseline já era falha (status ≥ 500 ou erro de transporte) e o replay falha do mesmo jeito | Já estava quebrado, continua quebrado. A refatoração não é responsável — e também não conserta. Nunca conte como `✓`. |
| `UNVERIFIED` | a entrada foi pulada, já era `UNVERIFIED` no baseline, ou não pôde ser exercitada agora | **Não é um pass.** Aparece no bloco de verificação degradada, com o motivo. |

**Entradas geradas e asserções de valor (D28).** Além das entradas de contrato e de segurança, o
inventário tem dois tipos que fecham o que a comparação de forma não vê:

| Tipo | Estados | Como ler |
|---|---|---|
| `kind: "robustness"` | `ROBUST` · `NOT ROBUST` · `REGRESSION` | O harness gera a matriz de entrada malformada a partir dos campos declarados e compara só a classe de status. `NOT ROBUST` (falhava antes e continua falhando) é finding `unresolved`. |
| `kind: "value"` | `HOLDS` · `VIOLATED` · `UNVERIFIED` | Asserções sobre caminhos do JSON (`equals`, `matches`, `absent`, `sameAsBaseline`) para dinheiro, ordenação, campo mascarado. |

Segredos ficam fora dos artefatos: o inventário escreve `{{env:NOME}}`, e o valor entra na hora do
envio, por `--env NOME=valor` (repetível). Se uma referência ficar sem valor, o harness sai com exit 2.

Uma entrada que **melhora** — baseline com erro de servidor, replay bem-sucedido — é reportada como
`PASS (improved from <status>)`: geralmente é o efeito pretendido de uma correção, mas continua sendo
uma mudança de comportamento, então é nomeada em vez de escondida.

**Compara-se forma, não valores.** Status/exit code, media type e o conjunto recursivo de chaves com o
tipo de cada folha. Ids gerados, timestamps, durações, hashes e ordenação não garantida ficam de fora
de propósito: comparar valores produziria regressão falsa a cada rodada, e em dois dias todo mundo
aprende a ignorar o resultado da validação.

**O que ler no relatório final,** em ordem de importância:

1. `## Verification Coverage` — `Full`, ou o bloco `DEGRADED` dizendo o que **não** foi verificado.
   Leia isto **antes** dos ✓.
2. A linha de replay: `<P> PASS, <R> REGRESSION, <F> PRE-EXISTING FAILURE, <U> UNVERIFIED`, e as
   linhas `Malformed input` e `Values`.
3. `## Proposed, Not Applied` — o que a skill se recusou a mudar por ser contrato público, com o
   argumento.
4. O cabeçalho: `Mode`, `Confirmation` e escopo aplicado — é o que distingue uma rodada completa e
   revisada de uma parcial e auto-aprovada.

---

## Limitações conhecidas

Esta seção não é uma fraqueza da entrega: é o princípio de B.5 aplicado à documentação do próprio
projeto. O que segue é o que **não** está provado.

**1. Três dos quatro adaptadores de superfície nunca foram exercitados.** A skill suporta quatro
tipos de superfície pública — serviço HTTP, CLI, biblioteca e worker de fila (D11). **Os três projetos
avaliados são serviços HTTP.** Os adaptadores de CLI, biblioteca e worker — incluindo a redução
estrutural de stdout não-JSON (§6.1 do protocolo) e a captura de efeitos persistidos de um worker
(§6.2) — são generalização sem prova. Eles tornam o desenho coerente; não são evidência de que
funcionam.

**2. Uma rodada com a opção `CRITICAL+HIGH only` não é evidência de `Zero anti-patterns remaining`**
(D10.1). A escolha humana no gate prevalece sobre o escopo default da Fase 3, mas o resultado é uma
refatoração parcial por definição. O cabeçalho do relatório declara o escopo aplicado exatamente para
que uma rodada dessas não seja lida como completa no scorecard.

**3. Sob `--offline`, a consulta viva de APIs deprecated não roda** e a cobertura de AP-14 fica
reduzida à camada 1 (warnings forçados no runtime + metadados locais). Pacotes deprecated, yanked ou
com advisory aberto podem existir e **não terão sido checados**. O relatório declara isso; declarar
não elimina a lacuna.

**4. O modo piso entrega menos, e isso não é resolvido por declará-lo** (D6.4). Sem nenhum runtime
capaz de processar JSON, a validação cai para paridade de status code: um handler que devolve `200`
com um objeto vazio onde antes devolvia um objeto populado **passa**. O rótulo torna o resultado
honesto, não equivalente.

**5. Para stacks sem harness embarcado, a implementação é gerada em tempo de execução** (D6.3) — ou
seja, **código não revisado participa da validação**. É um risco assumido conscientemente, em troca de
não acoplar a skill a um conjunto fechado de ecossistemas. A contrapartida: existem hoje N
implementações do mesmo protocolo e elas podem divergir entre si ou da spec. O documento normativo é a
autoridade; as implementações precisam ser revisadas contra ele, e `probe.py`/`probe.mjs` só foram
verificados um contra o outro quanto à compatibilidade de saída.

**6. A comparação de shape ignora comprimento e ordem de arrays de propósito** (D6.5). Uma regressão
que se manifeste apenas como "a coleção voltou vazia" ou "a ordenação mudou" **não é detectada**. Foi
uma escolha explícita contra ruído — uma validação ruidosa é ignorada em dois dias — mas é uma
lacuna real, e quem depende de ordenação precisa asseverá-la numa entrada dedicada do inventário.

**7. O baseline pressupõe estado de datastore comparável entre as duas execuções.** A comparação de
forma absorve a maior parte da variação de dados, mas uma coleção vazia numa execução e populada na
outra muda o descritor do array. Use o mesmo estado nas duas, ou declare a diferença.

**8. A evidência da seção C é medida pelo próprio autor.** O gate da Fase 2 foi respondido por uma
pessoa nas três execuções (rodadas 5, 6 e 7), mas essa pessoa é o autor da skill, e nas rodadas 6 e 7 a
resposta foi repassada por uma sessão orquestradora a subagentes. O recall e os achados além do
gabarito (C.6, da rodada 5) comparam a skill com a análise manual do mesmo autor, e o casamento ✓/◐/✗
é julgamento. Por isso cada linha está exposta nos scorecards da rodada 5 em `docs/evals/`, para ser
contestada, em vez de resumida num número só. **Não há scorecards das rodadas 6 e 7.**

**9. A matriz de robustez é gerada, mas não é um verificador independente.** As variantes de entrada
malformada (D28) saem do harness, e não da imaginação do agente. Mas os campos de cada operação são
declarados pelo agente, e um campo que ele não declara não entra na matriz. A verificação independente
da rodada 6 (`docs/verification/`) achou defeitos que o replay não via; ela **não foi repetida** sobre a
entrega da rodada 7.

---

## Referências deste repositório

| Documento | O que é |
|---|---|
| [`instructions.md`](instructions.md) | O enunciado original do desafio, **preservado sem alterações** (era o `README.md` do repositório base). É a fonte da verdade sobre o que foi pedido. |
| [`docs/decisions.md`](docs/decisions.md) | Registro ADR completo de D1–D28: contexto, alternativas rejeitadas, custos aceitos e as duas reversões (D6 e D13), com o caminho que levou a cada forma final. |
| [`CLAUDE.md`](CLAUDE.md) | Especificação viva do projeto: requisitos extraídos do enunciado, escala de severidade canônica, contratos de saída das fases e o resumo das decisões. |
| [`.claude/skills/refactor-arch/`](.claude/skills/refactor-arch/) | A skill em si — o entregável. |
