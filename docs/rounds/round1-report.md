# Rodada 1 — `/refactor-arch` nos três projetos-alvo

- **Data:** 2026-09-21
- **Branch com o código refatorado:** [`round1`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/tree/round1)
- **Estado da skill:** `catalog/frozen` (`38b77d9`), sem ajustes entre as rodadas
- **Tags de partida (D3):** `run/code-smells-project/iter1`, `run/ecommerce-api-legacy/iter1`,
  `run/task-manager-api/iter1`. As três apontam para `38b77d9`.

## Como a rodada foi executada

- **Isolamento de contexto (D3):** um subagente por projeto, os três em paralelo na mesma árvore de
  trabalho. Cada um começou com contexto próprio, escreveu só no próprio diretório e usou uma porta
  distinta para baseline e replay (5101, 5102 e 5103). Nenhum dos três rodou comandos git. Tags e
  commits ficaram com a sessão orquestradora.
- **Confirmação da Fase 2 (D10):** as três rodadas usaram `--yes`, porque um subagente não consegue
  responder ao prompt `[y/n]`. Os três relatórios registram
  `Confirmation: --yes (auto-approved, not human-reviewed)`. **Esta é uma rodada de calibração, não
  uma revisão humana.**
- **Escopo aplicado:** todas as severidades, com o gate de contrato ativo (D7).
- **Verificação upstream (D13):** modo completo nos três projetos. Houve consulta viva a OSV.dev e aos
  registries, e os warnings de deprecation do runtime foram forçados.

## Critérios de aceite (`instructions.md`)

| Critério | code-smells-project | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Fase 1 detecta a stack | ✓ Python 3.13 · Flask 3.1.1 · SQLite | ✓ Node 24 · Express 4.22.1 · sqlite3 5.1.7 | ✓ Python 3.13 · Flask 3.0.0 · Flask-SQLAlchemy 3.1.1 · SQLite |
| Fase 2 encontra ≥ 5 findings | ✓ 27 | ✓ 17 | ✓ 18 |
| Fase 2 tem ≥ 1 CRITICAL/HIGH | ✓ 8 C · 10 H | ✓ 5 C · 6 H | ✓ 4 C · 5 H |
| Fase 3: a aplicação funciona | ✓ boot + 43/43 PASS | ✓ boot + 11 PASS, 1 UNVERIFIED | ✓ boot + 55/55 PASS |

Nenhum dos três replays apontou regressão contra o baseline. Nenhum endpoint precisou ser marcado
`PRE-EXISTING FAILURE`.

## Resumo por projeto

| | code-smells-project | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Domínio | E-commerce (produtos, usuários, pedidos, relatório de vendas) | LMS com checkout, relatório financeiro e exclusão de usuário | Task manager (usuários, categorias, tarefas, relatórios) |
| Superfície | 19 rotas HTTP | 3 rotas HTTP | 21 rotas HTTP + script `seed.py` |
| Arquitetura original | 4 módulos planos (~780 linhas) | God Class + módulo utilitário (180 linhas) | Camadas só no nome: `services/` e `utils/` sem uso |
| Findings (C/H/M/L) | 27 (8/10/7/2) | 17 (5/6/3/3) | 18 (4/5/7/2) |
| Resolvidos | 22/27 | 14/17 | 13/18 |
| Linha da re-auditoria (D14) | `○ 4 proposed-not-applied, 4 unresolved (8)` | `○ 5 proposed-not-applied, 1 unresolved (6)` | `○ 5 proposed-not-applied, 0 unresolved (5)` |

Nenhum projeto recebeu `✓ Zero anti-patterns remaining`, e essa ausência está correta. Nos três
restaram itens `PROPOSED, NOT APPLIED`, então a skill não imprimiu a linha de zero, como a D14
determina.

## O que foi encontrado

As categorias que apareceram nos três projetos:

| Anti-pattern | csp | eal | tma | Severidade típica |
|---|:-:|:-:|:-:|---|
| AP-01 Segredos hardcoded | ✓ | ✓ | ✓ | CRITICAL |
| AP-04 Autorização ausente | ✓ | ✓ | ✓ | CRITICAL |
| AP-08 Dados sensíveis / senhas (texto puro, pseudo-hash, MD5, hash exposto na resposta) | ✓ | ✓ | ✓ | CRITICAL/HIGH |
| AP-05 Regra de negócio na camada de entrega | ✓ | ✓ | ✓ | HIGH |
| AP-06 Sem composition root | ✓ | ✓ | ✓ | HIGH |
| AP-09 Erros engolidos / sem transação | ✓ | ✓ | ✓ | HIGH/CRITICAL |
| AP-10 N+1 | ✓ | ✓ | ✓ | MEDIUM/HIGH |
| AP-11 Validação ausente | ✓ | ✓ | ✓ | MEDIUM/HIGH |
| AP-14 Dependência deprecated ou com advisory | ✓ | ✓ | ✓ | HIGH/MEDIUM/LOW |
| AP-15 Magic values | ✓ | ✓ | ✓ | LOW/MEDIUM |
| AP-02 SQL injection | ✓ | | | CRITICAL |
| AP-03 God Class / God Module | ✓ | ✓ | | CRITICAL |
| AP-07 Estado global mutável | ✓ | ✓ | | HIGH/MEDIUM |
| AP-12 Duplicação | ✓ | | ✓ | MEDIUM/HIGH |
| AP-13 Leituras sem limite | ✓ | | ✓ | MEDIUM |
| AP-16 Nomes / estrutura enganosa | ✓ | ✓ | ✓ | LOW |
| AP-17 Código morto | ✓ | ✓ | ✓ | LOW/MEDIUM |

