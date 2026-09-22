# CLAUDE.md — Projeto: Skill `refactor-arch`

> Fonte única desta especificação: **`instructions.md`** — o enunciado original do desafio,
> preservado sem alterações (era `README.md` no repositório base; renomeado para liberar
> `README.md` para a documentação de entrega).
>
> **Convenção de termos neste documento:** onde se lê "o README" sem qualificação, trata-se do
> **enunciado** (`instructions.md`). O `README.md` da raiz é o **entregável** de documentação,
> descrito em §7.
>
> Este documento foi escrito **sem** ler o código dos três projetos-alvo — de propósito.
> Ver §2 (Princípio diretor) e D12.

---

## 1. O que é este repositório

Repositório de um desafio do MBA FullCycle. O **entregável não é código refatorado** — é uma
**Skill** (`refactor-arch`) capaz de analisar, auditar e refatorar *qualquer* codebase para o
padrão MVC, de forma agnóstica de tecnologia.

Os três projetos existentes são **campo de prova**, não o produto:

| Projeto | Stack | Domínio | Nível de organização |
|---|---|---|---|
| `code-smells-project/` | Python / Flask | API de E-commerce | Monolito desestruturado |
| `ecommerce-api-legacy/` | Node.js / Express | LMS API com checkout | Desestruturado (`AppManager.js`, `utils.js`) |
| `task-manager-api/` | Python / Flask | API de Task Manager | Parcialmente organizado (`models/`, `routes/`, `services/`, `utils/`) |

O código refatorado dos três é **subproduto** da execução da skill, e serve como evidência de que
ela funciona. Os critérios de aceite exigem sucesso nos **3/3**, não em um.

---

## 2. Princípio diretor: a skill não pode ser *overfitted*

Esta é a restrição mais importante do projeto, definida pelo autor do repositório.

**Regra de ouro:** a skill (SKILL.md + arquivos de referência) **nunca** pode conter:

- nome de arquivo dos projetos-alvo (`AppManager.js`, `models.py`, `database.py`, …);
- nome de função, rota, tabela, variável ou constante específica dos projetos;
- descrição de um bug concreto encontrado em um dos projetos;
- contagem esperada de findings ("este projeto tem 14 problemas");
- qualquer heurística que só faça sentido em uma das três codebases.

**Como escrever no lugar:** descrever o *sinal observável* e o *raciocínio*, não a instância.

| ❌ Overfitted | ✅ Generalizável |
|---|---|
| "Procure pela SECRET_KEY hardcoded em `app.py`" | "Literal string atribuída a identificador cujo nome casa com `(secret|key|token|password|pwd|credential|api_key|dsn|conn_str)`, fora de arquivo de exemplo/teste" |
| "O `AppManager.js` é uma God Class" | "Um único módulo concentra ≥3 responsabilidades distintas (persistência, regra de negócio, roteamento/IO, formatação) **ou** excede ~300 linhas com ≥2 dessas responsabilidades" |
| "Corrigir a query N+1 do endpoint de pedidos" | "Chamada a driver de banco (`execute`/`query`/`find`) dentro de corpo de laço, ou em função chamada dentro de laço" |

**Teste do Quarto Projeto (critério de aceite interno):** antes de considerar a skill pronta,
perguntar de cada linha do SKILL.md e dos arquivos de referência:
*"isso continuaria correto e útil se o alvo fosse um projeto Ruby/Rails ou Go que eu nunca vi?"*
Se a resposta for não, a linha está acoplada e deve ser generalizada ou removida.

**Corolário de método:** a *análise manual* dos 3 projetos (requisito §1 do README) serve para
**calibrar** o catálogo — confirmar que as categorias existem no mundo real e medir recall —
e **não** para populá-lo com casos. O catálogo nasce de literatura de anti-patterns
(Fowler/Refactoring, SOLID, OWASP); a análise manual só verifica cobertura.

---

## 3. Requisitos obrigatórios extraídos do README

### 3.1 Identidade e localização (imutáveis)
- Nome da skill: **`refactor-arch`** (não alterar).
- Arquivo principal: **`SKILL.md`** (não alterar).
- Path: `<projeto>/.claude/skills/refactor-arch/` — presente nos **3** projetos.
- Invocação: `claude "/refactor-arch"` a partir da raiz de cada projeto.
- Arquivos de referência: **Markdown**.

### 3.2 As 3 fases sequenciais

| Fase | Nome | Obrigações |
|---|---|---|
| 1 | **Análise** | Detectar linguagem, framework (+versão), dependências, domínio, arquitetura atual, nº de arquivos, tabelas de BD. Imprimir resumo em bloco formatado. |
| 2 | **Auditoria** | Cruzar código contra o catálogo de anti-patterns. Gerar relatório com findings **ordenados por severidade** (CRITICAL→LOW), cada um com **arquivo e linhas exatos**. **PAUSAR e pedir confirmação humana** antes de tocar em qualquer arquivo. |
| 3 | **Refatoração** | Reestruturar para MVC. **Validar**: app sobe sem erro + endpoints originais respondem. Imprimir a nova árvore de diretórios e o resultado da validação. |

