# Gabarito — Análise Manual dos Projetos

Revisão manual dos três projetos-alvo, feita lendo integralmente o código-fonte de cada um
(sem `node_modules/`, `.venv/` e bancos gerados). Severidade conforme a escala do enunciado,
aplicada ao **impacto real no contexto** de cada projeto.

Itens marcados com **(confirmado)** foram reproduzidos executando uma **cópia** do código no
diretório temporário da sessão; nenhum arquivo versionado foi alterado.

---

## code-smells-project (Python / Flask)

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

---

## ecommerce-api-legacy (JavaScript / Node.js + Express)

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

---

## task-manager-api (Python / Flask + Flask-SQLAlchemy)

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

---

## Cobertura mínima

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | ≥1 C/H | ≥2 M | ≥2 L | ≥5 |
|---|---|---|---|---|---|---|---|---|---|
| code-smells-project | 5 | 5 | 8 | 7 | 25 | ✓ | ✓ | ✓ | ✓ |
| ecommerce-api-legacy | 5 | 3 | 8 | 5 | 21 | ✓ | ✓ | ✓ | ✓ |
| task-manager-api | 3 | 3 | 10 | 7 | 23 | ✓ | ✓ | ✓ | ✓ |

---

## Dúvidas

- **Granularidade dos achados.** Juntei ocorrências do mesmo problema numa linha só (ex.: todas as
  concatenações SQL do projeto 1 são um item). Um relatório que as quebre por função terá mais
  itens sem ter achado nada a mais; para comparação, vale casar por **categoria + arquivo**.
- **P1 #9 e P2 #13 (estado global mutável).** O enunciado cita estado global como HIGH. No projeto
  1 mantive HIGH porque a conexão compartilhada tem efeito real entre requisições. No projeto 2
  rebaixei para MEDIUM: o cache só é escrito, nunca lido; o dano é vazamento de memória, não
  comportamento incorreto.
- **P1 #8 e P2 #7 (integridade de pedido/checkout).** Classifiquei como HIGH por serem bugs de
  regra de negócio com efeito financeiro. A escala do enunciado é orientada a arquitetura/SOLID e
  não tem um lugar óbvio para "bug de corretude"; dá para defender CRITICAL ("impede o
  funcionamento correto").
- **P2 #8 (pagamento simulado).** Pode ser intencional num projeto de demonstração. Mantive como
  HIGH pela mistura de regra de pagamento com a rota, não pela simulação em si.
- **P2 #16 (banco em memória).** Provavelmente escolha de demo (o README do projeto diz que o
  banco é em memória). Deixei como MEDIUM; se a intenção for demo, cai para LOW ou nem é problema.
- **P3 #4 vs #1.** MD5 isolado seria HIGH; a exposição do hash é que torna o conjunto CRITICAL.
  Mantive separados porque a correção de um não resolve o outro.
