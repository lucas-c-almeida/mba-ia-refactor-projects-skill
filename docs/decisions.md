# Registro de Decisões Arquiteturais — Skill `refactor-arch`

> Documento de histórico e argumentação. Fonte: `CLAUDE.md` (§1–§10, decisões D1–D14) e
> `instructions.md` (enunciado original do desafio).
>
> `CLAUDE.md` é a **especificação do estado atual** — diz o que é verdade hoje.
> Este documento é a **história e o argumento** — diz o que foi considerado, o que foi
> escolhido, o que foi recusado e quanto custou. Onde os dois divergirem, `CLAUDE.md` é a
> autoridade sobre o *quê*; este documento é a autoridade sobre o *porquê*.

---

## 1. Enquadramento

### 1.1 O que é este projeto

O entregável deste desafio **não é código refatorado**. É uma **Skill** — `refactor-arch` —
capaz de analisar, auditar e refatorar uma codebase qualquer para o padrão MVC, de forma
agnóstica de tecnologia. Os três projetos fornecidos no repositório base são **campo de
prova**, não produto: o código refatorado deles é subproduto da execução da skill e serve
como evidência de que ela funciona.

Essa distinção não é retórica. Ela muda o que conta como sucesso. Se o entregável fosse
código refatorado, a pergunta seria *"esses três projetos ficaram bons?"* — e a resposta
ótima seria resolver os três à mão, com conhecimento específico de cada um. Como o
entregável é a skill, a pergunta passa a ser *"essa ferramenta funcionaria num quarto
projeto que ninguém viu?"* — e qualquer atalho que melhore os três às custas do quarto é
uma regressão disfarçada de progresso. Os critérios de aceite do enunciado reforçam isso
ao exigir sucesso nos **3/3**, e não em um: um resultado que só vale para uma stack não
demonstra nada sobre a skill.

### 1.2 A restrição governante: a skill não pode ser *overfitted*

O autor do repositório fixou, antes de qualquer outra coisa, a restrição que governa o
projeto inteiro (§2 de `CLAUDE.md`): a skill — `SKILL.md` e arquivos de referência — nunca
pode conter nome de arquivo, função, rota, tabela, variável ou constante dos projetos-alvo;
nem descrição de um bug concreto encontrado neles; nem contagem esperada de findings; nem
heurística que só faça sentido em uma das três codebases.

A regra positiva que substitui a proibição é: **descrever o sinal observável e o raciocínio,
não a instância**. O contraste que `CLAUDE.md` usa para ensinar isso — reproduzido aqui
apenas como *exemplo do que não escrever*, e por isso citando nomes dos projetos-alvo em um
contexto de proibição:

| ❌ Acoplado (exemplo do que **não** escrever) | ✅ Generalizável |
|---|---|
| "Procure pela `SECRET_KEY` hardcoded em `app.py`" | Literal string atribuída a identificador cujo nome casa com `(secret\|key\|token\|password\|credential\|api_key\|dsn\|conn_str)`, fora de arquivo de exemplo/teste |
| "O `AppManager.js` é uma God Class" | Um único módulo concentra ≥3 responsabilidades distintas (persistência, regra de negócio, roteamento/IO, formatação) **ou** excede ~300 linhas com ≥2 delas |
| "Corrigir a query N+1 do endpoint de pedidos" | Chamada a driver de banco (`execute`/`query`/`find`) dentro de corpo de laço, ou em função chamada dentro de laço |

O critério de aceite interno derivado dessa regra é o **Teste do Quarto Projeto**: de cada
linha da skill, perguntar *"isso continuaria correto e útil se o alvo fosse um projeto
Ruby/Rails ou Go que eu nunca vi?"*. Se não, a linha está acoplada.

Essa restrição é a causa direta de quase todas as decisões deste documento. Ela determina
a ordem de trabalho (D12), o formato da validação (D6), o tratamento de APIs deprecated
(D13), a métrica que importa (D8), o escopo do alvo arquitetural (D11) e até onde a skill
escreve seus relatórios (D5). Quando duas decisões entraram em conflito, o desempate
quase sempre veio daqui — inclusive contra a conveniência imediata dos três alvos.