A pausa na Fase 2 é **obrigatória e bloqueante**. Nenhuma escrita em arquivo do projeto antes do `y`.

### 3.3 As 5 áreas de conhecimento (cobertura obrigatória)

A organização e a quantidade de arquivos são livres; a **cobertura** não é.

| Área | Conteúdo mínimo |
|---|---|
| Análise de projeto | Heurísticas de detecção de linguagem, framework, banco de dados; mapeamento de arquitetura |
| Catálogo de anti-patterns | ≥8 anti-patterns, com sinais de detecção e severidade distribuída entre CRITICAL/HIGH/MEDIUM/LOW; **obrigatório incluir detecção de APIs deprecated** com o equivalente moderno |
| Template de relatório | Formato padronizado da saída da Fase 2 |
| Guidelines de arquitetura | Regras do MVC alvo: responsabilidades de Models, Views/Routes e Controllers |
| Playbook de refatoração | ≥8 padrões de transformação com exemplos de código **antes/depois** |

### 3.4 Requisitos numéricos (checklist rápido)
- [ ] ≥ 8 anti-patterns no catálogo, cobrindo as 4 severidades
- [ ] ≥ 1 anti-pattern de **API deprecated** com recomendação do equivalente moderno
- [ ] ≥ 8 padrões de transformação no playbook, com código antes/depois
- [ ] Fase 2 pausa antes de modificar arquivos
- [ ] Fase 3 valida boot + endpoints

---

## 4. Escala de severidade (canônica — usar literalmente)

Retirada do README; é o vocabulário compartilhado entre catálogo, relatório e playbook.

- **CRITICAL** — falhas graves de arquitetura ou segurança que impedem o funcionamento correto,
  expõem dados sensíveis (credenciais hardcoded, SQL Injection) ou violam completamente a
  separação de responsabilidades (God Class com BD + lógica + roteamento no mesmo arquivo).
- **HIGH** — fortes violações de MVC ou SOLID que dificultam muito manutenção e testes
  (lógica de negócio pesada dentro de Controllers, forte acoplamento sem Injeção de Dependência,
  estado global mutável).