**Evidência de APIs deprecated (D13):** houve achados reportáveis nos três projetos, todos com fonte e
data.
- **Tier A (warning emitido pelo runtime):** `datetime.utcnow` e `Query.get()` do SQLAlchemy, no
  task-manager-api.
- **Tier B (advisory):** flask e flask-cors (OSV.dev), transitivas do Express (npm audit) e a cadeia
  de instalação do sqlite3 5 (metadado de deprecation do registry).

**O baseline confirmou três findings de segurança** no code-smells-project. O login com SQL injection
entrou como admin sem senha (200). O pedido com quantidade negativa foi aceito (201). O `produto_id`
`"2 OR 1=1"` também foi aceito (201).

## O que foi alterado

As três aplicações terminaram com a mesma forma: `config/`, `models/`, `controllers/`, rotas ou views,
`middlewares/` com error handler central, e um `app.py`/`app.js` que só monta a aplicação.

- **code-smells-project**
  - `controllers.py`, `models.py` e `database.py` foram removidos.
  - O código agora está em `config/settings.py`, `models/` (repositórios, regras, erros, senhas),
    `controllers/` (5 casos de uso), `views/` (4 blueprints, schemas, serializers) e `middlewares/`.
  - Todas as queries usam parâmetros.
  - As senhas passaram a scrypt, com re-hash das antigas no próximo login.
  - Cada requisição abre a própria conexão.
  - O pedido é gravado numa única transação.
  - O N+1 virou join/`IN`.
  - Dependências: flask 3.1.3, flask-cors 6.0.5 e Werkzeug 3.1.8.
- **ecommerce-api-legacy**
  - `AppManager.js` e `utils.js` foram removidos.
  - O código agora está em `src/config`, `src/models` (wrapper de banco com transação, schema,
    repositórios, scrypt, erros de domínio), `src/controllers`, `src/routes` e `src/middlewares`.
  - O checkout passou a ser transacional.
  - Dependências: express `^4.22.3` e sqlite3 `^6.0.1`. O `npm audit` agora mostra 0
    vulnerabilidades.
  - Status, content-type e as mensagens em português foram preservados.
- **task-manager-api**
  - A lógica saiu das rotas para `controllers/`.
  - As entidades e seus repositórios ficam em `models/`, junto com `clock.py`, que substitui o
    `utcnow`.
  - As rotas de categoria ganharam arquivo próprio.
  - Foram adicionados `presenters.py`, `middlewares/error_handler.py` e `config/settings.py`.
  - `utils/` e `services/` foram removidos, porque eram código morto, assim como três dependências
    declaradas e nunca importadas.
  - As senhas saíram de MD5 para scrypt, com migração no login.
  - O N+1 virou eager loading ou consultas agrupadas.
  - Três erros 500 do baseline agora retornam 400 em JSON.

## O que ficou pendente

**Os três projetos:**
- **Rotacionar credenciais.** Segredos, senha de banco, chave do gateway e senha SMTP saíram do código,
  mas continuam no histórico do git.
- **Proposto, não aplicado: autenticação e autorização (AP-04).** Não existe modelo de usuário/papel
  sobre o qual basear a política, e adicionar 401/403 muda o contrato.

**code-smells-project:**
- **Unresolved, CRITICAL: contas do seed com senhas literais** (inclusive `admin123`), em
  `models/database.py:65-70`. A Fase 2 deixou passar e só a re-auditoria pegou.
- **Proposto, não aplicado: remover o campo `senha` das respostas de `/usuarios`.** Hoje ele expõe o
  hash.

**task-manager-api:**
- **Proposto, não aplicado: remover o campo `password` das respostas de usuário.**
- **Proposto, não aplicado: atualizar flask-cors para 6.x.** O harness não captura headers de CORS,
  então não havia como provar que a atualização não muda nada.

