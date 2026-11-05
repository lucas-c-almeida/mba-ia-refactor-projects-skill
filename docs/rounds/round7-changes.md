# Rodada 7 — lista de mudanças congelada

- **Data do congelamento:** 2026-11-04
- **Origem:** [`round6-skill-results.md`](round6-skill-results.md) (G1–G10), que consolida os relatórios
  da skill na rodada 6, a verificação independente
  ([`delivery-test-report.md`](../verification/delivery-test-report.md)) e a Parte 2 do
  [`gabarito`](../gabarito.md).
- **Meta:** a skill passa a tratar todos os erros listados; a rodada 7 é a entrega limpa.
- **Regra:** só muda o que é atribuível a esta lista. Restrição permanente (CLAUDE.md §2): sinal
  observável e raciocínio, Teste do Quarto Projeto, sem nome de rota, arquivo, campo ou tabela dos alvos.

## ⚠ Contaminação declarada (D12)

O autor leu o código, os relatórios e o gabarito dos três alvos, e a Parte 2 do gabarito nasceu das
próprias execuções. Diferente da rodada 6, esta rodada **muda o que a auditoria procura** (G4, G8),
então o recall da rodada 7 sobre os três alvos **não** é evidência de generalização: mede só se a
skill passou a pegar o que já sabíamos que existia. A métrica ⭐ (achados além do gabarito) fica
declarada como contaminada.

**Decisão do autor (2026-11-04):** não rodar um quarto projeto nesta rodada. Custo aceito: a rodada 7
não produz evidência nova de generalização; a defesa contra overfitting fica só no Teste do Quarto
Projeto aplicado ao texto.

## Decisão de desenho: a matriz de robustez é gerada pelo harness

**Escolhida (autor, 2026-11-04):** o agente declara os **campos** de cada operação; `probe.py`/`probe.mjs`
expandem a matriz de forma determinística, e o teste de conformidade cobre a expansão.

**Alternativa descartada:** o agente escreve cada variante em `surface.json`. Mais barato de
implementar, mas a cobertura varia por execução: é exatamente a falha do G1 (validação aplicada só onde
alguém olhou), deslocada da Fase 3 para o inventário.
**Custo aceito:** mais código de harness, em duas implementações que precisam ficar byte-compatíveis.

## Mudanças