O corolário de método vale registrar porque inverte a ordem sugerida pelo enunciado: a
análise manual dos três projetos existe para **calibrar** o catálogo — confirmar que as
categorias existem no mundo real e medir recall — e **não** para populá-lo. O catálogo
nasce de literatura de anti-patterns (Fowler/*Refactoring*, SOLID, OWASP); a análise manual
só verifica cobertura.

### 1.3 Como ler este documento

Cada decisão aparece em forma de ADR: **Contexto** (o problema que forçou a escolha),
**Decisão** (o que foi escolhido), **Justificativa** (por quê — é a parte que importa),
**Alternativas rejeitadas** (o que mais estava na mesa e por que perdeu) e **Custo aceito /
consequências** (o que a decisão torna mais difícil, e que decisões posteriores ela
restringe).

Duas decisões — **D6** e **D13** — foram tomadas, desafiadas e **revertidas** durante o
desenho. Elas trazem uma seção adicional, *Reversão*, com a posição original, o desafio
levantado, a falha exposta, a resolução e a lição geral. São o conteúdo mais instrutivo do
registro, e foram mantidas com a história inteira em vez de reescritas na forma final:
o erro é o que explica a regra.

O documento fecha com uma seção sobre um princípio que **não foi desenhado de antemão** e
convergiu de quatro decisões independentes (§4), e uma nota sobre as duas armadilhas de
medição que o projeto se protege (§5).

---

## 2. Índice de decisões

| # | Título | Em uma linha |
|---|---|---|
| **D1** | Idioma: inglês integral | A skill e seus relatórios são escritos em inglês, rótulos inclusive |
| **D2** | Fonte da verdade: cópia única na raiz | Uma só cópia canônica da skill; as três cópias exigidas são sincronizadas na entrega |
| **D3** | Isolamento entre rodadas | Sessão limpa + tag git + transcript por rodada, contra contaminação de contexto |
| **D4** | Validação da Fase 3: baseline antes + replay depois | *Characterization test*: gravar o comportamento original e comparar depois |
| **D5** | Relatório da Fase 2 dentro do alvo, com histórico | A skill escreve em `<alvo>/reports/`, sem conhecer o layout deste repositório |
| **D6** | Validação: protocolo normativo + harness no runtime do alvo | *(revertida)* Markdown normativo; o harness roda no runtime que o alvo já tem |
| **D7** | Fase 3 corrige tudo, com gate de contrato | Toda severidade é corrigida; mudança de contrato público é proposta, não aplicada |
| **D8** | Scorecard formal com métricas de generalização | *Achados além do gabarito* é a métrica-chave; *findings inventados* é a contramétrica |
| **D9** | Arquivos originais: reescrita in-place | O código antigo é removido; o backup é o git |
| **D10** | Confirmação da Fase 2 obrigatória, com escape | Pausa `[y/n]` ON por padrão; `--yes` para calibração, com o modo registrado |
| **D11** | Escopo genérico por superfície pública | Não só HTTP: rotas, comandos, API exportada ou mensagens são a mesma abstração |
| **D12** | Catálogo cego primeiro, gabarito em sessão separada | Escrever o catálogo sem ter lido nenhum alvo; a análise manual vem depois |
| **D13** | APIs deprecated: evidência viva, nunca lista estática | *(revertida)* A skill sabe onde perguntar; não pode saber a resposta |
| **D14** | Re-auditoria obrigatória ao final da Fase 3 | A linha `Zero anti-patterns remaining` só é impressa se uma re-auditoria completa retornar zero |
| **D15** | Autorização e validação: teste do uso legítimo | Rejeitar o que só clientes ilegítimos mandam é seguro; rejeitar clientes legítimos é proposta *(rodada 2)* |
| **D16** | O original roda de um snapshot intocado | Toda execução do original acontece numa cópia fora do alvo; a regra de escrita da Fase 2 fica absoluta *(rodada 2)* |
| **D17** | Entradas de segurança na superfície | Entrada hostil que deve mudar tem estado próprio: `FIXED` / `NOT FIXED`, nunca `REGRESSION` *(rodada 2)* |
| **D18** | Upgrade de dependência versus contrato | Dentro da major, seguro; fora dela, só se o replay cobrir o que muda *(rodada 2)* |
| **D19** | Isolamento de execução: container primeiro | Toda execução roda num container nomeado e descartável; sem container, modo host declarado; nunca encerrar por nome *(rodada 3)* |
| **D20** | Ferramenta de ciclo de vida separada do probe | `proc` sobe o comando que o agente derivou e encerra só a árvore que criou (emenda à D6.1) *(rodada 3)* |
| **D21** | Entrada de segurança neutralizada | Correção que muda a resposta sem rejeitar é `FIXED` quando o shape bate com o de uma entrada benigna irmã *(rodada 3)* |
| **D22** | O contrato de erro | São contrato o status e o shape dos erros intencionais; a página padrão do framework não é *(rodada 3)* |
| **D23** | Laço de correção limitado | Um replay completo; no máximo duas passadas de re-auditoria; `missed-in-phase-2` corrigido é contado à parte *(rodada 3)* |

---

## 3. As decisões

### D1 — Idioma: inglês integral

**Contexto.** O enunciado é em português e seu exemplo de saída mistura rótulos em inglês
(`PHASE 1: PROJECT ANALYSIS`, `[CRITICAL]`, `File:`, `Description:`) com prosa em português
nas descrições dos findings. O projeto precisava escolher um idioma para o `SKILL.md`, para
os arquivos de referência e para a saída dos relatórios, e a escolha tem efeito direto na
qualidade da detecção, não só na estética.

**Decisão.** Inglês integral: `SKILL.md`, arquivos de referência e relatórios de auditoria,
incluindo os rótulos estruturais. A documentação *sobre* o projeto — `CLAUDE.md` e este
documento — permanece em português.

**Justificativa.** Três razões, em ordem de peso.

Primeira, os nomes canônicos dos anti-patterns são em inglês. Traduzir *God Class* para
*Classe Deus* afasta o leitor da literatura, da busca e do vocabulário que ele vai
encontrar em qualquer ferramenta de análise estática. Um catálogo é útil na medida em que
seus termos são pesquisáveis.

Segunda, e mais alinhada à restrição governante: uma skill agnóstica de tecnologia também
deveria ser agnóstica do idioma do time que a usa. Português no `SKILL.md` acopla a skill a
um público, do mesmo jeito que um nome de arquivo a acopla a um projeto — é a mesma classe
de erro, em outro eixo.

Terceira, o vocabulário do modelo para conceitos de arquitetura é mais preciso em inglês.
A skill é, no fim, um prompt; escrevê-la no idioma em que os conceitos são mais densos
melhora a detecção.

**Alternativas rejeitadas.**
- *Português integral* — perderia a correspondência com a literatura e acoplaria a skill a
  um time lusófono.
- *Híbrido, como no exemplo do enunciado* (rótulos em inglês, prosa em português) — é o que
  o exemplo faz, mas mistura idiomas dentro do mesmo artefato sem ganho; e a parte que o
  avaliador verifica estruturalmente são justamente os rótulos, que já são inglês.

**Custo aceito / consequências.** A prosa dos relatórios diverge do exemplo em português do
enunciado; o que é preservado é o **formato estrutural**, que é o que o checklist de
validação cobra. O avaliador lê em português e recebe artefatos em inglês — este documento
e o `README.md` de entrega existem em português em parte para fazer essa ponte. A decisão
se propaga para D5 (os arquivos copiados para `reports/` na raiz estarão em inglês) e para
o contrato de saída de §5 de `CLAUDE.md`.

---

### D2 — Fonte da verdade: cópia única na raiz

**Contexto.** O enunciado exige a skill presente em `.claude/skills/refactor-arch/` **dentro
de cada um dos três projetos**, e descreve o fluxo como "copiar a pasta para o próximo
projeto". Seguido ao pé da letra durante o desenvolvimento, isso produz três cópias vivas
do mesmo artefato, editadas em momentos diferentes, cada uma sob a pressão do projeto em
que está.

**Decisão.** A skill canônica vive em **uma única cópia**, em `.claude/skills/refactor-arch/`
na raiz do repositório. As execuções acontecem a partir da raiz, projeto por projeto. Não se
mantém uma quarta cópia em um diretório-fonte separado.

**Justificativa.** Uma cópia só é a garantia **estrutural** contra divergência: não existe
"a versão do projeto 2" para ajustar sob pressão quando uma rodada vai mal. Isso é o ponto
central — transforma o anti-overfitting de **disciplina** (que depende de o autor resistir à
tentação) em **propriedade do repositório** (que não depende de ninguém). A restrição de §2
proíbe escrever conteúdo acoplado; manter três cópias editáveis tornaria o acoplamento
*possível sem ser visível*, porque cada cópia pareceria genérica isoladamente e só o
conjunto denunciaria a especialização.

**Alternativas rejeitadas.**
- *Três cópias vivas, sincronizadas manualmente* — o fluxo literal do enunciado. Rejeitado
  porque convida exatamente ao ajuste local que a restrição governante proíbe, e porque
  "sincronizar manualmente" é um passo que falha em silêncio.
- *Quarta cópia em um `skill-source/`* — acrescenta um artefato a manter sem resolver nada
  que a cópia na raiz já não resolva; mais um lugar onde a verdade pode divergir.

**Consequência de design obrigatória (D2.1).** Como o agente roda a partir da raiz e não de
dentro do projeto, a skill **não pode assumir que o alvo é o diretório corrente**. O
`SKILL.md` aceita um diretório-alvo opcional e usa o CWD como padrão:

```
/refactor-arch                      # alvo = diretório corrente
/refactor-arch <subdiretorio>       # alvo = subdiretório informado
```

Isso não é uma concessão ao nosso layout — é generalização. Um projeto real é subdiretório
de um monorepo com a mesma frequência com que é a raiz de um checkout. Escopar o alvo
explicitamente deixa a skill **mais** genérica, e faz com que todo path em relatório e
validação passe a ser relativo ao alvo, nunca ao CWD.

**Consequência operacional (D2.2).** Na entrega, um passo de sync copia a skill para dentro
dos três projetos, cumprindo a estrutura exigida. A cópia é feita **uma vez, ao final**,
nunca durante a iteração.

**Custo aceito / consequências.** Durante todo o desenvolvimento, o repositório **não**
exibe a estrutura que o enunciado descreve — as três cópias só existem depois do sync final,
e esquecer esse passo significa entregar fora da especificação. A decisão também acrescenta
um parâmetro à superfície de invocação: como o enunciado cobra literalmente
`claude "/refactor-arch"` sem argumento, o default por CWD precisa continuar funcionando, e
os dois caminhos precisam ser testados. Por fim, D2.1 é o que torna possível D5 — todo path
relativo ao alvo — e D5 depende disso para não vazar o layout deste repositório para dentro
da skill.

---

### D3 — Isolamento entre rodadas: sessão limpa + tag git + transcript

**Contexto.** O enunciado avisa que 2–4 iterações por projeto são normais. Rodar a skill
várias vezes, em três projetos, ajustando o catálogo no meio, cria um risco silencioso: o
resultado de uma rodada pode vir da memória do agente sobre a rodada anterior, e não do
conteúdo da skill.

**Decisão.** Cada execução da skill em um projeto é uma **rodada**, e toda rodada é isolada
em três eixos:

| Eixo | Mecanismo | Contra o quê protege |
|---|---|---|
| Contexto | Sessão nova do agente por projeto (nunca os três na mesma) | O agente chegar no projeto seguinte já "sabendo" o que achar |
| Código | Tag git antes de cada rodada (`run/p<N>/iter<K>`) | Rodada não repetível; impossibilidade de re-testar após ajustar a skill |
| Evidência | Transcript salvo por rodada | Perder o *porquê* de uma regressão quando a sessão fecha |

**Justificativa.** O eixo de contexto é o mais importante justamente por ser **o único
invisível**. Um repositório sujo denuncia a falta de reset; uma sessão contaminada produz um
resultado que *parece* ótimo. Rodar os três projetos na mesma sessão mede a memória do
agente, não a qualidade do catálogo — e isso é overfitting **em tempo de execução**,
indistinguível, a partir do output, de uma skill genuinamente boa. Nenhuma revisão do
`SKILL.md` pegaria esse erro, porque o `SKILL.md` estaria limpo: o acoplamento estaria no
contexto da sessão. Os outros dois eixos são infraestrutura de repetibilidade: sem a tag,
ajustar a skill e rodar de novo não é o mesmo experimento; sem o transcript, a explicação de
uma regressão morre com a sessão.

**Alternativas rejeitadas.**
- *Uma sessão para os três projetos* — mais rápido e mais confortável, e exatamente o que
  invalida a medição.
- *Confiar no `git status` para saber o estado* — cobre o eixo de código e ignora os outros
  dois; o problema não é o repositório estar sujo, é o contexto estar carregado.

**Custo aceito / consequências.** Atrito operacional real: três projetos × 2–4 iterações
significa até doze sessões frias, cada uma recomeçando do zero, sem reaproveitar nada do
raciocínio anterior. Toda melhoria da skill exige `reset` e nova rodada completa para valer
como evidência. A namespace de tags do repositório acumula marcas de processo, e os
transcripts precisam ser salvos com disciplina — é um passo manual, portanto falível. D3 é
pré-requisito de D8: sem rodadas isoladas e repetíveis, as métricas do scorecard não
comparam nada.

---

### D4 — Validação da Fase 3: baseline antes + replay depois

**Contexto.** O enunciado exige que a Fase 3 valide o resultado: "a aplicação inicia sem
erros" e "os endpoints originais continuam respondendo". A segunda afirmação parece
objetiva, mas não é: responder *o quê*? Um endpoint que já retornava erro antes da
refatoração continua retornando erro depois e passa como "continua respondendo".

**Decisão.** A skill captura, **antes** de escrever qualquer arquivo, um baseline
comportamental do projeto original; **depois** da refatoração, repete as mesmas chamadas
contra a aplicação nova e compara. O fluxo é: (1) inventário de pontos de entrada extraído
estaticamente do código original; (2) captura do baseline — sobe a aplicação original,
exercita cada ponto de entrada, grava status e a *forma* da resposta, não os dados voláteis;
(3) refatoração; (4) replay contra a aplicação refatorada e comparação. Divergência é
**regressão**, reportada explicitamente.

**Justificativa.** Isto é um *characterization test* no sentido de Michael Feathers
(*Working Effectively with Legacy Code*): num sistema sem testes, o que o código faz hoje é
a única especificação disponível, e registrá-lo é o que permite mudá-lo. Sem baseline, "os
endpoints respondem" é uma afirmação vazia — não há contra o quê comparar, e a validação
não consegue falhar, o que a torna decorativa. Com baseline, a validação passa a poder
falhar, e portanto passa a significar alguma coisa. Há ainda um efeito de segunda ordem
importante: o baseline é o que permite refatorar com agressividade (D7) sem apostar. Quem
não sabe o que o sistema fazia antes só pode mexer com timidez.

**Regra de honestidade.** Pontos de entrada que já falhavam no baseline são marcados
`PRE-EXISTING FAILURE`, não `✗`. A skill nunca relata como sucesso algo que não verificou, e
nunca imputa à refatoração um defeito que já existia. Esta regra é uma das quatro
convergências do princípio emergente de §4.

**Alternativas rejeitadas.**
- *Só verificar o boot* — literal demais ao enunciado; um app que sobe e responde 500 em
  tudo passaria.
- *Comparar valores de resposta, e não forma* — rejeitado em D6.5 pelo ruído; ids e
  timestamps mudam a cada rodada.
- *Escrever testes novos para o comportamento desejado* — mede o que queremos, não o que
  havia; não detecta regressão e exige conhecer o domínio de cada alvo, o que é acoplamento.

**Custo aceito / consequências.** Dobra-se o trabalho de execução: é preciso subir a
aplicação **original** antes de tocar em qualquer arquivo, e a refatorada depois. Se o
projeto original não sobe, não há baseline — e a validação já começa degradada (o que, por
§4, deve ser declarado). O inventário de pontos de entrada é extraído estaticamente e pode
ser incompleto: o que não for enumerado não é comparado, e essa lacuna é invisível no
relatório a menos que seja dita. D4 restringe duas decisões posteriores: **D7** (o gate de
contrato existe porque "não quebrei nada" só é verificável se o contrato for preservado) e
**D6** (a comparação precisa de um harness, e a escolha desse harness virou uma decisão por
si só).

---

### D5 — Relatório da Fase 2: dentro do alvo, com histórico

**Contexto.** O enunciado pede que o relatório da Fase 2 de cada projeto seja salvo em
`reports/audit-project-{1,2,3}.md` na raiz do repositório. A tentação óbvia é fazer a skill
escrever direto nesse caminho.

**Decisão.** A skill escreve `<alvo>/reports/audit-<YYYYMMDD-HHMM>.md` e atualiza
`<alvo>/reports/audit-latest.md`. Um passo de entrega copia o `audit-latest.md` de cada
projeto para `reports/audit-project-N.md` na raiz.

**Justificativa.** A skill **não pode conhecer o layout deste repositório**. Não existe
"project-1" no mundo; existe *um diretório que ela recebeu como alvo*. Saber que um certo
diretório é "o projeto 1" seria acoplamento estrutural ao enunciado — a mesma categoria de
erro que §2 proíbe, deslocada do conteúdo do catálogo para a convenção de nomes de arquivo.
A numeração é um fato sobre a entrega, não sobre o alvo, e por isso pertence ao passo de
entrega, feito por um humano que sabe qual projeto é qual. O timestamp existe para comparar
iterações, que é o insumo de D8.

**Alternativas rejeitadas.**
- *Escrever direto em `reports/audit-project-N.md` na raiz* — acopla a skill ao enunciado e
  ao layout deste fork; falharia no Teste do Quarto Projeto na primeira linha.
- *Sobrescrever sempre o mesmo arquivo dentro do alvo* — perde o histórico entre iterações,
  que é justamente o que D8 precisa para medir progresso.

**Ressalva registrada.** Escrever o relatório é escrita em disco **antes** da confirmação da
Fase 2. Isso não viola a regra de pausa, porque a regra proíbe modificar **arquivos do
projeto**, e `reports/` é artefato de auditoria, não código-fonte. O `SKILL.md` precisa
dizer isso explicitamente, para o agente não se autoparalisar diante da própria instrução:
*"Phase 2 may write only to `<target>/reports/`. No file outside it may be created, modified
or deleted before the user confirms."* Vale notar o que está acontecendo aqui — uma regra de
segurança formulada de forma absoluta ("não escreva nada") teria bloqueado o próprio
entregável; a formulação correta precisa nomear o perímetro, não a ação.

**Custo aceito / consequências.** Cada projeto-alvo passa a carregar um diretório
`reports/` que não estava previsto na estrutura do enunciado. O mapeamento
alvo → "projeto N" fica fora da skill, nas mãos de um humano, e é portanto um passo que pode
ser feito errado ou esquecido na entrega. E a ressalva acima exige uma linha explícita no
`SKILL.md` que, mal redigida, vira a brecha por onde a pausa de D10 deixa de ser respeitada.

---

### D6 — Validação: protocolo normativo + harness no runtime do alvo *(revertida)*

**Contexto.** D4 exige exercitar a superfície pública do alvo, gravar a forma das respostas
e comparar duas execuções. Isso é código — alguém tem que emitir as requisições e fazer o
diff estrutural. A pergunta é: *em que runtime esse código roda, numa skill que não sabe
qual é a stack do alvo?*

#### Reversão

**Posição original.** Um harness escrito em **Python**, com **fallback para `curl`** quando
Python não estivesse disponível.

**O desafio levantado.** Por que Python? A resposta honesta era: porque dois dos três
projetos-alvo são Flask.

**A primeira falha exposta.** Não há nada em "auditar uma codebase" que exija Python. A
escolha veio por reflexo, do conjunto de amostra — e num alvo Go ou Ruby ela vira uma
dependência arbitrária que o usuário precisa instalar para validar um projeto que não tem
nada a ver com Python. É **exatamente** o erro que §2 proíbe, cometido não no conteúdo do
catálogo, mas na **escolha da ferramenta**. O detalhe que torna o episódio instrutivo é
cronológico: o princípio anti-overfitting foi escrito como D-zero do projeto, e foi violado
três decisões depois, pelo próprio autor, sem que soasse errado na hora. Overfitting não se
apresenta como uma decisão de acoplar; apresenta-se como a escolha óbvia, e o que a torna
óbvia é a amostra que se tem na cabeça.

**A segunda falha exposta.** O "fallback" não era equivalente ao caminho principal. `curl`
emite requisições, mas **não faz diff estrutural de JSON** — isso exigiria `jq`, que é
*menos* disponível que Python ou Node. Na prática, o fallback degradava para paridade de
status code: uma verificação muito mais fraca, vendida com o mesmo nome. Era um **plano C
apresentado como plano B**. E o dano não é a fraqueza em si: é a fraqueza **não declarada**.
Um relatório dizendo "validado" significaria coisas diferentes conforme o ambiente, sem que
o leitor soubesse qual delas recebeu.

**A resolução.** Duas mudanças. O protocolo passou a ser um documento **normativo em
Markdown**, e o harness passou a rodar **no runtime do próprio alvo**, sob o princípio *"se
você consegue subir a aplicação, você tem um runtime no qual consegue escrever um script"*.
E o modo mais fraco deixou de ser um fallback silencioso: virou um **modo piso declarado**.

**A lição geral.** Overfitting não mora só no texto do catálogo — mora em toda escolha feita
"porque no nosso caso é assim". E um fallback só pode se chamar fallback se fizer a mesma
coisa; se faz menos, ele não é um caminho alternativo, é um resultado diferente com o mesmo
rótulo, e precisa de um rótulo próprio.

**Decisão (forma final).**

**D6.1 — Separação de responsabilidades.** O harness **não sobe a aplicação**. Subir é
específico de stack; sondar é protocolo puro.

| Responsabilidade | Quem | Por quê |
|---|---|---|
| Descobrir o comando de boot | Agente (saída da Fase 1) | Varia por stack — é o que a Fase 1 deduz |
| Subir o processo e esperar ficar pronto | Agente | Idem |
| Exercitar a superfície, gravar e comparar | Harness | O algoritmo é o mesmo em toda linguagem |

**D6.2 — O runtime do harness é o runtime do alvo.** A Fase 1 já detectou a stack antes de o
harness ser necessário. Alvo Python → harness em Python de biblioteca padrão; alvo Node →
harness em Node sem dependências. A dependência adicional é **zero por construção**, não por
sorte.

**D6.3 — O protocolo é normativo; as implementações são traduções.** Existe um único
documento de referência com a spec; as implementações de referência são finas e derivadas
dele; uma stack não coberta é resolvida pelo agente **gerando** a implementação a partir da
spec; e a ausência de qualquer runtime com JSON cai no modo piso. Isto não é "um script por
ecossistema" — essa opção foi descartada: ela seria anti-agnóstica se o **protocolo**
variasse por stack, e ele não varia. A proposta original de "Markdown puro" sobrevive aqui,
promovida de caminho único a caminho geral.

**D6.4 — Modo piso declarado, não fallback silencioso.** Sem nenhum runtime capaz de
processar JSON, a validação cai para paridade de status code, e o relatório **declara** que
foi degradada e o que deixou de ser verificado. *Validação degradada rotulada é honesta;
validação degradada silenciosa é pior que não ter validação.* (Convergência de §4.)

**D6.5 — Comparação de forma, não de dados.** Compara-se status/exit code, content-type e o
**shape** do resultado — conjunto de chaves e tipos, recursivamente — nunca valores voláteis
como ids, timestamps ou ordenação não determinística. Comparar valores produziria regressões
falsas a cada rodada, e em dois dias o time aprenderia a ignorar o resultado da validação.
*Uma validação ruidosa é pior que nenhuma: custa o mesmo e você para de ler.*

**D6.6 — Conformidade com o enunciado.** O enunciado exige **arquivos de referência em
Markdown**; os arquivos de conhecimento são Markdown. O harness não é arquivo de referência
— é ferramental, e o protocolo que ele implementa está integralmente descrito no documento
normativo.

**Alternativas rejeitadas.**
- *Harness fixo em Python, com fallback `curl`* — a posição original; caiu pelas duas falhas
  acima.
- *Um script por ecossistema, mantidos em paralelo* — multiplicaria a spec e permitiria que
  o comportamento divergisse por stack, que é o oposto de agnóstico.
- *Markdown puro, sem nenhuma implementação de referência* — obrigaria o agente a reinventar
  o harness em toda rodada, com variação a cada vez; sobrevive como caminho para stacks não
  cobertas, não como único caminho.

**Custo aceito / consequências.** Existem agora N implementações do mesmo protocolo, e elas
podem divergir entre si ou da spec — o custo clássico de qualquer normativa com múltiplas
implementações; o documento normativo tem que ser tratado como a autoridade, e as
implementações revisadas contra ele. Para stacks não cobertas, a implementação é **gerada
em tempo de execução**, o que significa código não revisado participando da validação — um
risco assumido conscientemente, em troca de não acoplar a skill a um conjunto fechado de
ecossistemas. E o modo piso, embora honesto, entrega menos: declarar a degradação não a
elimina.

---

### D7 — Escopo da Fase 3: corrigir tudo, com gate de contrato

**Contexto.** O enunciado pede, na validação da Fase 3, `Zero anti-patterns remaining` — e
pede também que os endpoints originais continuem respondendo. As duas exigências entram em
tensão: alguns anti-patterns só somem se o contrato público mudar (uma rota mal nomeada, um
status code errado, um campo de resposta redundante).

**Decisão.** A Fase 3 corrige findings de **todas as severidades**. Porém, qualquer correção
que alteraria o **contrato público** da aplicação **não é aplicada** — é registrada como
`PROPOSED, NOT APPLIED`, com justificativa, no relatório final.

Contam como mudança de contrato: renomear/mover rota, alterar método HTTP, mudar status code
de sucesso, mudar o formato do corpo da resposta, remover ou renomear campo, tornar
obrigatório um parâmetro antes opcional. **Não** contam (e portanto são aplicadas): corrigir
SQL injection, mover segredo para variável de ambiente, eliminar N+1, extrair lógica para
camada, renomear identificador interno, transformar magic number em constante, centralizar
error handling. Estas mudam a *implementação*, não o que o cliente observa em uso legítimo.

**Justificativa.** O gate resolve a tensão sem sacrificar nenhuma das duas exigências: tudo
o que é seguro é corrigido, tudo o que é arriscado é proposto com argumento. A afirmação
"não quebrei nada" (D4) só é **verificável** se o contrato for preservado — mudar o contrato
e depois comparar contra o baseline produziria divergências que não são regressões, tornando
o sinal da validação inútil. E há um argumento de papel: decidir *pelo* time o que quebrar
não é função de uma ferramenta automatizada. A ferramenta pode identificar, argumentar e
propor; a decisão de romper compatibilidade é do dono do sistema.

**Alternativas rejeitadas.**
- *Corrigir apenas CRITICAL e HIGH* — mais seguro, mas deixa o `Zero anti-patterns
  remaining` inalcançável por desenho e abandona MEDIUM/LOW que são baratos e seguros de
  corrigir.
- *Corrigir tudo, inclusive contrato* — atingiria a letra do `Zero anti-patterns remaining`
  ao custo de invalidar a validação de D4 e de tomar, sem mandato, uma decisão de negócio.

**Custo aceito / consequências.** `Zero anti-patterns remaining` deixa de ser literalmente
verdade quando há itens `PROPOSED, NOT APPLIED`, e o relatório tem que carregar essa
qualificação em vez de exibir um check limpo — é menos vistoso e mais honesto. Além disso, a
classificação "isto muda o contrato?" é um juízo que a skill precisa fazer em cada correção;
a lista acima cobre os casos comuns, mas casos de fronteira existirão e vão depender do
julgamento do agente. D7 depende diretamente de D4 (sem baseline, o gate não teria o que
proteger) e interage com D10, cuja terceira opção de confirmação permite restringir o escopo
a CRITICAL+HIGH numa rodada específica.

---

### D8 — Medição: scorecard formal com métricas de generalização

**Contexto.** "A skill funcionou" precisa de uma definição operacional. O enunciado fornece
um checklist binário (as três fases cumpriram o contrato?), mas ele não distingue uma skill
que **generaliza** de uma que apenas reencontra o que o autor plantou nela.

**Decisão.** Uma rubrica formal define as métricas, e cada rodada produz um scorecard.

| Métrica | Pergunta que responde |
|---|---|
| Checklist do enunciado (Fases 1/2/3) | A skill cumpre o contrato do desafio? (binário, obrigatório) |
| **Recall** vs. análise manual | Dos problemas que eu sei que existem, quantos ela achou? |
| **Falsos positivos** | Quantos findings apontam para código que está correto? |
| **Findings inventados** | Quantos citam arquivo/linha que não existe ou não contém aquilo? |
| **Achados além do gabarito** ⭐ | Quantos problemas legítimos ela achou que **não** estavam na análise manual? |
| Regressões pós-refactor | Quantos pontos de entrada divergiram do baseline (D4)? |
| Intervenções humanas | Quantas vezes foi preciso corrigir o rumo para a rodada terminar? |

**Justificativa.** Está desenvolvida em §5 deste documento, porque é o outro princípio
transversal do projeto. Em resumo: *achados além do gabarito* é a métrica-chave porque é a
única evidência **positiva** de generalização, e *findings inventados* é a contramétrica sem
a qual a primeira se degrada em prêmio por alucinação.

**Alternativas rejeitadas.**
- *Só o checklist do enunciado* — binário e satisfeito por uma skill acoplada; não distingue
  qualidade de conformidade.
- *Só recall contra a análise manual* — a métrica mais fácil de inflar que existe neste
  projeto (ver §5).

**Custo aceito / consequências.** O scorecard é preenchido à mão, rodada a rodada, e produz
artefatos de processo que não constam da estrutura de entrega exigida pelo enunciado.
Julgar se um achado além do gabarito é **legítimo** é subjetivo, e o julgamento é feito pela
mesma pessoa que escreveu o catálogo e o gabarito — um conflito de interesse que a rubrica
mitiga, mas não elimina. D8 só é significativo porque D12 garante a independência entre
catálogo e gabarito, e só é comparável entre rodadas porque D3 as isola.

---

### D9 — Arquivos originais na Fase 3: reescrita in-place

**Contexto.** A Fase 3 move o conteúdo para as camadas do MVC. Resta decidir o que fazer com
os arquivos originais: apagá-los, movê-los para um diretório de legado, ou construir a nova
estrutura ao lado da antiga.

**Decisão.** O conteúdo migra para as camadas e os arquivos originais são **removidos**. A
rede de segurança é o histórico do git, as tags de rodada (D3) e o baseline comportamental
(D4).

**Justificativa.** É a única opção compatível com `Zero anti-patterns remaining`. Deixar o
código antigo ao lado do novo mantém no repositório uma segunda implementação do mesmo
comportamento, com todos os anti-patterns intactos. Uma auditoria seguinte os reencontraria
— e com razão, porque **código morto é um anti-pattern, não um backup**. Backup é o que o
git faz, e faz melhor: com histórico, autoria, data e diff.

**Alternativas rejeitadas.**
- *Diretório `legacy/` preservado* — cria o problema acima e ainda sugere que alguém vai
  voltar lá, o que nunca acontece.
- *Nova estrutura em paralelo, antiga intocada* — dobra a superfície do projeto e deixa
  ambíguo qual é o ponto de entrada real.

**Custo aceito / consequências.** Não há escape hatch dentro da árvore de trabalho: uma
rodada que falhe no meio pode deixar o projeto em estado não executável até um `reset`. A
recuperação depende inteiramente de disciplina de git — se a tag da rodada não foi criada
(D3), o custo do erro sobe muito. E a comparação antes/depois, pedida na documentação de
entrega, precisa ser feita via git, não olhando dois diretórios lado a lado.

---

### D10 — Confirmação da Fase 2: obrigatória, com escape para iteração

**Contexto.** A pausa antes da Fase 3 é requisito explícito do enunciado, repetido em vários
pontos e presente no checklist de validação avaliado. Ao mesmo tempo, o próprio enunciado
avisa que 2–4 iterações por projeto são normais — e reconfirmar um relatório já lido, doze
vezes, é atrito sem valor.

**Decisão.** A pausa fica **ON por padrão** e não pode ser desligada por default. A skill
aceita `--yes`, que pula a confirmação, e o relatório **registra qual modo foi usado**. A
forma da confirmação é o prompt `[y/n]` literal, como no exemplo do enunciado, com uma opção
adicional para aplicar apenas CRITICAL+HIGH. Antes do `y`, a única escrita permitida é em
`<alvo>/reports/` (D5).

**Justificativa.** O requisito é do avaliador e não é negociável; o `y/n` literal garante a
correspondência com o que será verificado, e a terceira opção é **aditiva**, portanto não
descumpre nada. O `--yes` existe para o nosso ciclo de calibração, e a escolha de projeto
aqui é a de sempre neste repositório: em vez de um atalho silencioso, um atalho **que se
declara**. Registrar o modo no relatório é o que impede confundir, semanas depois, uma
rodada auto-aprovada com uma revisada por humano — que é precisamente a confusão que
invalidaria a evidência de que a pausa funciona.

**Alternativas rejeitadas.**
- *Pausa sempre, sem escape* — cumpre o enunciado ao pé da letra e torna a calibração
  desnecessariamente cara.
- *`--yes` sem registro no relatório* — economiza uma linha e destrói a rastreabilidade da
  evidência.
- *Substituir `y/n` por um menu próprio* — mais expressivo, mas quebra a correspondência
  literal com o exemplo que o avaliador vai procurar.

**Custo aceito / consequências.** `--yes` é, por construção, uma porta que permite produzir
uma rodada que *parece* revisada por humano; a mitigação é documental (o registro do modo),
não técnica. A terceira opção (só CRITICAL+HIGH) cria um segundo escopo possível para a Fase
3, que precisa conviver com o "corrigir tudo" de D7 — e uma rodada feita nesse modo não pode
ser lida como evidência de `Zero anti-patterns remaining`. A permissão de escrita em
`reports/` antes do `y` depende de o `SKILL.md` delimitar o perímetro com precisão (D5).

---

### D11 — Escopo: genérico por superfície pública, não só HTTP

**Contexto.** Dois eixos de agnosticismo estavam misturados na conversa: ser agnóstica de
**stack** (Python/Node/Go/Ruby), que o enunciado exige, e ser agnóstica de **tipo de
aplicação** (API/CLI/worker/biblioteca), que ele não exige. Boa parte do `SKILL.md` estava
implicitamente assumindo que todo alvo tem uma porta HTTP.

**Decisão.** Separar os eixos e adotar os dois, unificados por um conceito:

> **Superfície pública** = o conjunto de pontos de entrada observáveis que o mundo externo
> usa.

O algoritmo de validação de D4 é o mesmo para todos — *enumerar a superfície → exercitar →
gravar a forma → comparar*. Só o adaptador muda:

| Tipo de aplicação | Superfície | O que se compara |
|---|---|---|
| Serviço HTTP | rotas (método + path) | status, content-type, shape do corpo |
| CLI | comandos + flags | exit code, shape do stdout |
| Biblioteca | API exportada | assinaturas, shape do retorno |
| Worker / consumidor | mensagens consumidas | efeitos e mensagens produzidas |

**Justificativa.** O ponto contraintuitivo é que generalizar assim **reduz** trabalho, em vez
de aumentar. A hipótese "existe uma porta HTTP" estava espalhada por vários pontos do
`SKILL.md`, cada um com sua própria formulação; substituí-la por um conceito único com um
ponto de extensão elimina a repetição e concentra a variação num lugar só. Generalização que
adiciona abstração sem remover duplicação seria luxo; esta paga o próprio custo.

**D11.1 — Consequência sobre o alvo arquitetural.** MVC pressupõe roteamento e apresentação.
Para uma biblioteca pura não existe View, e forçar MVC produziria uma pasta `views/` vazia só
para satisfazer checklist. As guidelines definem o alvo como **separação de camadas, com MVC
como instância concreta**: havendo superfície de requisição, MVC literal — o caso dos três
alvos e o que o enunciado cobra; não havendo, o mapeamento mais próximo (domínio / portas /
adaptadores), com o relatório **declarando** a adaptação e a justificativa. (Convergência
de §4.)

**Alternativas rejeitadas.**
- *Assumir HTTP em toda parte* — mais simples e falso; reprovaria no Teste do Quarto Projeto
  no primeiro alvo que fosse um worker ou uma CLI.
- *MVC literal sempre, inclusive onde não há View* — produziria estrutura cerimonial
  (diretório vazio) para satisfazer um checklist, que é o oposto do que o padrão serve para
  fazer.

**Custo aceito / consequências.** Os três alvos são todos serviços HTTP: os adaptadores de
CLI, biblioteca e worker **nunca serão exercitados neste projeto**. São, portanto,
generalização sem prova — exatamente o tipo de código que costuma estar errado quando
finalmente é usado. A alternativa (não generalizar) foi julgada pior porque a hipótese HTTP
estava entrando em lugares onde não pertencia. Segundo custo: D11.1 afrouxa o alvo
arquitetural de "MVC" para "separação de camadas", e o checklist do avaliador fala em MVC —
a mitigação é que, para todo alvo com superfície de requisição, a instância concreta *é*
MVC literal, e a adaptação só existe em casos que este desafio não contém.

---

### D12 — Ordem de trabalho: catálogo cego primeiro, gabarito em sessão separada

**Contexto.** O enunciado sugere a ordem natural: primeiro analisar manualmente os três
projetos, depois escrever a skill "agora que você conhece os problemas". Essa ordem é
pedagogicamente razoável e metodologicamente fatal para a medição que D8 pretende fazer.

**Decisão.** Inverter a ordem e separar as sessões:

1. **Sem ter lido nenhum dos três projetos**, escrever o catálogo de anti-patterns e as
   demais referências, a partir de literatura (Fowler, SOLID, OWASP).
2. **Congelar e commitar** o catálogo.
3. **Depois**, em sessão separada que nunca viu o catálogo, fazer a análise manual dos três
   projetos — esse é o **gabarito**.
4. Comparar os dois para produzir as métricas de D8.

**Justificativa.** Catálogo e gabarito precisam ser **mutuamente independentes**, senão as
métricas mentem — e mentem nas duas direções, o que é o detalhe que torna a decisão
necessária:

- *Gabarito primeiro* → o **catálogo** nasce enviesado, contendo só as categorias que o autor
  por acaso encontrou nos três projetos. E essa contaminação é invisível: ela não aparece
  como nome de arquivo (que a regra de §2 pega numa revisão), aparece na **escolha das
  categorias incluídas** — no que ficou de fora. Nenhuma revisão do texto detecta uma
  ausência.
- *Catálogo primeiro, mas na mesma sessão* → o **gabarito** é que nasce enviesado: o autor
  encontra exatamente o que o catálogo mandou procurar, o recall infla para perto de 100% e
  *achados além do gabarito* vira zero por construção. A skill fica boa; a métrica morre.

**Este momento é irrepetível.** É a única janela em que o autor do catálogo está
genuinamente cego para os alvos. Depois de ler um projeto, não há como desler — e por isso
a decisão precisou ser tomada e executada antes de qualquer curiosidade ser satisfeita.
É também a razão pela qual este documento foi escrito sem acesso aos três projetos.

**Alternativas rejeitadas.**
- *A ordem sugerida pelo enunciado* (análise manual primeiro) — a mais confortável e a que
  contamina o catálogo de forma indetectável.
- *Tudo numa sessão só, com disciplina de não olhar* — impossível de garantir e impossível
  de auditar depois; a separação por sessão é o mesmo tipo de garantia estrutural que D2 dá
  contra a divergência de cópias.

**Custo aceito / consequências.** O projeto desobedece à ordem de execução sugerida pelo
enunciado, e isso precisa ser explicado na documentação de entrega para não parecer
desatenção. O catálogo cego pode genuinamente **não cobrir** categorias que existem nos
alvos — e o enunciado cobra que a Fase 2 reencontre ao menos cinco dos problemas da análise
manual, o que, sob D12, é um teste real que pode falhar, em vez de uma formalidade
garantida por construção. Exige duas sessões e um commit de congelamento no meio do
caminho. Em troca, as métricas de D8 passam a significar o que dizem significar: D12 é a
decisão que sustenta D8.

---

### D13 — APIs deprecated: evidência viva, nunca lista estática *(revertida)*

**Contexto.** O enunciado exige, explicitamente, que o catálogo inclua detecção de APIs
deprecated com recomendação do equivalente moderno. Essa exigência colide de frente com a
restrição governante: todo item útil dessa categoria é **acoplado a um ecossistema** e, pior,
**perece**. Uma lista escrita hoje estará parcialmente errada em dezoito meses, e uma skill
que afirma deprecation a partir da memória do modelo produz exatamente aquilo que D8 mede
como defeito grave: *findings inventados*.

#### Reversão

**Posição original.** Duas camadas. A Camada 1 seria evidência local (observar warnings do
runtime); a Camada 2 seria um **apêndice estático datado** de APIs conhecidamente deprecated
por ecossistema, mantido dentro da skill.

**O desafio levantado.** O autor do repositório recusou o apêndice estático.

**A falha exposta.** Conteúdo **perecível versionado dentro de uma skill envelhece sem
aviso**. Um arquivo de referência não tem data de validade visível para quem o lê: ele
parece igualmente autoritativo no primeiro dia e três anos depois. Pior, ele contamina o
resto do catálogo por associação — o leitor (humano ou agente) não tem como saber que
aquela seção específica apodreceu enquanto as outras continuam válidas. E o apêndice
carregaria a acoplagem a ecossistemas para dentro do artefato que §2 protege.

**A resolução.** A Camada 2 deixou de ser conteúdo e virou **consulta viva em tempo de
execução**, sob uma regra fundante:

> A skill pode saber **onde perguntar**. Ela não pode saber **a resposta**.
>
> O conhecimento do modelo é **gerador de hipótese, nunca evidência**. O modelo pode decidir
> *verificar* se algo está deprecated; não pode **reportar** que está. Todo finding desta
> categoria cita **fonte + data da consulta**, ou não é reportado.

A distinção operacional é entre fato estável e fato perecível: um endpoint de registry é
infraestrutura e pode ser versionado com segurança, porque diz apenas *para onde mandar a
query*. "O pacote X está deprecated" é perecível e só pode vir de consulta viva.

**A correção na premissa do próprio autor.** Durante a mesma discussão, a Camada 1 também
mudou. A formulação original — "observar se o código roda sem warnings de deprecation" —
prova muito pouco, porque **os runtimes escondem esses warnings por padrão**: Python suprime
`DeprecationWarning` fora do `__main__` e Node mantém *pending deprecations* desligadas.
"Rodou limpo" com os detectores desligados não é informação. A Camada 1 passou, então, a
**ligar os detectores** antes de concluir qualquer coisa:

```bash
PYTHONWARNINGS=always::DeprecationWarning   python -X dev <boot>
node --pending-deprecation --trace-deprecation <boot>
```

Benefício colateral que vale registrar: o warning vem com **stack trace apontando arquivo e
linha** — exatamente o campo `File: <caminho>:<linha>` exigido pelo template de relatório. A
evidência chega no formato do entregável, sem intermediação de juízo.

**A lição geral.** Duas. Primeira: **ausência de sinal não é sinal de ausência** quando o
detector está desligado por padrão — uma verificação que não pode falhar não é uma
verificação. Segunda: numa skill, conhecimento perecível deve ser substituído por *endereço*
de conhecimento; versionar a pergunta é seguro, versionar a resposta não é.

**Decisão (forma final).** Duas camadas, ambas baseadas em evidência.

**Camada 1 — evidência local, offline, forçada.** Ligar os detectores de deprecation do
runtime antes de concluir qualquer coisa (comandos acima), e complementar com sinais locais
e agnósticos: dependência marcada como deprecated no manifesto/lockfile; padrões
estruturalmente superados (callback onde o ecossistema migrou para async; API síncrona
bloqueante onde existe assíncrona).

**Camada 2 — consulta viva, opcional, nunca estática.** Executada em tempo de execução, com
o resultado carimbado com a data. Versiona-se apenas a **tabela de adaptadores** — onde
perguntar — nunca as respostas.

| Fonte | Cobre |
|---|---|
| **OSV.dev** | advisories por pacote+versão; **uma API para npm, PyPI, crates, Go, Maven, RubyGems** — agnóstica por design |
| Registry do ecossistema | pacote deprecated/yanked exatamente na versão pinada |
| Tooling nativo (`npm outdated`, `pip list --outdated`) | distância da versão em uso |
| Doc/changelog oficial da versão em uso | deprecations **de linguagem**, que registry nenhum reporta |

**Gradação de evidência** — determina se o finding pode ser reportado:

| Tier | Evidência | Reportável? |
|---|---|---|
| **A — observada** | warning emitido pelo runtime, com stack trace | Sim, com arquivo e linha |
| **B — declarada** | metadado de registry/advisory para a versão pinada | Sim, citando fonte + data |
| **C — documentada** | doc/changelog oficial da versão em uso | Sim, citando URL + data |
| **D — suspeita** | conhecimento prévio do modelo | **Não.** Promove a A/B/C por verificação, ou descarta |

O Tier D é o coração da decisão: o conhecimento prévio do modelo é admitido como **motor de
busca**, e nunca como testemunha. A severidade segue o impacto: pacote deprecated **com
advisory de segurança** escala para CRITICAL/HIGH; API soft-deprecated sem risco fica
MEDIUM/LOW.

**Degradação declarada.** Sem rede, a Camada 2 não roda. O relatório **declara** que a
verificação upstream foi pulada e o que deixou de ser coberto — nunca omite silenciosamente.
Um flag `--offline` força esse modo. (Convergência de §4.)

**Alternativas rejeitadas.**
- *Apêndice estático datado por ecossistema* — a posição original; recusada porque conteúdo
  perecível dentro da skill envelhece sem aviso e contamina o catálogo.
- *Deixar o modelo reportar deprecations pelo que sabe* — o caminho que produz findings
  inventados, que é a contramétrica explícita de D8.
- *Simplesmente observar se o app roda sem warnings* — inválido, porque os runtimes
  suprimem esses warnings por padrão.

**Custo aceito / consequências.** A skill passa a depender de **rede** para a cobertura
completa desta categoria, e o modo offline entrega menos (declaradamente). A regra do Tier D
é deliberadamente conservadora: deprecations reais que o modelo conhece mas não consegue
verificar **não serão reportadas** — trocou-se recall por precisão, de forma consciente, e
essa troca aparece nas métricas de D8. Forçar os detectores do runtime pode inundar a saída
com warnings vindos de dependências de terceiros, e não do código do alvo, exigindo
filtragem. E a tabela de adaptadores, embora estável, é ela própria um item que pode
envelhecer — endpoints mudam, mesmo que devagar; a aposta é que mudem muito mais devagar que
o conteúdo que eles retornam.

---

### D14 — Re-auditoria obrigatória e a linha que precisa ser merecida

**Contexto.** O exemplo de saída do enunciado (`instructions.md`, L107) encerra a Fase 3 com
`Zero anti-patterns remaining`. Reproduzi-lo literalmente exigiria que a skill afirmasse, ao
final de toda refatoração, que nenhum anti-pattern restou.

A frase é uma **universal negativa**. Ela não diz "corrigi o que encontrei"; diz que não existe
mais nenhum. Ter corrigido todos os findings da Fase 2 não a sustenta, porque aquela lista nunca
foi prova de exaustividade — ela era o resultado de uma varredura, não um censo. E há um problema
adicional, específico deste projeto: sob o gate de contrato de D7, itens são deliberadamente
deixados sem aplicar e registrados em `PROPOSED, NOT APPLIED`. Se existe um único item ali, então
restam anti-patterns por construção — e o próprio relatório os lista poucas linhas abaixo. A linha
e a lista se contradiriam dentro de uma mesma tela. O mesmo vale para uma rodada executada no modo
`CRITICAL+HIGH only` (D10.1).

**Decisão.** Duas partes:

1. A **re-auditoria passa a ser passo obrigatório da Fase 3** (etapa 3d): a auditoria da Fase 2 é
   re-executada sobre o alvo refatorado, com o mesmo catálogo e os mesmos limiares. É o único fato
   capaz de licenciar qualquer afirmação sobre o que restou.
2. O resultado **sempre ocupa uma linha** no bloco `## Validation`, em uma de três formas:

```
  ✓ Zero anti-patterns remaining  (re-audit: 0 findings)
  ○ Anti-patterns remaining: <k> proposed-not-applied, <u> unresolved  (re-audit: <m> findings)
  ⚠ Re-audit partial — see Verification Coverage  (<m> findings over the checks that ran)
```

Os findings remanescentes são separados em dois conjuntos que **não** podem ser somados:
`proposed-not-applied`, decisões tomadas de propósito e justificadas pelo gate de contrato; e
`unresolved`, transformações que falharam ou problemas que a refatoração introduziu. Colapsá-los
num número único esconderia exatamente o que exige ação.

**Justificativa.** Esta é a afirmação mais forte do relatório inteiro e a mais barata de imprimir.
Um `✓` de template custa zero e, por isso, não carrega informação nenhuma — pior, ensina o leitor
a desconfiar dos demais `✓` da mesma lista. Condicionar a linha à evidência é a aplicação direta
do princípio emergente da §4: a skill nunca degrada em silêncio, e o output nunca mente para o
usuário. A escolha da forma intermediária preserva o vocabulário do exemplo do enunciado nos três
casos, de modo que o leitor reconheça o padrão esperado sem que nada seja afirmado sem verificação.

**Alternativas rejeitadas.**

- *Imprimir a linha sempre, como no exemplo.* Reproduziria o enunciado ao pé da letra, mas abriria
  no relatório uma contradição visível e daria ao princípio governante do projeto uma exceção
  justamente na afirmação mais destacada.
- *Omitir a linha quando não fosse verdadeira.* Honesto, porém deixaria um vazio onde o avaliador
  espera um item, sem explicar o motivo da ausência — uma forma branda de degradação silenciosa.

**Custo aceito e consequências.** A re-auditoria obrigatória alonga a Fase 3 e consome contexto:
o catálogo inteiro é percorrido uma segunda vez. Na prática, com o gate de contrato ativo, a
primeira forma raramente aparecerá — a maioria das rodadas terá ao menos um item
proposto-não-aplicado. O risco de avaliação foi verificado e é baixo: a string aparece **uma única
vez** em `instructions.md`, dentro do bloco ilustrativo "Exemplo de Uso no CLI", e não consta nem
do checklist de validação avaliado nem dos Critérios de Aceite, que cobram "a aplicação funciona"
— demonstrado com mais evidência pelas linhas de replay de D4 do que por um `✓` genérico.
Uma re-auditoria parcial (por exemplo sob `--offline`, sem a consulta viva de D13) nunca produz a
primeira forma: cobertura reduzida não sustenta afirmação de ausência.

---

### Nota — decisões da rodada 2 (D15–D18)

As decisões abaixo foram tomadas **depois** da rodada 1, a partir do relatório consolidado
([`docs/rounds/round1-report.md`](rounds/round1-report.md)), e **antes** do gabarito. A sessão que
as tomou leu o relatório, mas não o código dos projetos nem o gabarito. Não são mais decisões
cegas no sentido de D12. A lista de mudanças foi congelada e commitada antes de qualquer edição
([`docs/rounds/round2-changes.md`](rounds/round2-changes.md)), e cada decisão aponta para o problema da rodada 1
que a originou. Um revisor pode assim separar o que veio da literatura do que veio da calibração.

---

### D15 — Autorização e validação: o teste do uso legítimo

**Contexto.** Problema #6 da rodada 1. O `SKILL.md` tratava todo `401` novo como mudança de
contrato (portanto: propor). As guidelines §6 e o playbook RP-04 mandavam aplicar a checagem de
autorização que faltava. As duas instruções se contradiziam, e o agente escolhia uma delas sem
regra. Na rodada 1 a escolha foi "propor" nos três projetos. O resultado estava certo lá (nenhum
dos três tinha modelo de identidade), mas por sorte, não por regra.

**Decisão.** A decisão depende de uma pergunta: **quem recebe a nova rejeição?** Sem modelo de
identidade, todo cliente atual é anônimo e passaria a receber o `401`, legítimos inclusive: é
mudança de contrato e vira proposta. Com identidade, mas sem checagem de dono ou papel, só o
chamador que age sobre o recurso de outro é rejeitado: é seguro e é aplicado. O mesmo teste vale
para validação: um valor inválido em si mesmo (payload de injeção, identificador malformado,
período que termina antes de começar) é rejeitado; uma regra que exige decisão de produto é
proposta. O texto é o mesmo em `SKILL.md`, guidelines §6 e RP-04.

**Justificativa.** Não é uma regra nova. É a regra que a D7 já usava para SQL injection
("mudam a implementação, não o que o cliente observa **em uso legítimo**"), aplicada por extenso a
um caso que ela não nomeava. A decisão passa a depender de fatos legíveis no código (existe modelo
de identidade? um cliente legítimo mandaria esse valor?), e não de adivinhar quem são os
principais. Passa no Teste do Quarto Projeto: não importa se o alvo é Rails, Go ou Express.

**Alternativas rejeitadas.**
- *Sempre propor* — previsível, mas a skill nunca fecharia um IDOR, mesmo quando isso não afeta
  nenhum cliente legítimo. Seria cauteloso demais para uma ferramenta que diz corrigir CRITICAL.
- *Sempre aplicar* — quebra a promessa da D7 e, na rodada 1, teria trancado todos os clientes dos
  três projetos.

**Custo aceito / consequências.** A fronteira entre "inválido em si mesmo" e "regra de produto"
exige julgamento, e haverá casos ambíguos. A regra de desempate é explícita: ambíguo, propõe.

---

### D16 — O original roda de um snapshot intocado, fora do alvo

**Contexto.** Problema #3 da rodada 1. A camada 1 de AP-14 exige executar a aplicação com os
detectores de deprecation ligados, e isso acontece na Fase 2. Executar a aplicação cria arquivos
(banco em arquivo, caches, bytecode) fora de `<alvo>/reports/`, a única pasta que a Fase 2 pode
tocar antes da confirmação. A regra da D5/D10 não previa artefatos de runtime. Relacionados: o
problema #1 (porta fixa no código, sem instrução para trocá-la sem editar o original) e o #12
(entradas adicionadas depois do baseline ficavam sem comparação, porque o original já não existia).

**Decisão.** No início da Fase 2, antes de qualquer execução, a skill copia o alvo para um
**snapshot intocado** num diretório temporário fora dele. Toda execução do **original** (a da
Fase 2, o baseline, uma captura tardia) roda numa cópia nova desse snapshot. A aplicação
refatorada roda no alvo. O snapshot é apagado ao final. A escolha de porta segue uma ordem
declarada: override que o código já lê, porta nativa com execuções em sequência, launcher fora da
árvore. O original nunca é editado.

**Justificativa.** Mantém a regra de escrita da Fase 2 **absoluta**, sem exceções. Uma regra com
lista de exceções é a que se erode primeiro. E resolve três problemas com um mecanismo: artefatos
de runtime (#3), estado inicial igual para todas as execuções do original, e um original disponível
para capturas tardias (#12).

**Alternativas rejeitadas.**
- *Executar no lugar e limpar depois* (comparar `git status` antes e depois) — perde arquivos
  ignorados pelo `.gitignore` e alterações em arquivos de banco versionados, e depende de git.
- *Ampliar a regra* para aceitar artefatos de runtime — enfraquece justamente o requisito que o
  enunciado cobra em cinco lugares.

**Custo aceito / consequências.** Copiar o alvo custa tempo e disco. Diretórios de dependência
podem ser linkados ou reinstalados a partir do lockfile, e o relatório declara qual das duas. Os
stack traces das execuções apontam para caminhos da cópia e precisam ser traduzidos para caminhos
relativos ao alvo.

---

### D17 — Entradas de segurança: comportamento que deve mudar

**Contexto.** Problema #9 da rodada 1. Uma entrada maliciosa (injeção, valor fora do domínio) muda
de status quando o finding é corrigido: era aceita e passa a ser rejeitada. No inventário comum, o
harness a marcava como `REGRESSION`. O rótulo estava errado, e ensinaria o leitor a ignorar o
estado de resultado.

**Decisão.** O inventário ganha entradas `kind: "security"`, que obrigatoriamente nomeiam o
finding que demonstram (`finding: "AP-xx"`), com `expect: "rejected"`. Os resultados são
`FIXED`, `NOT FIXED`, `REGRESSION` (a correção fez a entrada hostil derrubar a aplicação) ou
`UNVERIFIED` (o baseline já rejeitava, e a entrada não demonstra nada). Essas entradas rodam
depois das entradas de contrato, porque podem alterar estado. Um `NOT FIXED` num finding contado
como resolvido é contradição, e o finding volta para `unresolved`.

**Justificativa.** O baseline deixa de só proteger contra regressão e passa também a provar a
correção: a rodada 1 mostrou no baseline três findings de segurança sendo explorados, mas nada
mostrava, depois, que tinham sido fechados. A exigência de `finding` impede que "segurança" vire
isenção genérica da regra de regressão.

**Alternativas rejeitadas.**
- *Pular as entradas maliciosas* — perde a única evidência comportamental de que a correção
  funciona.
- *Deixar como `REGRESSION` e explicar no relatório* — é o ruído que a D6.5 proíbe.

**Custo aceito / consequências.** O agente precisa escrever essas entradas, e só vale para
correções visíveis como rejeição. Um hash que deixa de sair na resposta não é "rejeição"; é
verificado de outra forma, e o relatório diz como.

---

### D18 — Upgrade de dependência versus contrato

**Contexto.** Problema #10 da rodada 1. Não estava definido se um upgrade major, ou com mudança de
comportamento, é mudança de contrato. Dois subagentes decidiram de formas opostas na mesma rodada.
Um aplicou um upgrade major; o outro propôs um upgrade porque o harness não capturava os headers
afetados. O segundo estava mais certo, mas pelo motivo errado: a limitação era do harness, não da
regra.

**Decisão.** Patch ou minor dentro da mesma major: seguro. Major, ou versão cujo changelog anuncia
mudança de comportamento: seguro **só** se o replay exercitar o comportamento que muda. Senão,
proposta. Para tornar isso verificável, o protocolo passa a capturar uma allowlist normativa de
**headers de contrato** (`Location`, `WWW-Authenticate`, `Access-Control-*` e os nomes dos
`Set-Cookie`). Advisory de segurança sobe a severidade do finding, mas não dispensa a regra.

**Justificativa.** A regra depende de um fato verificável (o replay cobre o comportamento?), não da
confiança do agente no changelog. E a allowlist aumenta o que o replay cobre sem trazer de volta o
ruído que a D6.5 proíbe: são headers que clientes usam, e não detalhes de transporte.

**Alternativas rejeitadas.**
- *Todo major é contrato* — simples, mas deixaria vulnerabilidades abertas mesmo quando o replay
  prova que nada mudou.
- *Todo upgrade com advisory é seguro* — confunde urgência com segurança da mudança.

**Custo aceito / consequências.** O agente precisa ler o changelog entre as versões, e às vezes
acrescentar uma entrada à superfície **capturada contra o original** (D16).

---

### Mudanças menores da rodada 2 (sem decisão própria)

| # | Mudança | Por quê |
|---|---|---|
| 4 | Estados de registro separados: `OBSERVED`, `ERROR` (falha de transporte), `SKIPPED` | A spec v1 dizia em §4 que erro de transporte no baseline é falha, mas mandava gravá-lo em §3 com o mesmo estado de "pulado". **Os dois probes** seguiam o §3. A contradição estava na spec, não em um probe |
| 4 | Teste de conformidade entre `probe.py` e `probe.mjs` (`tests/probe-conformance/`) | Os probes são traduções da spec, e traduções divergem. O teste já encontrou uma divergência que a rodada 1 não viu: `probe.py` seguia redirects e `probe.mjs` não |
| 5 | Corpo de texto ≤ 4096 bytes comparado como esqueleto mascarado (linhas distintas, números/UUIDs/timestamps mascarados) | `opaque` escondia mensagens de erro reescritas |
| 7 | Nova AP-18 *Insecure Runtime Configuration* (OWASP A05) + RP-17 | Lacuna revelada na calibração: os subagentes classificaram debug ligado sob AP-15/AP-06, com escalonamento improvisado |
| 8 | Nova AP-19 *Known-Vulnerable Dependency* (OWASP A06) + RP-18, separada de AP-14 | Advisory não é deprecation. A regra de evidência de D13 vale integralmente |
| 11 | Achado resolvido: só três baldes, `resolved`, `proposed`, `unresolved`. **Não existe "parcial"** | Um balde "parcial" deixaria o finding contar como progresso enquanto o resto dele fica fora de todos os totais |
| 12 | `--only` e `--merge` no harness; entrada tardia é capturada contra o original (D16) | Uma entrada que só rodou contra o código novo não foi comparada com nada |
| 13 | Varredura **por entrada do catálogo** e tabela `Catalog Coverage` no relatório; AP-01 cobre credenciais em dados que chegam ao datastore de runtime (seeds, migrações) | Os três achados que a Fase 2 perdeu na rodada 1. **Constatação honesta:** AP-11 já listava "invariantes de domínio" na versão cega. A falha foi de **varredura**, não de catálogo, e por isso a correção principal é de processo |
| 13 | A re-auditoria marca cada `unresolved` com a origem: `failed`, `introduced` ou `missed-in-phase-2` | Mede o recall da Fase 2 separado da qualidade da refatoração (emenda à D14) |
| 2 | Instalar as dependências **declaradas** pelo alvo em ambiente isolado é permitido e registrado; adicionar dependência continua proibido | "Nunca instale dependência" não distinguia os dois atos |
| — | A skill nunca altera índice nem histórico do git | Intervenção da rodada 1: um subagente rodou `git rm --cached` |

---

### Nota — decisões da rodada 3 (D19–D23)

Tomadas depois de ler [`docs/rounds/round2-report.md`](rounds/round2-report.md) **e depois do
gabarito**. Diferente da rodada 2, o autor já não está cego para os alvos. A lista de mudanças foi
congelada antes de qualquer edição da skill
([`docs/rounds/round3-changes.md`](rounds/round3-changes.md)), e declara essa contaminação.

---

### D19 — Isolamento de execução: container primeiro, modo host declarado

**Contexto.** Incidente R2-1. Na Fase 2 de um dos projetos, um subagente encerrou a cópia do
original com `taskkill /F /IM python.exe`, que mira todo processo Python da máquina. A skill manda
subir e derrubar a aplicação umas seis vezes por execução (Fase 2, baseline, capturas tardias,
replay, re-auditoria), mas nunca disse **como** derrubar. O log da rodada omitiu o incidente, que
só apareceu na mensagem final do subagente. Relacionados: R2-2 (a aplicação refatorada rodava no
alvo e sujava a árvore com banco e bytecode; o snapshot era apagado antes da re-auditoria, que ainda
precisava dele) e R2-3 (overrides de porta com efeitos colaterais, como desligar o debug).

**Decisão.**
1. **Modo container**, quando existe um runtime de container. Cada execução (original ou
   refatorada) roda num container descartável com a cópia de execução montada, nome
   `refactor-arch-<alvo>-<run>` e label da rodada. O probe roda **dentro** do container (`exec`),
   contra a porta nativa, e por isso não é preciso publicar porta nem mudar bind. Encerrar é
   remover o container **por aquele nome exato**.
2. **Modo host**, quando não há container ou a imagem não pode ser obtida (por exemplo, com
   `--offline`). Toda execução passa pela ferramenta de ciclo de vida (D20). O relatório declara
   `Isolation: reduced (host)`.
3. **Nos dois modos**, é proibido encerrar por nome, imagem ou padrão, encerrar o que a skill não
   subiu e liberar à força uma porta ocupada por outro processo (escolhe-se outra porta). Todo
   start e stop entra num `## Execution Log` no relatório, e uma ação sobre processo fora do log é
   **incidente**, reportado em `## Verification Coverage`.
4. **Emenda à D16:** a aplicação refatorada também roda de uma cópia (`refactored-<n>/`), nunca no
   alvo. O snapshot é apagado depois da re-auditoria.

**Justificativa.** A rodada mostrou que uma regra sozinha não basta: o outro projeto Python usou a
forma segura (`taskkill /PID`) e este não, e a diferença foi acaso. Um container torna o erro
**inofensivo**, em vez de só proibido: um `kill` errado dentro dele não alcança o host, e o ciclo de
vida inteiro vira um handle só. É o padrão das outras degradações da skill (D6.4, D13): o melhor
modo quando possível, e o modo reduzido **declarado**.

**Alternativas rejeitadas.**
- *Só a regra* — é regra, não barreira. Depende de o agente obedecer sob pressão, que foi
  exatamente o que falhou.
- *Só container* — sem Docker, a skill pararia de validar. Isso contraria a D6.2 (dependência
  adicional zero) e o princípio de degradar declarando, e não parando.

**Custo aceito / consequências.** Dois caminhos de execução para manter e testar. O container
precisa de uma imagem oficial do runtime na versão da Fase 1, e baixá-la exige rede. Em host POSIX,
os arquivos criados no volume podem ficar com o dono do container: roda-se com o uid/gid do
usuário. O container é uma dependência **opcional do host**, não do alvo: a D6.2 continua valendo
para o que se instala no projeto.

---

### D20 — Ferramenta de ciclo de vida separada do probe (emenda à D6.1)

**Contexto.** No modo host, "encerrar só o que eu subi" exige lembrar o PID de uma invocação para
outra, conferir que o PID não foi reutilizado e encerrar a árvore inteira (servidores com
*reloader* criam filhos). Pedir isso a um agente a cada vez, em texto livre, é o que produziu o
R2-1. A D6.1 dizia que o agente sobe e encerra o processo, e que o harness nunca sobe nada.

**Decisão.** Novos scripts de referência `scripts/proc.py` e `scripts/proc.mjs` (stdlib/built-ins),
**separados do probe**:
- `start`: executa o argv que o agente derivou, num grupo de processos novo; grava PID, grupo,
  argv, cwd, porta e hora de início num arquivo de estado dentro do snapshot; espera a porta
  aceitar conexões. Recusa uma porta já ocupada.
- `stop`: confere a identidade do PID (a hora de início bate) e encerra **só a árvore registrada**.
  Se a identidade não bate, recusa e reporta.
- `status`: diz se o processo registrado está vivo e se a porta responde.

A D6.1 é emendada: o **agente** continua derivando *o que* rodar; o `proc` é dono só do *tempo de
vida* do processo; o **probe** continua sem subir nada.

**Justificativa.** Transforma a regra da D19 em código conferível, com teste. O `proc` não sabe nada
de stack: recebe um argv, como um supervisor de processos qualquer. Por isso não reintroduz o
acoplamento que a D6.1 evitava, que era o harness saber subir Flask, Express ou Rails.

**Alternativas rejeitadas.**
- *Pôr o ciclo de vida dentro do probe* — mistura um protocolo puro com gestão de processo e obriga
  o teste de conformidade do probe a cobrir comportamento de sistema operacional.
- *Instruções por sistema operacional no SKILL.md* — texto por plataforma, que envelhece, e
  continua dependendo de o agente acertar o PID.

**Custo aceito / consequências.** Mais duas implementações para manter em conformidade. Conferir a
hora de início do processo exige um comando do sistema (`ps` em POSIX, PowerShell no Windows),
porque nem a stdlib do Python nem o Node expõem isso de forma portável.

---

### D21 — Entrada de segurança neutralizada

**Contexto.** R2-5. A D17 só conhece `expect: "rejected"`. Uma correção de injeção que passa a
tratar a entrada hostil como texto, em vez de rejeitá-la, muda a resposta sem rejeitar. Sem estado
próprio, a entrada virou `REGRESSION` e a linha do replay saiu com `✗`. A saída foi honesta, mas
errada, e é o ruído que a D6.5 proíbe.

**Decisão.** `expect: "neutralized"`, obrigatoriamente com `like: <id de entrada benigna>`. O
resultado é `FIXED` quando o replay responde sem erro e com o mesmo shape da entrada benigna irmã,
capturada no mesmo baseline; `NOT FIXED` quando repete o comportamento anômalo do baseline. Nunca
vira `REGRESSION` só por ter mudado.

**Justificativa.** "Neutralizada" sem critério viraria isenção genérica, porque qualquer mudança
passaria. A entrada benigna irmã é o critério objetivo: a entrada hostil tem que passar a se
comportar como uma entrada comum do mesmo endpoint.

**Alternativas rejeitadas.**
- *Marcar a entrada como `skip`* — perde a única prova comportamental de que a injeção foi fechada.
- *Aceitar qualquer 2xx* — um 2xx com shape diferente pode ser justamente o vazamento.

**Custo aceito / consequências.** Cada entrada neutralizável precisa de uma irmã benigna no
inventário, com o mesmo método e caminho e parâmetros legítimos.

---

### D22 — O contrato de erro

**Contexto.** R2-7. O §6 das guidelines chamava de mudança de contrato alterar o shape da resposta de
erro; o RP-17 chamava de seguro trocar a página de erro padrão do framework, que vaza stack trace.
Um subagente mascarou segredos vazados mantendo o campo, e não havia regra que dissesse se isso é
seguro. Correções que exigem dependência nova (um servidor de produção) não tinham regra.

**Decisão.**
- São contrato o **status** e o **shape dos corpos de erro que a aplicação produz de propósito**.
  A página de erro padrão do framework, emitida quando nada tratou o erro, não é contrato:
  substituí-la mantendo o status é seguro.
- Mascarar um segredo ou credencial vazado **mantendo o campo e o tipo** é seguro, pelo teste do
  uso legítimo da D15: nenhum cliente legítimo depende de ler de volta um hash de senha ou uma
  chave. Remover o campo continua sendo mudança de contrato.
- Correção que exige **dependência de runtime nova** é proposta: muda o que quem implanta precisa
  instalar.
- Um `missed-in-phase-2` que exige decisão de produto pode ser `proposed`, e não só `unresolved`.

**Justificativa.** O teste é o mesmo em todos os casos: o que um cliente legítimo observa em uso
legítimo. Ninguém programa contra o HTML de uma página de erro não tratada. Um cliente pode
programar contra o JSON de erro que a aplicação documenta.

**Alternativas rejeitadas.** *Todo erro é contrato* deixaria vazamentos de stack trace sem correção.
*Nenhum erro é contrato* quebraria clientes que tratam códigos de erro da aplicação.

**Custo aceito / consequências.** O agente precisa distinguir erro intencional de erro não tratado.
O critério observável é quem produziu o corpo: um handler da aplicação ou o default do framework.

---

### D23 — Laço de correção limitado

**Contexto.** R2-10. O playbook mandava fazer replay depois de cada transformação e o SKILL.md tinha
um replay só. Não dizia se o que a re-auditoria encontra pode ser corrigido na mesma rodada. Os três
subagentes decidiram de três formas.

**Decisão.** Um replay completo é obrigatório; replays por transformação são opcionais (smoke).
Findings `failed` e `introduced` da re-auditoria podem ser corrigidos na mesma rodada, seguidos de
replay completo e de **no máximo mais uma** re-auditoria. As duas passadas ficam no relatório.
`missed-in-phase-2` corrigido na Fase 3 é contado à parte (`fixed-after-re-audit`), e o total de
findings da Fase 2 não muda.

**Justificativa.** Sem limite, o laço não termina e o relatório final não corresponde a nenhuma
auditoria completa. Sem permissão para corrigir, a skill entrega defeitos que ela mesma introduziu e
já viu. Contar `missed-in-phase-2` à parte mantém o recall da Fase 2 mensurável (D8): corrigir não
apaga o fato de que a auditoria não viu.

**Alternativas rejeitadas.** *Nunca corrigir depois da re-auditoria* é simples, mas entrega
`introduced` conhecidos. *Corrigir até zerar* pode não terminar.

**Custo aceito / consequências.** Uma rodada pode ter duas re-auditorias, e o relatório fica mais
longo.

---

### Mudanças menores da rodada 3 (sem decisão própria)

| # | Mudança | Por quê |
|---|---|---|
| R2-4 | `Target:` absoluto quando não é relativo ao CWD; campos `Boot:`, `Port:`, `Runtime env:`, `Isolation:`; `surface.json` escrito na 3a; exclusão de diretórios de configuração de agentes na contagem | O bloco da Fase 1 não tinha onde pôr o que o `01` mandava registrar, e a Fase 1 é só leitura |
| R2-6 | RP-18 alinhado ao §6; correção opt-in; advisory só domina AP-14 no caminho de runtime; pins exatos sem lockfile; degrau para advisory LOW; AP-14 sem sucessor nomeado | Arestas da regra da D18 que os subagentes resolveram cada um de um jeito |
| R2-9 | `audit-latest.md` é o estado final; sem prompt com `--yes`; uma só `## Proposed, Not Applied`; `File:` do arquivo inteiro para God Module | Contradições do template |
| R2-11 | Mensagens dos probes, contagem do aviso de transporte, saída de `capture --only --merge`, fixtures de conformidade | Bugs do harness |
| R2-12 | Precedência única entre AP-03 e AP-05 | As duas escalavam em direções opostas, e o número de findings dependia da escolha |
| R2-8 | Nova AP-20 *Missing Schema-Level Integrity Constraints* + RP-19 (Karwin, *SQL Antipatterns*); `Catalog Coverage` registra os sinais checados por entrada | Família perdida na Fase 2 nos três projetos. **Constatação honesta:** limite de tamanho de requisição e transição de estado sem guarda **já eram sinais de AP-11**; ali a falha foi de varredura. A entrada nova cobre só o que faltava no catálogo: restrições do esquema |

---

### D24 — Comandos analisáveis e scratch dentro do perímetro (emenda à D16 e à D19)

**Contexto.** Depois da rodada 3, toda execução da skill passou a interromper o usuário dezenas de
vezes com *"Contains simple_expansion; under the read block
(permissions.blockReadsOutsideWorkingDirectories) a command the shell parser cannot analyse asks
the person"*. Com essa configuração ligada, o Claude Code só roda um comando shell sem perguntar se
provar, **lendo o texto do comando**, que todo path acessado fica dentro dos diretórios permitidos.
A D16 pôs o snapshot no temp do sistema (fora do perímetro), e o placeholder `<tmp>` só podia ser
preenchido com `$TMPDIR`, `$env:TEMP` ou uma variável `SNAP=...` reaproveitada. Cada comando falhava
duas vezes: path fora do perímetro **e** path que só existe em tempo de execução. A D19/D20
multiplicou o número desses comandos (cópia por execução, `proc` start/status/stop, `docker exec`).

**O erro registrado.** A D16 e a D19 decidiram *onde* executar sem perguntar *como o harness
autoriza* o que é executado. O raciocínio de cada uma estava certo no eixo em que foi feito
(isolamento, posse de processo) e ignorou um terceiro eixo: um comando que ninguém consegue ler
antes de rodar. É o mesmo tipo de erro da primeira versão da D6: uma escolha local correta com um
custo que só aparece no uso.

**Decisão.**
1. **Scratch root em ordem de preferência** (protocolo §1.1): o diretório de scratch que o ambiente
   do agente designa; senão, `.refactor-arch-work/` ao lado do alvo, dentro do perímetro; senão, o
   temp do sistema, **declarado** no relatório (campo `Scratch:`). Fora do alvo e fora de `reports/`
   continua valendo; a D16 muda só de endereço.
2. **Comandos literais** (protocolo §1.4): cada path é resolvido uma vez e colado como absoluto; sem
   `$VAR`, `$env:`, `%VAR%`, `$(...)`, `cd ... &&`, laços; ambiente por `--env`/`-e`; argv em vez de
   `sh -c` no container; leitura de arquivos pelas ferramentas do agente. O que não puder ser escrito
   assim é declarado (`NON-LITERAL` em `## Verification Coverage`).
3. **`proc copy`**: um subcomando novo do `proc` (não um script novo) para toda cópia (snapshot,
   `run-<n>`, `refactored-<n>`). Deixa de fora os diretórios de VCS, recusa destino existente ou
   dentro da origem, e é coberto pelo teste de conformidade nas duas implementações.

**Justificativa.** As duas metades são necessárias: path dentro do perímetro escrito como `$SNAP`
ainda pergunta, e path literal no temp do sistema também. A regra é agnóstica: vale para qualquer
camada de permissão que avalia comandos antes de rodar, e para o humano que os lê. Uma pessoa que
aprova doze comandos opacos seguidos parou de lê-los, e aí a pergunta já não protege nada.

**Alternativas rejeitadas.** *Desligar `blockReadsOutsideWorkingDirectories`* resolve a máquina do
autor e esconde o defeito, que volta na máquina de quem roda a skill com a proteção ligada.
*Adicionar o temp do sistema a `additionalDirectories`* não resolve a expansão de variável e
depende de configuração do usuário. *Um `snapshot.py` separado* duplicaria o par py/mjs e a
conformidade; o `proc` já é a ferramenta de "coisas que a skill faz no host".

**Custo aceito / consequências.** Comandos mais longos e repetitivos (paths absolutos por extenso).
Diretórios de dependência dentro da árvore **nunca são copiados**: a Fase 1 os identifica, cada
`proc copy` os recebe em `--exclude`, e as dependências declaradas são instaladas na cópia que roda.
A lista não fica no `proc` (seria acoplada a ecossistemas); fica no raciocínio do agente, que já
detectou a stack. Custo: toda execução paga uma instalação.

---

## 4. O princípio emergente: a skill nunca degrada em silêncio

> **A skill nunca degrada em silêncio.**
> Quando ela verifica menos, ela declara que verificou menos.

Este princípio **não foi desenhado de antemão**. Ele não estava em §2 junto com a restrição
anti-overfitting, não abriu nenhuma discussão e não foi escrito como regra antes de ser
seguido. Ele foi identificado depois, quando quatro decisões tomadas em momentos diferentes,
sobre problemas diferentes, chegaram à mesma forma de resposta. Vale registrá-lo como
princípio justamente por isso: uma regra que emerge de convergência independente é mais
confiável que uma imposta de cima, porque já vem com quatro casos de uso comprovados.

As quatro convergências:

**D4 — `PRE-EXISTING FAILURE`.** Um ponto de entrada que já falhava antes da refatoração não
é marcado `✗`, porque isso imputaria à refatoração um defeito herdado; e não é marcado `✓`,
porque isso contaria como sucesso algo que não funciona. Recebe um terceiro rótulo, que diz
a verdade: já estava quebrado, continua quebrado, a refatoração não é responsável e a
validação não o cobre. Duas mentiras diferentes evitadas pelo mesmo mecanismo — nomear o
estado real em vez de forçá-lo num binário que não o comporta.

**D6.4 — modo piso declarado.** Sem runtime capaz de processar JSON, a validação cai para
paridade de status code e o relatório **diz** que a validação foi degradada e o que deixou de
ser verificado. Esta convergência nasceu diretamente do erro corrigido em D6: o problema do
fallback `curl` original não era ser fraco, era ser fraco **sob o mesmo rótulo** do caminho
forte.

**D11.1 — adaptação declarada.** Quando o alvo não tem View, as guidelines não fabricam uma
pasta vazia para satisfazer o checklist: aplicam o mapeamento mais próximo e o relatório
**declara** a adaptação e a justificativa. O checklist deixa de ser satisfeito por cerimônia
e passa a ser satisfeito por argumento.

**D13 — verificação upstream pulada, declarada.** Sem rede, a consulta viva não roda; o
relatório diz que a verificação upstream foi pulada e o que deixou de ser coberto, em vez de
omitir e deixar a ausência de findings parecer uma ausência de problemas.

**A razão subjacente.** É a mesma frase que aparece em D6.5 sobre ruído, generalizada: *uma
validação ruidosa é pior que nenhuma, porque custa o mesmo e você para de ler*. O leitor de
um relatório de validação — humano ou agente — calibra confiança pelo histórico. Uma
verificação que às vezes significa uma coisa forte e às vezes uma coisa fraca, sem avisar
qual, treina seu leitor a não confiar em nenhuma das duas. Uma verificação que falha por
motivo errado (dado volátil que mudou, defeito herdado que não é regressão) treina seu leitor
a ignorar falhas. Em ambos os casos, o custo de produzir a verificação foi pago e o benefício
foi perdido — e, pior, a existência dela dá uma sensação de cobertura que a realidade não
sustenta.

Daí a formulação forte, que vale para todo o projeto: **uma validação que não pode falhar, ou
que falha pelo motivo errado, é pior que nenhuma validação** — porque a inexistência é
honesta e a decoração não é.

---

## 5. Nota companheira: as duas armadilhas de medição (D8)

O princípio de §4 trata de não mentir sobre o que foi *verificado*. Esta nota trata do risco
paralelo: não mentir sobre o que foi *medido*. As duas armadilhas abaixo são as razões pelas
quais o scorecard de D8 tem a forma que tem.

**Primeira armadilha: recall é trivialmente manipulável.** Recall mede quantos dos problemas
conhecidos a skill encontrou. Neste projeto, os "problemas conhecidos" são a análise manual
feita pelo próprio autor do catálogo. Basta escrever o catálogo **a partir** dessa análise
para que a skill reencontre 100% do que foi plantado — e o número resultante não diz nada
sobre a skill, diz apenas que ela consegue ler a própria lista. É por isso que a métrica-chave
não é recall, e sim **achados além do gabarito**: quantos problemas legítimos a skill
encontrou que **não** estavam na análise manual. Essa métrica mede o oposto exato — a
capacidade de ver o que o autor do catálogo não viu — e é a única evidência **positiva** de
que a skill generaliza em vez de reproduzir gabarito. É, ponto a ponto, o inverso do risco
descrito na restrição governante de §1.2. (É também a razão pela qual D12 teve que inverter a
ordem de trabalho: sem independência entre catálogo e gabarito, esta métrica é zero por
construção.)

**Segunda armadilha: a métrica-chave é sem sentido sozinha.** Se *achados além do gabarito*
fosse a única coisa medida, "achou 30 problemas" seria recompensado mesmo quando 12 fossem
alucinação — e a maneira mais fácil de maximizar a métrica seria inventar. Por isso
**findings inventados** (citar arquivo/linha que não existe, ou que não contém aquilo) é
contramétrica indispensável, ao lado de **falsos positivos** (apontar código que está
correto). Recall e precisão sempre se medem juntos; medir só um dos lados não é medir mal, é
criar um incentivo na direção errada.

O elo com D13 é direto: a regra do Tier D — conhecimento do modelo nunca é reportável —
existe porque essa é a fonte mais provável de findings inventados nesta skill. Uma afirmação
de deprecation vinda da memória do modelo é plausível, específica, bem formulada e
frequentemente falsa: é o formato exato de uma alucinação bem-sucedida.

---

## 6. Estado do registro

D1–D24 estão decididas (D15–D18 na rodada 2, D19–D23 na rodada 3 e D24 depois dela, ver as notas que as precedem); `CLAUDE.md` §9 não registra perguntas em aberto no momento em que
este documento foi escrito. Duas dessas decisões (D6 e D13) já foram revertidas uma vez, e
o registro das reversões foi mantido deliberadamente: a versão final de cada uma é menos
instrutiva do que o caminho que levou a ela.

Este documento foi escrito **sem** acesso ao código dos três projetos-alvo, por exigência de
D12 — e permanecerá assim. Qualquer revisão futura feita depois da análise manual deve
registrar esse fato explicitamente, porque a partir daí o autor deixa de estar cego e o valor
probatório das decisões tomadas às cegas depende de saber quais foram tomadas antes e quais
depois.

Novas decisões são registradas primeiro em `CLAUDE.md`, que é o documento vivo da
especificação; este registro é atualizado em seguida, com o histórico e o argumento.

**Revisão da rodada 2 (2026-09-21).** D15–D18 e as mudanças menores foram escritas por uma sessão
que leu o relatório da rodada 1, e portanto viu achados concretos dos três projetos, mas não leu o
código deles nem o gabarito. A lista de mudanças foi congelada antes, em
[`round2-changes.md`](rounds/round2-changes.md). As duas entradas novas do catálogo (AP-18, AP-19) vêm do
OWASP Top 10 e deveriam ter estado na versão cega. A entrada delas pela calibração é declarada
aqui, e não escondida.

**Revisão da rodada 3 (2026-09-21).** D19–D23 foram escritas por uma sessão que **leu o gabarito**
e a comparação dele com a rodada 2. A partir desta revisão o autor não está mais cego para os
alvos. A única entrada nova do catálogo (AP-20) vem de Karwin, *SQL Antipatterns*. O recall da
rodada 3 na família que ela cobre é declarado contaminado em
[`round3-changes.md`](rounds/round3-changes.md), e não conta como evidência de generalização.
