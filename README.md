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
├── CLAUDE.md                              # especificação viva do projeto (D1–D14)
│
├── .claude/skills/refactor-arch/          # ← A SKILL (fonte única da verdade, D2)
│   ├── SKILL.md                           #   orquestração das 3 fases
│   ├── references/
│   │   ├── 01-project-analysis.md         #   heurísticas de detecção (Fase 1)
│   │   ├── 02-antipattern-catalog.md      #   catálogo de 17 anti-patterns (Fase 2)
│   │   ├── 03-report-template.md          #   formato normativo do relatório (Fase 2)
│   │   ├── 04-architecture-guidelines.md  #   arquitetura alvo e gate de contrato (Fase 3)
│   │   ├── 05-refactoring-playbook.md     #   16 transformações antes/depois (Fase 3)
│   │   └── 06-validation-protocol.md      #   protocolo normativo de validação (Fase 3)
│   └── scripts/
│       ├── probe.py                       #   harness de referência — Python stdlib
│       └── probe.mjs                      #   harness de referência — Node, zero deps
│
├── docs/                                  # artefatos de processo (nossos, fora do exigido)
│   ├── decisions.md                       #   registro ADR das decisões D1–D14
│   ├── rounds/                            #   relatório consolidado de cada rodada
│   ├── runs/                              #   PENDENTE — transcript de cada rodada (D3)
│   └── evals/                             #   PENDENTE — rubrica e scorecards (D8)
│
├── code-smells-project/                   # Projeto 1 — campo de prova
├── ecommerce-api-legacy/                  # Projeto 2 — campo de prova
├── task-manager-api/                      # Projeto 3 — campo de prova
│
├── reports/                               # PENDENTE — saída da Fase 2 de cada projeto
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

> ## ⚠️ PENDENTE — deliberadamente vazio neste momento
>
> **O que esta seção vai conter:** a análise manual dos três projetos, com no mínimo 5 problemas por
> projeto (≥1 CRITICAL ou HIGH, ≥2 MEDIUM, ≥2 LOW), cada um com arquivo, linhas, severidade e a
> justificativa de por que importa.
>
> **De que ela depende:** de uma sessão de trabalho **separada**, que nunca tenha lido o catálogo de
> anti-patterns, executada **depois** de o catálogo estar congelado e commitado (decisão **D12**).
>
> **Por que está vazia e não apenas inacabada:** esta análise é o **gabarito** contra o qual a skill
> será medida (D8). Catálogo e gabarito precisam ser mutuamente independentes, senão as métricas
> mentem — e mentem nas duas direções:
>
> - *gabarito primeiro* → o catálogo nasce enviesado, contendo só as categorias que o autor por acaso
>   viu nestes três projetos. Essa contaminação não aparece como nome de arquivo (que a regra
>   anti-overfitting pega); aparece na **escolha das categorias incluídas**, que nenhuma revisão
>   detecta;
> - *catálogo e gabarito na mesma sessão* → o gabarito é que nasce enviesado: encontra-se exatamente
>   o que o catálogo manda procurar, o recall infla para ~100% e a métrica-chave (*achados além do
>   gabarito*) vira zero por construção.
>
> Preencher esta seção agora — por estimativa, por extrapolação ou por leitura antecipada dos
> projetos — destruiria a medição na origem. **Depois de ler um projeto, não há como desler.**
>
> Enquanto estiver marcada assim, nenhuma linha abaixo é resultado.

### A.1 — `code-smells-project/` (Python / Flask)

| # | Severidade | Problema | Arquivo:linhas | Por que é relevante |
|---|---|---|---|---|
|   |            |          |                |                     |

### A.2 — `ecommerce-api-legacy/` (Node.js / Express)

| # | Severidade | Problema | Arquivo:linhas | Por que é relevante |
|---|---|---|---|---|
|   |            |          |                |                     |

### A.3 — `task-manager-api/` (Python / Flask)