- **Versões de dependências com CVE.** Pelo que sei, `requests==2.31.0` e `flask-cors==4.0.0`
  (task-manager-api) têm advisories corrigidos em versões posteriores, e Express 4 já tem sucessor
  (Express 5). **Não listei** porque não verifiquei em fonte viva (sem pesquisa na web nesta
  sessão) e não há evidência no repositório. As deprecações listadas foram todas observadas: pelo
  runtime (P3 #12) ou declaradas no lockfile (P2 #15).
- **Seed com senhas fracas** (`database.py:75-79` no P1, `seed.py:19-33` no P3). Não listei à
  parte: são dados de exemplo; o problema real é o armazenamento/exposição, já listado.
- **LIKE sem escapar `%`/`_`** na busca do P3 (`routes/task_routes.py:252-253`). Não é injeção (o
  ORM parametriza), só busca imprecisa. Não listei.
- **Contaminação do gabarito.** Esta sessão carregou o `CLAUDE.md` do repositório, que cita como
  exemplos genéricos um arquivo de configuração com chave hardcoded, uma God Class em
  `AppManager.js` e uma query N+1 em pedidos. Os três achados aparecem aqui (P1 #4, P2 #5, P1 #11),
  mas seriam encontrados de qualquer forma. Não li o catálogo da skill nem os relatórios de rodada.

---

# Parte 2 — Extensão pós-rodada 6 (2026-10-13)

> **Leia antes de usar.** A Parte 1 acima é o gabarito **cego**: escrito antes de qualquer rodada, só
> com a leitura do código. Ela continua sendo o denominador de **recall** (25 + 21 + 23 = 69 itens) e
> **não foi alterada**. Esta Parte 2 acrescenta o que se aprendeu *depois*, com duas origens, e por isso
> **está contaminada por construção** (D12): vários itens existem porque a skill os viu primeiro.
>
> - **Regra de uso.** Recall histórico (rodadas 1–6) = só Parte 1. Recall da rodada 7 em diante = Parte 1
>   **e** Parte 1 + 2, reportados separados. Um item da Parte 2 achado pela skill **não** conta como
>   "achado além do gabarito" (D8): ele já está no gabarito. A métrica ⭐ passa a medir o que não está
>   em nenhuma das duas partes.
> - **Fonte `S`** = achado pela skill (Fase 2 da rodada limpa da rodada 6, ou rodada anterior citada).
>   **Fonte `V`** = achado por verificador independente executando a entrega (docs/verification/).
> - **Estado** diz o que a skill fez com o item na entrega `release/delivery-r6`: `corrigido`,
>   `proposto` (gate de contrato), `não visto` (a Fase 2 não reportou) ou `introduzido` (a
>   refatoração criou o defeito).
> - Linhas apontam o **código original** (`7ef5932`) salvo quando a coluna diz "entrega".

## code-smells-project — extensão

| # | Sev. | Problema | Arquivo:linhas | Fonte | Estado |
|---|---|---|---|---|---|
| X1.1 | MEDIUM | Dependências com advisory vivo (OSV.dev, 2026-10-12): `flask-cors` 5.0.1 e `flask` 3.1.1, mesma linha da dúvida "versões com CVE" da Parte 1 | `requirements.txt:1-2` | S | corrigido (upgrade dentro da major do flask; major do flask-cors coberta pelo replay de CORS) |
| X1.2 | MEDIUM | Listagens (produtos, usuários, pedidos) devolvem a tabela inteira, sem paginação | `models.py:4-22` | S | proposto (muda o corpo recebido) |
| X1.3 | MEDIUM | Conexão aberta por requisição e nunca fechada (ciclo de vida do handle), distinto da conexão global do item 9 | `database.py:10-11` | S | corrigido |
| X1.4 | CRITICAL | Relatório de vendas (agregado financeiro de todos os clientes) aberto a qualquer anônimo | `controllers.py:257-262`, `models.py:239-254` | S | corrigido (guarda de operador, D27) |
| X1.5 | CRITICAL | Contas de seed com senha conhecida (`admin`/`admin123`) criadas em todo banco vazio, inclusive em produção | `database.py:75-83` | S | proposto (mudaria quais contas existem). A Parte 1 decidiu *não* listar à parte; as skills reportam como CRITICAL. Divergência de severidade registrada |
| X1.6 | MEDIUM | Sem limite de tamanho de corpo nem de linhas por pedido (o sinal estava na lista de "verificados" da Fase 2 e não foi reportado) | `controllers.py:188-220`, `app.py:24-31` | S | não visto na Fase 2; achado pela re-auditoria (`missed-in-phase-2`); proposto |
| X1.7 | LOW | Colunas de conjunto fechado (`pedidos.status`, `usuarios.tipo`) como texto livre; `email` e `nome` anuláveis embora o código os desreferencie | `database.py:26-44` | S | não visto na Fase 2; proposto |
| X1.8 | MEDIUM | Inteiro fora da faixa do SQLite vira 500 depois da parametrização: `GET /produtos/<9999…9>` (original: 404) e `POST /produtos` com `estoque` gigante (original: 201) | entrega: `controllers/produto_controller.py`, `models/produto.py`, `controllers/validation.py` | V | **introduzido** pela correção do AP-02; a validação de borda não limita a faixa |
| X1.9 | LOW | Valor não finito aceito: `preco=1e999` (original: 500, agora 201 e `estoque` "inf") | entrega: `controllers/validation.py:12-16` (`eh_numero`) | V | **introduzido** (validação de tipo sem validação de faixa) |
| X1.10 | LOW | `POST /pedidos` com `itens` numérico → 500 por `len(itens)` antes de validar que é lista (o original também dava 500) | entrega: `controllers/pedido_controller.py:39` | V | não corrigido embora seja o "subconjunto seguro" de AP-11 (entrada malformada → 4xx) |
| X1.11 | LOW | JSON com milhares de níveis de aninhamento → 500 por recursão (original também) | entrega, todas as rotas de escrita | V | não visto |

## ecommerce-api-legacy — extensão

| # | Sev. | Problema | Arquivo:linhas | Fonte | Estado |
|---|---|---|---|---|---|
| X2.1 | MEDIUM | Advisories na cadeia de execução do Express (ex.: ReDoS em `path-to-regexp`, `qs`, `body-parser`) | `package.json:9-12` | S | corrigido (lockfile dentro da major) |
| X2.2 | HIGH | Página de erro padrão do framework com stack trace; `NODE_ENV` nunca definido | `src/app.js:5-6` | S | corrigido (middleware de erro central) |
| X2.3 | MEDIUM | Tipo errado derruba o **processo**: `card` ou `pwd` numérico → `cc.startsWith is not a function` / `ERR_INVALID_ARG_TYPE` (a Parte 1, item 11, cita só o `err` ignorado) | `src/AppManager.js:28-35`, `:45` | S | corrigido |
| X2.4 | LOW | Advisories e pacote sem manutenção na cadeia de instalação do `sqlite3` (a Parte 1, item 15, cita só a deprecação) | `package.json:11-11` | S | proposto (a única saída é um upgrade major cujas notas não cobrem a mudança do motor) |
| X2.5 | LOW | Ordem do relatório financeiro não determinística (curso e aluno) | `src/AppManager.js:83-127` | V | corrigido (ordem por id) |
| X2.6 | MEDIUM | `usr` e `eml` aceitam objeto, array e inteiro (200); o que foi gravado não foi conferido. A Parte 1, item 14, cita senha, e-mail, cartão e `c_id`, mas não o tipo de `usr`/`eml` | entrega: `src/routes/index.js` (validação de borda do checkout) | V | não corrigido (original igual) |
| X2.7 | MEDIUM | Placeholder fraco entregue: `OPERATOR_TOKEN=change-me` em `.env.example`; a guarda aceita esse valor se for o configurado | entrega: `.env.example` | V | **introduzido** |
| X2.8 | LOW | `DELETE /api/users/<id>` com id inexistente ou não numérico responde 200 "sucesso" (Parte 1, item 11, já cita) | entrega: `src/controllers/userController.js` | V | **ainda presente** na entrega (proposto como contrato) |
| X2.9 | LOW | O log de auditoria do checkout é só escrito e nunca lido. A skill reportou isso como AP-17 e retirou na re-auditoria ("trilha de auditoria é write-only por natureza") | `src/AppManager.js:57-58` | S | **falso positivo conhecido**; não é problema do alvo |

## task-manager-api — extensão

| # | Sev. | Problema | Arquivo:linhas | Fonte | Estado |
|---|---|---|---|---|---|
| X3.1 | HIGH | `flask-cors` 4.0.0 com 5 advisories (a Parte 1 declarou a dúvida e não listou por falta de evidência viva) | `requirements.txt:3-3` | S | parcial: 4.0.2 aplicado (fecha 2); os outros 3 só na 6.0.0, major cujo comportamento de path-matching o replay não exercita → proposto |
| X3.2 | LOW | `flask` 3.0.0 com advisory (cabeçalho `Vary` de sessão), reportado só na tabela de cobertura | `requirements.txt:1-1` | S | não visto como finding na Fase 2; achado pela re-auditoria; corrigido (3.1.3) |
| X3.3 | MEDIUM | O módulo de relatórios hospeda a API de categorias (nome e responsabilidade desencontrados) | `routes/report_routes.py:159-223` | S | corrigido |
| X3.4 | HIGH | Relatório geral e relatório por usuário (rollup de todos os principais) abertos a anônimos; a exclusão de conta também | `routes/report_routes.py:12-101`, `routes/user_routes.py:134-151` | S | corrigido (guarda de operador, D27). `GET /reports/user/<id>` é ambíguo (uma execução guardou, outra propôs) |
| X3.5 | MEDIUM | `tags` como objeto → 500 | entrega: `controllers/task_controller.py:25-30` (`normalize_tags` só trata lista) | V | não corrigido (original igual) |
| X3.6 | MEDIUM | `active` com valor não booleano (`"maybe"`) → 500 | entrega: `controllers/user_controller.py:117-118` | V | não corrigido (original igual); a Parte 1, item 9, cita `active` sem validação |
| X3.7 | MEDIUM | Nome de categoria como lista → 500 | entrega: `controllers/category_controller.py:57-58` | V | não corrigido (original igual) |
| X3.8 | MEDIUM | Id inteiro gigante em rota → 500 (`GET /tasks/<99…9>`) | rotas com `<int:id>` | V | não corrigido (original igual) |
| X3.9 | LOW | Contas legadas (MD5) só migram no próximo login bem-sucedido; quem nunca loga mantém o digest fraco no banco | `models/user.py` (entrega) | S, V | `unresolved` na execução `--yes`; residual declarado |
| X3.10 | LOW | `python app.py` com outro diretório corrente cria `instance/` e o banco relativos ao CWD; o README não avisa | entrega: `app.py`, `README.md` | V | introduzido (documentação) |
| X3.11 | MEDIUM | `PUT /users/<id>` (pode setar `active` e `role`) e cadastro com `role` no corpo seguem abertos | `routes/user_routes.py:52`, `119-122` | S, V | proposto; é a parte de **negócio** do item 2 da Parte 1 |

## Itens transversais — defeitos da própria skill (não do alvo)

Não entram no recall (não são problemas dos alvos), mas são **erros achados pelas execuções** e
precisam de tratamento na skill. Detalhe e proposta de mudança em
[`docs/rounds/round6-skill-results.md`](rounds/round6-skill-results.md).

| # | Problema | Origem |
|---|---|---|
| T1 | Artefatos da skill (`surface.json`, `baseline.json`) gravam senhas do seed e tokens de fixture do alvo | V |
| T2 | A skill não gera nem preserva `.gitignore` do alvo; a rodada limpa removeu o dos projetos 1 e 3 | orquestrador |
| T3 | `proc start` falha em imagem slim (sem hora de início do processo) | S (3 projetos) |
| T4 | Rótulo de container e scratch com identificador só de timestamp colidem em execuções simultâneas | S |
| T5 | AP-17 reporta tabela de auditoria "só escrita" | S |
| T6 | A Fase 2 lista um sinal como verificado e não reporta (corpo/array sem limite; advisory só na tabela de cobertura) | S |
| T7 | A classificação privilegiada/negócio diverge entre execuções (um relatório por usuário) | S |
| T8 | O replay compara forma, não valor: a busca com aspa passou a achar o produto; faixa de inteiro e `1e999` passam | S, V |
| T9 | AP-11 "subconjunto seguro" aplicado de forma incompleta: tipos errados ainda dão 500 em campos que a refatoração tocou | V |

## Cobertura da Parte 2

| Projeto | Itens | CRITICAL | HIGH | MEDIUM | LOW | Fonte S | Fonte V |
|---|---|---|---|---|---|---|---|
| code-smells-project | 11 | 2 | 0 | 5 | 4 | 7 | 4 |
| ecommerce-api-legacy | 9 | 0 | 1 | 4 | 4 | 5 | 4 |
| task-manager-api | 11 | 0 | 2 | 6 | 3 | 6 | 7 |
| **Total** | **31** | 2 | 3 | 15 | 11 | 18 | 15 |

(Itens com fonte "S, V" contam nas duas colunas; `T1..T9` não entram na contagem.)