- **MEDIUM** — padronização, duplicação de código ou gargalos de performance moderada
  (N+1, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW** — legibilidade, nomenclatura ruim, magic numbers.

**Regra de desempate (decisão nossa, ver §8):** a severidade é determinada pelo **impacto no
contexto**, não pela etiqueta da categoria. O catálogo define a severidade *default* de cada
anti-pattern e as condições explícitas de escalonamento/rebaixamento.

---

## 5. Contrato de saída de cada fase

O README mostra a forma esperada; ela é parte do entregável e deve ser reproduzida.

**Fase 1** — bloco `PHASE 1: PROJECT ANALYSIS` com: Language, Framework, Dependencies, Domain,
Architecture, Source files, DB tables.

**Fase 2** — bloco `ARCHITECTURE AUDIT REPORT` com cabeçalho (Project/Stack/Files), `## Summary`
com a contagem por severidade, `## Findings` e, por finding:

```
### [SEVERITY] Nome do Anti-Pattern
File: <caminho>:<linha-inicial>-<linha-final>
Description: <o que foi encontrado>
Impact: <por que importa>
Recommendation: <o que fazer>
```

Fechando com `Total: N findings` e o prompt de confirmação.

**Fase 3** — bloco `PHASE 3: REFACTORING COMPLETE` com `## New Project Structure` (árvore) e
`## Validation` (checks com ✓/✗).

---

## 6. Critérios de aceite (do README) — valem nos 3/3 projetos

| Critério | Requisito |
|---|---|
| Fase 1 detecta a stack corretamente | 3/3 |
| Fase 2 encontra ≥ 5 findings | 3/3 |
| Fase 2 inclui ≥ 1 CRITICAL ou HIGH | 3/3 |
| Fase 3 — app funciona após a refatoração | 3/3 |

Adicionalmente, o README pede que a Fase 2 reencontre **≥5** dos problemas documentados na
análise manual do projeto 1.

O checklist de validação completo (Fases 1/2/3) está no README, seção "Validação" — deve ser
preenchido por projeto e publicado no README de entrega.

---

## 7. Entregáveis

```
mba-ia-refactor-projects-skill/
├── README.md                     # A: Análise Manual · B: Construção da Skill
│                                 # C: Resultados · D: Como Executar
├── reports/
│   ├── audit-project-1.md        # saída da Fase 2 — code-smells-project
│   ├── audit-project-2.md        # saída da Fase 2 — ecommerce-api-legacy
│   └── audit-project-3.md        # saída da Fase 2 — task-manager-api
├── code-smells-project/.claude/skills/refactor-arch/
├── ecommerce-api-legacy/.claude/skills/refactor-arch/
└── task-manager-api/.claude/skills/refactor-arch/
```

Mais o código refatorado dos três projetos, commitado.

### 7.1 Artefatos de processo (nossos, fora da estrutura exigida)

A árvore acima é a exigida pelo enunciado. Nossas decisões produzem artefatos adicionais, que
**não** substituem nada dela. `CLAUDE.md` e `instructions.md` ficam na raiz; todo o resto fica
agrupado sob `docs/`:

```
instructions.md                # enunciado original, preservado intacto (era README.md)
CLAUDE.md                      # esta especificação viva
docs/decisions.md              # registro ADR das decisões, com alternativas e custos
docs/rounds/round<K>-report.md # relatório consolidado de cada rodada
docs/rounds/round<K>-changes.md# lista de mudanças congelada antes da rodada K (D12, enfraquecida)
docs/runs/p<N>-iter<K>.md      # transcript de cada rodada                 (D3)
docs/evals/rubric.md           # rubrica de avaliação                      (D8)
docs/evals/run-p<N>-iter<K>.md # scorecard preenchido por rodada           (D8)
docs/gabarito.md               # análise manual (gabarito, D12); cópia na seção A do README
tests/probe-conformance/       # teste de conformidade entre os probes (D6.3) — exceção: fica na raiz
```

O teste de conformidade fica **fora** da skill de propósito: é ferramenta de manutenção de quem
escreve a skill, não algo que a skill leva para dentro do alvo. Rode-o sempre que um dos probes ou
o `06-validation-protocol.md` mudar: `python tests/probe-conformance/run.py`.

Dentro de cada projeto-alvo, a skill gera `<alvo>/reports/audit-*.md` (D5); a entrega copia o
`audit-latest.md` de cada um para `reports/audit-project-N.md` na raiz.

**Nota:** `docs/runs/` e `docs/evals/` existem para a nossa metodologia de medição, não para a
nota. Se poluírem a entrega, vão para `.gitignore` — mas a decisão padrão é commitá-los, porque são a
evidência de que a seção C do README de entrega não foi inventada.

---

## 8. Decisões de projeto

> Cada decisão registra **o quê** e **por quê**.

### D1 — Idioma: **inglês integral** ✅ decidido

SKILL.md, arquivos de referência e relatórios de auditoria em inglês, incluindo os rótulos
(`PHASE 1`, `[CRITICAL]`, `File:`, `Description:`, `Impact:`, `Recommendation:`).

**Por quê:** (a) os nomes canônicos dos anti-patterns são em inglês — traduzir *God Class* para
*Classe Deus* afasta o leitor da literatura e da busca; (b) uma skill agnóstica de tecnologia
também deveria ser agnóstica de idioma do time que a usa; (c) o vocabulário do modelo para
conceitos de arquitetura é mais preciso em inglês, o que melhora a qualidade da detecção.
**Custo aceito:** diverge da prosa em português do exemplo do README (o formato estrutural é o mesmo).

### D2 — Fonte da verdade: **cópia única na raiz** ✅ decidido

A skill canônica vive em `.claude/skills/refactor-arch/` **na raiz do repositório**. As execuções
acontecem a partir da raiz, projeto por projeto. Não se mantém uma quarta cópia em `skill-source/`.

**Por quê:** uma cópia só é a garantia estrutural contra divergência — não existe "a versão do
projeto 2" para ajustar sob pressão. Isso transforma o anti-overfitting de disciplina em
propriedade do repositório.

**Consequência de design obrigatória (D2.1):** como o Claude roda a partir da raiz e não de dentro
do projeto, a skill **não pode assumir que o projeto-alvo é o diretório corrente**. O SKILL.md
aceita um **diretório-alvo opcional** como argumento e usa o CWD como padrão:

```
/refactor-arch                      # alvo = diretório corrente
/refactor-arch code-smells-project  # alvo = subdiretório informado
```

Isso não é uma concessão: um projeto real é um subdiretório de um monorepo com a mesma frequência
com que é a raiz de um checkout. Escopar o alvo explicitamente deixa a skill **mais** genérica, e
todo path em relatório e validação passa a ser relativo ao alvo, nunca ao CWD.

**Consequência operacional (D2.2):** na entrega, um passo de sync copia
`.claude/skills/refactor-arch/` para dentro dos 3 projetos, cumprindo a estrutura exigida em §7.
A cópia é feita **uma vez, ao final**, nunca durante a iteração.

### D3 — Isolamento entre rodadas: **sessão limpa + tag git + transcript** ✅ decidido

Cada execução da skill num projeto é uma **rodada**, e toda rodada é isolada em três eixos:

| Eixo | Mecanismo | Contra o quê protege |
|---|---|---|
| Contexto | Sessão nova do Claude por projeto (nunca os 3 na mesma) | Contaminação: o agente chegar no projeto 2 já "sabendo" o que achar |
| Código | `git tag run/p<N>/iter<K>` antes de cada rodada | Rodada não repetível; impossibilidade de re-testar após ajustar a skill |
| Evidência | Transcript salvo em `docs/runs/p<N>-iter<K>.md` | Perder o *porquê* de uma regressão quando a sessão fecha |

```bash
git tag run/p2/iter1
claude                                   # sessão NOVA, contexto zerado
> /refactor-arch ecommerce-api-legacy
# ajustou a skill? volta ao ponto e roda de novo:
git reset --hard run/p2/iter1
```

**Por quê o eixo de contexto é o mais importante:** é o único invisível. Um repositório sujo
denuncia a falta de reset; uma sessão contaminada produz um resultado que *parece* ótimo. Rodar os
3 projetos na mesma sessão mede a memória do agente, não a qualidade do catálogo — e é overfitting
em tempo de execução, indistinguível de uma skill genuinamente boa a partir do output.

### D4 — Validação da Fase 3: **baseline antes + replay depois** ✅ decidido

A skill captura, **antes** de escrever qualquer arquivo, um baseline comportamental do projeto
original; **depois** da refatoração, repete as mesmas chamadas contra a aplicação nova e compara.

Fluxo:

1. **Inventário de endpoints** — extraído estaticamente do código original (método + path + params).
2. **Captura do baseline** — sobe a aplicação original, chama cada endpoint, grava status code e a
   *forma* da resposta (chaves do JSON / tipo), não os dados voláteis (ids, timestamps).
3. *(refatoração)*
4. **Replay** — sobe a aplicação refatorada, repete as mesmas chamadas, compara com o baseline.
   Divergência = **regressão**, reportada explicitamente.

**Por quê:** isto é um *characterization test* (Michael Feathers, *Working Effectively with Legacy
Code*). Sem baseline, "os endpoints respondem" é uma afirmação vazia: um endpoint que já retornava
500 antes continua retornando 500 depois e passa como "não quebrei nada". O baseline é também o que
permite refatorar com agressividade (D7) sem apostar.

**Regra de honestidade:** endpoints que já falhavam no baseline são marcados
`PRE-EXISTING FAILURE`, não `✗`. A skill nunca relata como sucesso algo que não verificou, e nunca
imputa à refatoração um defeito que já existia.

### D5 — Relatório da Fase 2: **dentro do alvo, com histórico** ✅ decidido

A skill escreve `<alvo>/reports/audit-<YYYYMMDD-HHMM>.md` e atualiza `<alvo>/reports/audit-latest.md`.
Um passo de entrega (§7) copia o `audit-latest.md` de cada projeto para `reports/audit-project-N.md`
na raiz.

**Por quê:** a skill não pode conhecer o layout deste repositório — não existe "project-1" no mundo,
existe *um diretório que ela recebeu como alvo*. Saber que `code-smells-project` é o projeto 1 seria
acoplamento estrutural ao enunciado. O timestamp existe para comparar iterações (D8).

**Ressalva registrada:** escrever o relatório é escrita em disco antes da confirmação da Fase 2.
Isto **não** viola a regra, porque a regra proíbe modificar **arquivos do projeto**. `reports/` é
artefato de auditoria, não código-fonte. O SKILL.md deve dizer isso de forma explícita para o agente
não se autoparalisar: *"Phase 2 may write only to `<target>/reports/`. No file outside it may be
created, modified or deleted before the user confirms."*

### D6 — Validação: **protocolo normativo + harness no runtime do alvo** ✅ decidido (revisado)

> **Revisão:** a versão anterior fixava o harness em Python, com fallback para `curl`. Duas falhas
> foram identificadas na discussão e corrigidas abaixo. O registro do erro fica porque o raciocínio
> é o conteúdo educativo da decisão.
>
> **Falha 1 — escolha de runtime por overfitting ao conjunto de amostra.** Python foi escolhido
> porque 2 dos 3 projetos-alvo são Flask. Não há nada em "auditar uma codebase" que exija Python;
> num alvo Go a escolha vira dependência arbitrária. É o mesmo erro que o §2 proíbe, cometido na
> escolha da ferramenta em vez de no conteúdo do catálogo.
>
> **Falha 2 — fallback que não era equivalente.** `curl` emite requisições, mas não faz diff
> estrutural de JSON; isso exigiria `jq`, que é menos disponível que Python ou Node. O "fallback"
> degradava silenciosamente para paridade de status code — vendido como plano B, era um plano C
> não declarado.

**D6.1 — Separação de responsabilidades (mantida).** O harness **não sobe a aplicação**. Subir é
específico de stack (`flask run`, `npm start`, `go run`); sondar é protocolo puro.

| Responsabilidade | Quem | Por quê |
|---|---|---|
| Descobrir o comando de boot | Agente (saída da Fase 1) | Varia por stack — é o que a Fase 1 deduz |
| Subir o processo e esperar ficar pronto | Agente | Idem |
| Exercitar a superfície, gravar e comparar | Harness | O algoritmo é o mesmo em toda linguagem |

**D6.2 — O runtime do harness é o runtime do alvo.** Princípio: *se você consegue subir a
aplicação, você tem um runtime no qual consegue escrever um script.* A Fase 1 já detectou a stack
antes de o harness ser necessário. Alvo Python → harness Python (stdlib). Alvo Node → harness Node
(zero deps, `fetch` nativo). A dependência adicional é **zero por construção**, não por sorte.

**D6.3 — O protocolo é normativo; as implementações são traduções.**

```
references/06-validation-protocol.md   ← spec normativa (Markdown)
scripts/probe.py                       ← implementação de referência (stdlib)
scripts/probe.mjs                      ← implementação de referência (zero deps)
  stack não coberta                    → agente emite a partir da spec
  nenhum runtime com JSON              → MODO PISO (ver D6.4)
```

Isto **não** é "scripts por ecossistema" (opção descartada na discussão): aquilo seria
anti-agnóstico se o *protocolo* variasse por stack. Ele não varia — existe um documento só, e as
implementações são finas e derivadas dele. A stack nunca vista se resolve por geração a partir da
spec, que era a proposta "Markdown puro" original, agora como caminho geral em vez de único.

**D6.4 — Modo piso declarado, não fallback silencioso.** Sem nenhum runtime capaz de processar
JSON, a validação cai para paridade de status code via `curl`, e o relatório **declara** que a
validação foi degradada e o que deixou de ser verificado. *Validação degradada rotulada é honesta;
validação degradada silenciosa é pior que não ter validação.*

**D6.5 — Comparação de forma, não de dados.** Compara-se status/exit code, content-type e o
**shape** do resultado (conjunto de chaves e tipos, recursivamente) — nunca valores voláteis (ids,
timestamps, ordenação não determinística). Comparar valores produziria regressões falsas a cada
rodada, e em dois dias a gente aprenderia a ignorar o resultado da validação. Uma validação
ruidosa é pior que nenhuma: custa o mesmo e você para de ler.

**D6.6 — Conformidade com o README.** O enunciado exige *arquivos de referência em Markdown*; os
5+ arquivos de conhecimento são Markdown. O harness não é arquivo de referência — é ferramental, e
o protocolo que ele implementa está integralmente descrito em `06-validation-protocol.md`.

### D7 — Escopo da Fase 3: **corrigir tudo, com gate de contrato** ✅ decidido

A Fase 3 corrige findings de **todas as severidades**. Porém, qualquer correção que alteraria o
**contrato público** da aplicação **não é aplicada** — é registrada como `PROPOSED, NOT APPLIED`,
com justificativa, no relatório final.

Contam como mudança de contrato: renomear/mover rota, alterar método HTTP, mudar status code de
sucesso, mudar o formato do corpo da resposta, remover ou renomear campo, tornar obrigatório um
parâmetro antes opcional.

**Não** contam como mudança de contrato (e portanto são aplicadas): corrigir SQL injection, mover
segredo para variável de ambiente, eliminar N+1, extrair lógica para camada, renomear identificador
interno, transformar magic number em constante, centralizar error handling. Estas mudam a
*implementação*, não o que o cliente observa em uso legítimo.

**Por quê:** o README pede `Zero anti-patterns remaining`, mas "não quebrou nada" (D4) só é uma
afirmação verificável se o contrato for preservado. O gate resolve a tensão entre as duas
exigências sem sacrificar nenhuma: tudo que é seguro é corrigido, tudo que é arriscado é proposto
com argumento. Decidir *por* o time o que quebrar não é papel de uma ferramenta automatizada.

### D8 — Medição: **scorecard formal com métricas de generalização** ✅ decidido

`docs/evals/rubric.md` define a rubrica; cada rodada produz `docs/evals/run-p<N>-iter<K>.md`.

Métricas, e o que cada uma responde:

| Métrica | Pergunta que responde |
|---|---|
| Checklist do README (Fases 1/2/3) | A skill cumpre o contrato do desafio? (binário, obrigatório) |
| **Recall** vs. análise manual | Dos problemas que eu sei que existem, quantos ela achou? |
| **Falsos positivos** | Quantos findings apontam para código que está correto? |
| **Findings inventados** | Quantos citam arquivo/linha que não existe ou não contém aquilo? |
| **Achados além do gabarito** ⭐ | Quantos problemas legítimos ela achou que **não** estavam na minha análise manual? |
| Regressões pós-refactor | Quantos endpoints divergiram do baseline (D4)? |
| Intervenções humanas | Quantas vezes precisei corrigir o rumo para a rodada terminar? |

**Por que "achados além do gabarito" é a métrica-chave:** recall alto é fácil de obter trapaceando —
basta escrever o catálogo a partir da análise manual, e a skill reencontra 100% do que você plantou.
Essa métrica mede o oposto: a capacidade de ver o que o autor do catálogo **não** viu. É a única
evidência positiva de que a skill generaliza em vez de reproduzir gabarito, e é diretamente o
inverso do risco descrito em §2.

**Findings inventados** é a contramétrica indispensável. Sem ela, "achou 30 problemas" é
recompensado mesmo quando 12 são alucinação. Recall e precisão sempre se medem juntos.

---

### D9 — Arquivos originais na Fase 3: **reescrita in-place** ✅ decidido

O conteúdo migra para as camadas e os arquivos originais são removidos. Rede de segurança: o
histórico do git, as tags de rodada (D3) e o baseline comportamental (D4).

**Por quê:** é a única opção compatível com `Zero anti-patterns remaining`. Deixar o código antigo
ao lado do novo — em `src/` paralelo ou em `legacy/` — mantém no repositório uma segunda
implementação do mesmo comportamento, com todos os anti-patterns intactos. Uma auditoria seguinte
os reencontraria, e com razão: código morto é um anti-pattern, não um backup. Backup é o que o git
faz, e faz melhor.

### D10 — Confirmação da Fase 2: **obrigatória, com escape para iteração** ✅ decidido

A pausa é **requisito explícito do enunciado**, cobrado em cinco pontos de `instructions.md`
(L156 definição da fase, L177 requisitos da skill, L196 roteiro de execução, L260 checklist de
validação avaliado, L447 dicas finais). Fica **ON por padrão** e não pode ser desligada por default.

**Escape para o nosso ciclo de calibração:** a skill aceita `--yes`, que pula a confirmação. Existe
porque vamos rodar 2–4 iterações por projeto (o próprio README avisa) e reconfirmar um relatório já
lido é atrito sem valor. O relatório **registra qual modo foi usado**, para não confundirmos uma
rodada auto-aprovada com uma revisada por humano.

**Forma da confirmação:** prompt `[y/n]` literal, como no exemplo do README, com uma opção adicional
para aplicar apenas CRITICAL+HIGH. O `y/n` garante a correspondência com o que será avaliado; a
terceira opção é aditiva e não descumpre nada.

**Escrita permitida antes do `y`:** apenas `<alvo>/reports/` (ver D5). Nenhum arquivo fora dali
pode ser criado, alterado ou removido antes da confirmação.

**D10.1 — Reconciliação com D7 (tensão levantada na auditoria do registro).** D7 manda "corrigir
tudo"; a terceira opção desta confirmação permite aplicar só CRITICAL+HIGH. Não é contradição, é
precedência: **a escolha humana no gate prevalece sobre o escopo default da Fase 3.** Porém uma
rodada executada nesse modo **não pode ser lida como evidência de `Zero anti-patterns remaining`**,
e o relatório deve declarar o escopo aplicado no cabeçalho — junto com o modo de confirmação
(humano ou `--yes`). Sem isso, uma rodada parcial seria indistinguível de uma completa no
scorecard (D8), o que é exatamente a degradação silenciosa que este projeto proíbe.

### D11 — Escopo: **genérico por superfície pública, não só HTTP** ✅ decidido

Dois eixos que estavam misturados e agora são tratados separadamente:

- **Agnóstica de stack** (Python/Node/Go/Ruby) — exigido pelo README.
- **Agnóstica de tipo de aplicação** (API/CLI/worker/biblioteca) — não exigido, mas adotado.

**Conceito unificador:**

> **Superfície pública** = o conjunto de pontos de entrada observáveis que o mundo externo usa.

O algoritmo de validação (D4) é o mesmo para todos — *enumerar a superfície → exercitar → gravar a
forma → comparar*. Só o adaptador muda:

| Tipo de aplicação | Superfície | O que se compara |
|---|---|---|
| Serviço HTTP | rotas (método + path) | status, content-type, shape do corpo |
| CLI | comandos + flags | exit code, shape do stdout |
| Biblioteca | API exportada | assinaturas, shape do retorno |
| Worker / consumidor | mensagens consumidas | efeitos e mensagens produzidas |

Generalizar assim **reduz** trabalho: elimina a hipótese "existe uma porta HTTP" espalhada pelo
SKILL.md, substituindo-a por um conceito único com um ponto de extensão.

**D11.1 — Consequência sobre o alvo arquitetural.** MVC pressupõe roteamento e apresentação. Para
uma biblioteca pura não existe View, e forçar MVC produziria uma pasta `views/` vazia só para
satisfazer checklist. As guidelines definem o alvo como **separação de camadas, com MVC como
instância concreta**: havendo superfície de requisição, MVC literal (o caso dos 3 projetos e o que
o README cobra); não havendo, o mapeamento mais próximo (domínio / portas / adaptadores), com o
relatório **declarando** a adaptação e a justificativa.

### D12 — Ordem de trabalho: **catálogo cego primeiro, gabarito em sessão separada** ✅ decidido

1. **Agora**, nesta sessão, sem ter lido nenhum dos 3 projetos: escrever o catálogo de
   anti-patterns e as demais referências, a partir de literatura (Fowler, SOLID, OWASP).
2. **Congelar e commitar** o catálogo.
3. **Depois**, em sessão separada que nunca viu o catálogo: fazer a análise manual dos 3 projetos
   (requisito do README) — esse é o **gabarito**.
4. Comparar os dois para produzir as métricas do D8.

**Por quê:** o catálogo e o gabarito precisam ser mutuamente independentes, senão as métricas
mentem — e mentem nas duas direções.

- Gabarito primeiro → o catálogo nasce enviesado, contendo só as categorias que eu por acaso vi.
  A contaminação não aparece como nome de arquivo (que o §2 pega), aparece na **escolha das
  categorias incluídas**, que nenhuma revisão detecta.
- Catálogo primeiro, na mesma sessão → o *gabarito* é que nasce enviesado: encontro exatamente o
  que o catálogo manda procurar, o recall infla para ~100% e "achados além do gabarito" vira zero
  por construção. A skill fica boa; a métrica morre.

**Este momento é irrepetível:** é a única janela em que o autor do catálogo está genuinamente cego
para os alvos. Depois de ler um projeto, não há como desler.

---

### D13 — APIs deprecated: **evidência viva, nunca lista estática** ✅ decidido

O README exige detecção de APIs obsoletas. Isso colide com §2: todo item útil dessa categoria é
acoplado a um ecossistema **e perece** — uma lista escrita hoje estará errada em 18 meses, e uma
skill que afirma deprecation por memória produz *findings inventados* (contramétrica do D8).

**Proposta descartada:** apêndice estático datado com exemplos por ecossistema. Recusado: conteúdo
perecível versionado dentro da skill envelhece sem aviso e contamina o catálogo.

**Regra fundante:**

> A skill pode saber **onde perguntar**. Ela não pode saber **a resposta**.
>
> O conhecimento do modelo é **gerador de hipótese, nunca evidência**. O modelo pode decidir
> *verificar* se algo está deprecated; não pode **reportar** que está. Todo finding desta
> categoria cita **fonte + data da consulta**, ou não é reportado.

Um endpoint de registry é infraestrutura estável e pode ser versionado (diz *para onde* mandar a
query). "O pacote X está deprecated" é fato perecível e só pode vir de consulta viva.

#### Camada 1 — evidência local, offline, forçada

Não basta *observar* warnings: os runtimes os **escondem** por padrão. Python suprime
`DeprecationWarning` fora do `__main__`; Node mantém *pending deprecations* desligadas. "Rodou
limpo" com os detectores desligados não é informação.

A skill **liga os detectores** antes de concluir qualquer coisa:

```bash
PYTHONWARNINGS=always::DeprecationWarning   python -X dev <boot>
node --pending-deprecation --trace-deprecation <boot>
```

Benefício colateral: o warning vem com **stack trace apontando arquivo e linha** — exatamente o
campo `File: <caminho>:<linha>` exigido pelo relatório. A evidência chega no formato do entregável.

Complementos locais e agnósticos: dependência marcada como deprecated no manifesto/lockfile; e
padrões estruturalmente superados (callback onde o ecossistema migrou para async; API síncrona
bloqueante onde existe assíncrona).

#### Camada 2 — consulta viva, opcional, nunca estática

Executada em tempo de execução, com resultado carimbado com a data. Versiona-se apenas a **tabela
de adaptadores** (onde perguntar), nunca respostas.

| Fonte | Consulta | Cobre |
|---|---|---|
| **OSV.dev** | `POST api.osv.dev/v1/query` | advisories por pacote+versão; **uma API para npm, PyPI, crates, Go, Maven, RubyGems** — agnóstica por design |
| Registry do ecossistema | `npm view <pkg>@<ver> deprecated`; `pypi.org/pypi/<pkg>/json` (`yanked`, `yanked_reason`) | pacote deprecated/yanked na versão exatamente pinada |
| Tooling nativo | `npm outdated`, `pip list --outdated` | distância da versão em uso |
| Doc/changelog oficial da versão em uso | fetch, último recurso | deprecations **de linguagem**, que registry nenhum reporta |

#### Gradação de evidência (determina se o finding pode ser reportado)

| Tier | Evidência | Reportável? |
|---|---|---|
| **A — observada** | warning emitido pelo runtime, com stack trace | Sim, com arquivo e linha |
| **B — declarada** | metadado de registry/advisory para a versão pinada | Sim, citando fonte + data |
| **C — documentada** | doc/changelog oficial da versão em uso | Sim, citando URL + data |
| **D — suspeita** | conhecimento prévio do modelo | **Não.** Promove a A/B/C por verificação, ou descarta |

A severidade segue o impacto (§4): pacote deprecated **com advisory de segurança** escala para
CRITICAL/HIGH; API soft-deprecated sem risco fica MEDIUM/LOW.

#### Degradação declarada (consistente com D6.4)

Sem rede, a Camada 2 não roda. O relatório **declara** que a verificação upstream foi pulada e o
que deixou de ser coberto — nunca omite silenciosamente. `--offline` força esse modo.

---

### D14 — Re-auditoria obrigatória e a linha que precisa ser merecida ✅ decidido

O exemplo de saída do enunciado (`instructions.md` L107) encerra a Fase 3 com
`✓ Zero anti-patterns remaining`. A skill **não** imprime essa linha por decreto.

**Contexto — por que a frase é um problema.** Ela não afirma "corrigi o que achei"; afirma que
**não resta nenhum** — uma universal negativa. Só uma nova auditoria completa a sustenta. E sob o
gate de contrato (D7), se um único item ficou em `PROPOSED, NOT APPLIED`, restam anti-patterns por
construção, listados poucas linhas abaixo no mesmo relatório. Imprimir "zero" ali seria o documento
se contradizendo dentro de uma tela. O mesmo vale para a opção `CRITICAL+HIGH only` (D10.1).

**Decisão, em duas partes:**

1. **A re-auditoria vira passo obrigatório da Fase 3** (3d): re-executar a auditoria da Fase 2
   sobre o alvo refatorado, com o mesmo catálogo. É o único fato que licencia qualquer afirmação
   sobre o que restou.
2. **O resultado sempre ocupa uma linha** no bloco `## Validation`, em uma de três formas:

```
  ✓ Zero anti-patterns remaining  (re-audit: 0 findings)
  ○ Anti-patterns remaining: <k> proposed-not-applied, <u> unresolved  (re-audit: <m> findings)
  ⚠ Re-audit partial — see Verification Coverage  (<m> findings over the checks that ran)
```

**Separação obrigatória de dois fatos distintos:** `proposed-not-applied` é decisão tomada de
propósito e justificada; `unresolved` é transformação que falhou ou problema que a refatoração
introduziu. Colapsar em um número só esconde justamente o que exige ação.

**Restrições:** a primeira forma exige re-auditoria **completa** retornando zero — não "zero
inesperados". Re-auditoria parcial (ex.: `--offline`, sem a consulta viva do D13) nunca a produz:
cobertura reduzida não sustenta afirmação de ausência.

**Por quê:** é a afirmação mais forte do relatório e a mais barata de imprimir. Um `✓` de template
custa zero e não carrega informação — pior, ensina o leitor a desconfiar dos outros `✓` também.
Aplicação direta do princípio emergente (§8, fecho): a skill nunca degrada em silêncio, e o output
nunca mente para o usuário.

**Risco de avaliação, verificado e baixo:** a string aparece **uma única vez** em
`instructions.md` (L107), dentro do bloco ilustrativo "Exemplo de Uso no CLI". Não consta do
checklist de validação avaliado (cujos itens de Fase 3 são estrutura MVC, config extraída, models,
views/routes, controllers, error handling centralizado, entry point, app inicia, endpoints
respondem) nem dos Critérios de Aceite. A forma escolhida preserva o vocabulário do exemplo nos
três casos, então o avaliador reconhece o padrão sem que nada seja afirmado sem verificação.

**Arquivos afetados:** `SKILL.md` §3d e bloco de saída da Fase 3;
`references/03-report-template.md` §"The re-audit line"; `README.md` §B, Desafio 4.

**D14.1 — Emenda da rodada 2.** (a) `Findings resolved` tem exatamente três baldes, que somam o
total: `resolved`, `proposed`, `unresolved`. **Não existe "parcial".** Um finding com qualquer
parte restante é `unresolved` (ou `proposed`, se o resto é o que o gate segurou), e a descrição diz
o que foi e o que não foi corrigido. (b) Cada `unresolved` da re-auditoria carrega sua origem:
`failed`, `introduced` ou `missed-in-phase-2`. A última mede o recall da Fase 2, não a refatoração.

---

### Decisões da rodada 2 (D15–D18)

> Tomadas depois de ler `docs/rounds/round1-report.md` e antes do gabarito, sem ler o código dos
> projetos. Lista congelada em `docs/rounds/round2-changes.md` antes de qualquer edição. ADRs completos
> em `docs/decisions.md`.

### D15 — Autorização e validação: **teste do uso legítimo** ✅ decidido

Pergunta que decide: *quem recebe a nova rejeição?* Sem modelo de identidade, todo cliente atual
receberia o `401`: é mudança de contrato e vira proposta. Com identidade, mas sem checagem de dono
ou papel, só o uso ilegítimo é rejeitado: é seguro e é aplicado. Valor inválido em si mesmo é
rejeitado; regra que exige decisão de produto é proposta. Na dúvida, propõe. É a regra da D7 para
SQL injection escrita por extenso. Resolve a contradição entre `SKILL.md` e guidelines §6/RP-04
(problema #6).

### D16 — O original roda de um **snapshot intocado**, fora do alvo ✅ decidido

No início da Fase 2, o alvo é copiado para um diretório temporário. Toda execução do **original**
(deprecation na Fase 2, baseline, captura tardia) roda numa cópia nova desse snapshot. A aplicação
refatorada roda no alvo. A regra de escrita da D5/D10 fica absoluta, e artefatos de runtime nunca
tocam o alvo antes do gate. Porta: override existente → porta nativa em sequência → launcher fora
da árvore. O original nunca é editado. Resolve os problemas #1, #3 e #12.

### D17 — **Entradas de segurança** na superfície ✅ decidido

`kind: "security"`, com `finding: "AP-xx"` obrigatório e `expect: "rejected"`. Resultados:
`FIXED` / `NOT FIXED` / `REGRESSION` / `UNVERIFIED`. Nunca viram `REGRESSION` só por mudar de
status. Rodam depois das entradas de contrato. `NOT FIXED` num finding contado como resolvido move
o finding para `unresolved`. Resolve o problema #9.

### D18 — Upgrade de dependência versus contrato ✅ decidido

Patch ou minor dentro da major: seguro. Major, ou changelog com mudança de comportamento: seguro
só se o replay cobrir o que muda. Senão, proposta. O protocolo passa a comparar headers de contrato
(`Location`, `WWW-Authenticate`, `Access-Control-*`, nomes de `Set-Cookie`). Resolve o problema #10.

---

## 9. Perguntas em aberto

Nenhuma. D1–D18 decididas. Rodada 2: mudanças da skill aplicadas em `feat/round2`, aguardando
o gabarito (sessão cega, `docs/gabarito-prompt.md`) e a execução da rodada.

---

## 10. Convenções desta sessão de trabalho

- **Sessão educativa:** toda decisão de projeto é discutida antes de ser implementada —
  trade-offs explícitos, não só o resultado.
- Nenhuma análise dos 3 projetos entra na skill como caso concreto (§2).
- Este `CLAUDE.md` é o documento vivo do projeto: novas decisões são registradas aqui.