| # | Severidade | Problema | Arquivo:linhas | Por que é relevante |
|---|---|---|---|---|
|   |            |          |                |                     |

### A.4 — Cobertura mínima exigida pelo enunciado

| Projeto | ≥1 CRITICAL/HIGH | ≥2 MEDIUM | ≥2 LOW | Total ≥5 |
|---|---|---|---|---|
| `code-smells-project` | — | — | — | — |
| `ecommerce-api-legacy` | — | — | — | — |
| `task-manager-api` | — | — | — | — |

---

## B) Construção da Skill

### B.1 — Estrutura dos arquivos e *progressive disclosure*

A skill tem nove arquivos, com uma divisão de papéis deliberada:

| Arquivo | Papel | Quando é lido |
|---|---|---|
| `SKILL.md` | **Orquestra.** Contrato de invocação, sequência das fases, formato exato dos blocos impressos, o gate, as regras invioláveis. | Sempre, inteiro |
| `references/01-project-analysis.md` | Heurísticas de detecção: linguagem, framework, dependências, banco, tipo de aplicação, superfície pública, comando de boot | Início da Fase 1 |
| `references/02-antipattern-catalog.md` | Catálogo de 17 anti-patterns, com sinais observáveis e regras de severidade | Início da Fase 2 |
| `references/03-report-template.md` | Formato normativo do relatório e regras de cada campo | Ao escrever o relatório |
| `references/04-architecture-guidelines.md` | Arquitetura alvo, direção de dependências, teste "camada real ou nominal", gate de contrato público | Ao planejar a Fase 3 |
| `references/05-refactoring-playbook.md` | 16 transformações concretas com código antes/depois | A cada transformação |
| `references/06-validation-protocol.md` | Spec normativa da validação baseline-then-replay | Fase 3a e sempre que a validação degradar |
| `scripts/probe.py`, `scripts/probe.mjs` | Implementações de referência do protocolo | Fase 3a, ou como base para gerar outra |

**O SKILL.md é um prompt; os arquivos de referência são conhecimento de domínio.** Essa separação
não é estética: o SKILL.md entra inteiro no contexto toda vez que a skill é invocada, enquanto os
arquivos de referência são carregados sob demanda, na fase que precisa deles. Por isso o SKILL.md
tem ~230 linhas e o playbook tem ~1.160: o custo de contexto de cada um é pago em momentos
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

**17 anti-patterns** (o enunciado exige ≥8), extraídos de literatura — Fowler (*Refactoring*),
Feathers (*Working Effectively with Legacy Code*), os princípios SOLID e o OWASP Top 10 — e não dos
projetos-alvo.

| Severidade default | Ids | Entradas |
|---|---|---|
| **CRITICAL** (4) | AP-01 … AP-04 | Hardcoded Secrets · Injection-Prone Dynamic Query · God Module / God Class · Missing or Bypassable Authorization |
| **HIGH** (5) | AP-05 … AP-09 | Business Logic in the Delivery Layer · Hard-Wired Dependencies / No Composition Root · Mutable Global State · Unsafe Handling of Credentials · Swallowed or Uncentralized Error Handling |
| **MEDIUM** (5) | AP-10 … AP-14 | N+1 / Query-Inside-Loop · Missing Boundary Validation · Duplicated Logic · Unbounded Resources and Leaked Handles · Deprecated or End-of-Life API Usage |
| **LOW** (3) | AP-15 … AP-17 | Magic Values · Misleading Names and Inconsistent Structure · Dead Code and Commented-Out Code |

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

O **playbook** espelha o catálogo com **16 transformações** (o enunciado exige ≥8), com exemplos de
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
que a seção A deste documento ainda está vazia.

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