**ecommerce-api-legacy:**
- **Unresolved: `prebuild-install` deprecated,** puxado até pelo sqlite3 6.0.1, que é a versão mais
  recente. Não há advisory e o pacote só roda na instalação.

A lista completa, com justificativas, está nos relatórios de auditoria de cada projeto.

## Problemas da skill revelados nesta rodada

São insumos para a iteração 2. **Nenhum foi corrigido nesta rodada**, porque a skill ficou congelada.

| # | Problema | Visto em |
|---|---|---|
| 1 | **Porta hardcoded no original.** Não há orientação para subir o original em outra porta sem editá-lo antes do baseline. | csp, eal |
| 2 | **Runtime ausente.** "Never install a dependency" não cobre um host sem as dependências declaradas pelo próprio projeto. Cada subagente resolveu com um venv. | csp, tma |
| 3 | **Escrita na Fase 2.** A checagem de deprecation exige rodar a app, que cria arquivos de banco fora de `reports/`. A regra de escrita da D5/D10 não prevê arquivos de runtime. | csp, tma |
| 4 | **Crash no baseline.** O `probe.mjs` grava erro de transporte como `UNVERIFIED`, mas o protocolo §4 diz que conta como falha. Uma requisição que derrubava o original nunca aparece como melhoria. | eal |
| 5 | **Corpo em texto puro.** A comparação só de shape trata `text/html` como `opaque`, então uma mensagem de erro alterada passa despercebida. | eal |
| 6 | **Autorização.** O SKILL.md trata todo 401 novo como mudança de contrato, mas as guidelines §6/RP-04 mandam aplicar a verificação que falta. As duas orientações se contradizem. | csp |
| 7 | **Sem entrada para configuração insegura de execução** (debug ligado em `0.0.0.0`). Os subagentes classificaram sob AP-15 ou AP-06, com escalonamento improvisado. | csp, tma |
| 8 | **Sem entrada para dependência vulnerável** (e não deprecated). Os advisories caem em AP-14. | tma, eal |
| 9 | **Testes de ataque.** Entradas maliciosas mudam o status por definição e o harness as marca como `REGRESSION`. Não há conjunto de superfície separado para segurança. | csp |
| 10 | **Upgrade de dependência vs. contrato.** Não está definido se upgrade major ou com mudança de comportamento é mudança de contrato. Os subagentes decidiram de formas diferentes (sqlite3 5→6 aplicado; flask-cors 6.x proposto). | eal, tma |
| 11 | **Finding parcialmente resolvido.** Não está definido como ele conta na linha `Findings resolved`. | csp, eal |
| 12 | **A superfície não cresce depois do baseline.** Casos-limite descobertos depois só são checados após a refatoração, sem comparação. | tma |
| 13 | **Recall da Fase 2.** Três achados ficaram de fora da Fase 2: o stack trace vazado pelo error handler padrão do framework (eal), as senhas do seed (csp) e três invariantes de domínio (csp). Os dois últimos só apareceram na re-auditoria. O stack trace o subagente achou e corrigiu por conta própria na Fase 3. | csp, eal |

O item 13 é o argumento mais forte a favor da re-auditoria obrigatória (D14). Sem ela, uma senha
CRITICAL teria passado como resolvida.

## Intervenções

- **Sessão orquestradora:** nenhuma correção de rumo durante as rodadas.
- **task-manager-api:** o subagente rodou `git rm --cached` por engano em `utils/` e `services/`,
  apesar da instrução de não mexer no git. Ele desfez com `git restore --staged` na hora. O índice foi
  conferido antes do commit e estava vazio.

## Evidência

Os arquivos abaixo estão na branch `round1`.

| Projeto | Relatório de auditoria | Transcript | Baseline / replay |
|---|---|---|---|
| code-smells-project | [`reports/audit-project-1.md`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/blob/round1/reports/audit-project-1.md) | [`runs/code-smells-project-iter1.md`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/blob/round1/runs/code-smells-project-iter1.md) | [`code-smells-project/reports/`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/tree/round1/code-smells-project/reports) |
| ecommerce-api-legacy | [`reports/audit-project-2.md`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/blob/round1/reports/audit-project-2.md) | [`runs/ecommerce-api-legacy-iter1.md`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/blob/round1/runs/ecommerce-api-legacy-iter1.md) | [`ecommerce-api-legacy/reports/`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/tree/round1/ecommerce-api-legacy/reports) |
| task-manager-api | [`reports/audit-project-3.md`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/blob/round1/reports/audit-project-3.md) | [`runs/task-manager-api-iter1.md`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/blob/round1/runs/task-manager-api-iter1.md) | [`task-manager-api/reports/`](https://github.com/lucas-c-almeida/mba-ia-refactor-projects-skill/tree/round1/task-manager-api/reports) |