| # | Origem | Mudança | Arquivo |
|---|---|---|---|
| R1 | G1 | **Inventário entrada → destino.** Na Fase 3, todo valor derivado da requisição (corpo, query, caminho, header) que chega a uma operação sensível ao tipo (driver, aritmética, método de texto/coleção, tamanho, indexação, desserialização) recebe checagem de **tipo e faixa** na borda, cite a Fase 2 o campo ou não. | `04-architecture-guidelines.md` §6, `05-refactoring-playbook.md` RP-11, `SKILL.md` §3 |
| R2 | G1, G2 | **Entrada `kind: "robustness"`.** O agente declara `fields` (`in`: body/query/path/header, `name`, `type`); o harness gera as variantes: omitido, `null`, texto, número, booleano, lista, objeto vazio, objeto aninhado e, para campo numérico, zero, negativo, máximo de 64 bits, máximo + 1, não finito. Ids derivados `<id>#<campo>=<variante>`, determinísticos. Rodam depois das entradas de contrato e de segurança. | `06-validation-protocol.md` §2.3, `probe.py`, `probe.mjs` |
| R3 | G1, G2 | **Estados de robustez:** `ROBUST` (replay sem 5xx e sem queda); `REGRESSION` (baseline sem falha, replay com falha: correção que introduziu 5xx); `NOT ROBUST` (baseline e replay com falha: pré-existente que a validação de borda devia ter fechado; conta como finding `unresolved` de AP-11). Compara-se só a classe de status, nunca o shape: endurecer 2xx → 4xx em tipo errado é seguro (D15). `REGRESSION` e `NOT ROBUST` dão exit 1. | `06-validation-protocol.md` §4.4, `probe.*` |
| R4 | G2 | **Parametrizar exige faixa.** RP-02: ao trocar concatenação por parâmetro, acrescentar na borda o limite de faixa do tipo de destino e a rejeição de não finito. | `05-refactoring-playbook.md` RP-02 |
| R5 | G3 | **Entrada `kind: "value"`.** Asserções sobre caminhos do JSON (`equals`, `matches`, `absent`, `sameAsBaseline`) para o que a transformação mexe em **valor** (dinheiro, ordenação, campo mascarado, campo removido). Estados `HOLDS` / `VIOLATED` / `UNVERIFIED`; `VIOLATED` dá exit 1. Toda verificação "à mão" vira entrada `value` ou é `UNVERIFIED` na linha de replay, nunca só prosa. | `06-validation-protocol.md` §2.4/§4.5, `probe.*`, `03-report-template.md` |
| R6 | G4 | **Livro de sinais.** A Fase 2 emite uma linha por sinal do catálogo: arquivos examinados, ocorrências, destino (finding `<id>` ou `descartado: <motivo>`). Coerência: nada da tabela de cobertura (advisory, hit de varredura) fica fora dos findings. `missed-in-phase-2` por sinal já catalogado é defeito de recall e entra no scorecard. | `03-report-template.md`, `SKILL.md` §2 |
| R7 | G5 | **Defaults e artefatos.** (a) Exemplo de segredo vazio ou inválido por construção, e a guarda rejeita o placeholder. (b) `.env.example` só com carregador ligado (dependência nova = proposta); senão o arquivo é rotulado lista de variáveis e o README diz "exporte". (c) A Fase 3 cria ou preserva o arquivo de exclusão do VCS do alvo, cobrindo segredo local, banco, caches, ambiente e dependências instaladas. (d) Caminho persistido vindo de configuração resolve contra a raiz do projeto, não contra o CWD. | `04-architecture-guidelines.md` §6, RP-01, RP-17 |
| R8 | G6 | **Segredos fora dos artefatos.** Em `surface.json`, todo valor de campo/header cujo nome casa o padrão de segredo é escrito como `{{env:NOME}}`; o harness substitui a partir do ambiente (`--env`) ao enviar e falha com exit 2 se faltar. O relatório lista as fixtures. | `06-validation-protocol.md` §2, `probe.*` |
| R9 | G7 | **Ambiguidades de classificação no gate.** A Fase 2 lista as operações cuja classificação privilegiada/negócio é ambígua (operação, critério, as duas decisões); a pessoa decide no gate; a Fase 3 aplica e registra. "Ambíguo → propõe" só vale em `--yes`. | `SKILL.md` §2, `03-report-template.md`, `04-architecture-guidelines.md` §6 |
| R10 | G8 | **AP-17:** trilha de auditoria/log append-only não é código morto; exige "sem leitor **e** sem propósito declarado". **D14.1/RP-08:** resíduo que só ação de operador resolve é `proposed`, com o passo operacional descrito. | `02-antipattern-catalog.md`, `05-refactoring-playbook.md`, `03-report-template.md` |
| R11 | G9 | **Ciclo de vida.** (a) Processo sem hora de início legível: o handle é o container removido pelo nome exato; caminho coberto pelo teste de conformidade. (b) Identificador de execução aleatório em rótulo de container, scratch e nome de arquivo. | `06-validation-protocol.md` §1.3, `proc.py`, `proc.mjs`, `tests/probe-conformance/` |
| R12 | G10 | Sem mudança de regra: defeitos pré-existentes que o gate de contrato segura continuam `proposed` e visíveis. Entrada malformada não é regra de produto: cai em R1. | — |

## Critério de saída (de `round6-skill-results.md` §5.6)

- zero 5xx em entrada malformada no verificador independente, e zero `NOT ROBUST`/`REGRESSION` na matriz;
- zero defeito introduzido;
- todos os itens da Parte 2 detectados pela Fase 2 ou, se de origem `V`, tratados;
- `git status` limpo e sem segredo nos artefatos;
- nenhuma execução com `--yes` na evidência: três sessões novas, uma por projeto, gate humano.

## Fora desta rodada

Quarto projeto (decisão acima). Modelo de identidade, ownership e regras de produto (D15, G10).