> ## ⚠️ PENDENTE — nenhuma execução ocorreu
>
> **O que esta seção vai conter:** o resumo dos relatórios de auditoria dos três projetos (findings
> por severidade), a comparação antes/depois da estrutura de cada um, o checklist de validação
> preenchido por projeto, os logs das aplicações rodando após a refatoração e as observações sobre o
> comportamento da skill em stacks diferentes.
>
> **De que ela depende:** de **executar a skill nos três projetos** — o que ainda não aconteceu.
> **Zero rodadas foram realizadas.** Depende também da seção A, porque as métricas de recall e de
> *achados além do gabarito* (D8) só existem contra um gabarito.
>
> **Por que está vazia e não apenas inacabada:** qualquer número aqui que não venha de uma execução
> real é invenção — e este projeto inteiro existe para medir quanto uma skill generaliza. Estimar
> contagens de findings, desenhar uma árvore de diretórios "provável" ou marcar um checkbox de
> validação sem ter observado o check passar destruiria a metodologia de medição (D8) na origem, e
> seria precisamente a degradação silenciosa que o princípio de B.5 proíbe — aplicada à própria
> documentação do projeto.
>
> **Nenhuma caixa abaixo está marcada, e nenhuma célula abaixo contém resultado.**

### C.1 — Resumo dos relatórios de auditoria

| Projeto | Stack | Arquivos | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
|---|---|---|---|---|---|---|---|---|
| 1 — `code-smells-project` | Python / Flask | — | — | — | — | — | — | `reports/audit-project-1.md` |
| 2 — `ecommerce-api-legacy` | Node.js / Express | — | — | — | — | — | — | `reports/audit-project-2.md` |
| 3 — `task-manager-api` | Python / Flask | — | — | — | — | — | — | `reports/audit-project-3.md` |

Modo de cada rodada (D10 / D10.1 — obrigatório para que uma rodada parcial não seja lida como
completa):

| Projeto | `Mode` (full / `--offline`) | `Confirmation` | Escopo aplicado | `Verification Coverage` |
|---|---|---|---|---|
| 1 | — | — | — | — |
| 2 | — | — | — | — |
| 3 | — | — | — | — |

### C.2 — Projeto 1 — `code-smells-project` (Python / Flask)

**Estrutura antes → depois**

```
(antes — a preencher a partir da Fase 1 da rodada)
```

```
(depois — a preencher a partir do bloco "New Project Structure" da Fase 3)
```

**Validação comportamental (D4 — baseline-then-replay)**

| PASS | REGRESSION | PRE-EXISTING FAILURE | UNVERIFIED |
|---|---|---|---|
| — | — | — | — |

**`PROPOSED, NOT APPLIED` (gate de contrato, D7):** —

**Logs da aplicação após a refatoração**

```
(a preencher com a saída real do boot e do replay)
```

**Checklist de Validação**

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

### C.3 — Projeto 2 — `ecommerce-api-legacy` (Node.js / Express)

**Estrutura antes → depois**

```
(antes — a preencher a partir da Fase 1 da rodada)
```

```
(depois — a preencher a partir do bloco "New Project Structure" da Fase 3)
```

**Validação comportamental (D4 — baseline-then-replay)**

| PASS | REGRESSION | PRE-EXISTING FAILURE | UNVERIFIED |
|---|---|---|---|
| — | — | — | — |

**`PROPOSED, NOT APPLIED` (gate de contrato, D7):** —

**Logs da aplicação após a refatoração**

```
(a preencher com a saída real do boot e do replay)
```

**Checklist de Validação**

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

### C.4 — Projeto 3 — `task-manager-api` (Python / Flask)

**Estrutura antes → depois**

```
(antes — a preencher a partir da Fase 1 da rodada)
```

```
(depois — a preencher a partir do bloco "New Project Structure" da Fase 3)
```

**Validação comportamental (D4 — baseline-then-replay)**

| PASS | REGRESSION | PRE-EXISTING FAILURE | UNVERIFIED |
|---|---|---|---|
| — | — | — | — |

**`PROPOSED, NOT APPLIED` (gate de contrato, D7):** —

**Camadas existentes: reais ou nominais?** (teste de `04-architecture-guidelines.md` §5) — a preencher.

**Logs da aplicação após a refatoração**

```
(a preencher com a saída real do boot e do replay)
```

**Checklist de Validação**

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

### C.5 — Critérios de aceite do enunciado (3/3 obrigatório)

| Critério | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| Fase 1 detecta a stack corretamente | — | — | — |
| Fase 2 encontra ≥ 5 findings | — | — | — |
| Fase 2 inclui ≥ 1 CRITICAL ou HIGH | — | — | — |
| Fase 3 — aplicação funciona após a refatoração | — | — | — |

### C.6 — Métricas de generalização (D8)

Preenchidas a partir de `docs/evals/run-p<N>-iter<K>.md`, só depois de a seção A existir.

| Métrica | O que responde | P1 | P2 | P3 |
|---|---|---|---|---|
| Recall vs. análise manual | Dos problemas que eu sei que existem, quantos ela achou? | — | — | — |
| Falsos positivos | Quantos findings apontam para código correto? | — | — | — |
| Findings inventados | Quantos citam arquivo/linha que não existe ou não contém aquilo? | — | — | — |
| **Achados além do gabarito** | Quantos problemas legítimos ela achou que **não** estavam na análise manual? | — | — | — |
| Regressões pós-refactor | Quantas entradas divergiram do baseline? | — | — | — |
| Intervenções humanas | Quantas vezes precisei corrigir o rumo? | — | — | — |

*Achados além do gabarito* é a métrica-chave: recall alto é trivialmente manipulável (basta escrever o
catálogo a partir da análise manual para reencontrar 100% do que foi plantado), enquanto essa métrica
mede o oposto — a capacidade de ver o que o autor do catálogo não viu. *Findings inventados* é sua
contramétrica indispensável: sem ela, "achou 30 problemas" seria recompensado mesmo com 12
alucinações.

### C.7 — Comportamento em stacks diferentes

A preencher após as três rodadas.

---

## D) Como Executar

### D.1 — Pré-requisitos

| Requisito | Detalhe |
|---|---|
| **Claude Code** | Instalado e autenticado. É a ferramenta escolhida entre as três aceitas pelo enunciado. |
| **Git** | A skill assume que o alvo está versionado: a reescrita in-place (D9) usa o histórico como rede de segurança. |
| **Runtime do alvo** | Python 3.8+ para alvos Python, Node 18+ para alvos Node. O harness roda no runtime do próprio alvo — **nada é instalado** para validar. |
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
2. A linha de replay: `<P> PASS, <R> REGRESSION, <F> PRE-EXISTING FAILURE, <U> UNVERIFIED`.
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

**8. As contagens desta entrega ainda não existem.** As seções A e C estão vazias por decisão (D12) e
por ausência de execuções, respectivamente. Enquanto estiverem assim, **nada neste documento prova
que a skill funciona nos três projetos** — apenas que ela foi construída para isso, e como. A skill
descreve o que verificou; esta seção descreve o que a entrega ainda não verificou.

---

## Referências deste repositório

| Documento | O que é |
|---|---|
| [`instructions.md`](instructions.md) | O enunciado original do desafio, **preservado sem alterações** (era o `README.md` do repositório base). É a fonte da verdade sobre o que foi pedido. |
| [`docs/decisions.md`](docs/decisions.md) | Registro ADR completo de D1–D14: contexto, alternativas rejeitadas, custos aceitos e as duas reversões (D6 e D13), com o caminho que levou a cada forma final. |
| [`CLAUDE.md`](CLAUDE.md) | Especificação viva do projeto: requisitos extraídos do enunciado, escala de severidade canônica, contratos de saída das fases e o resumo das decisões. |
| [`.claude/skills/refactor-arch/`](.claude/skills/refactor-arch/) | A skill em si — o entregável. |
