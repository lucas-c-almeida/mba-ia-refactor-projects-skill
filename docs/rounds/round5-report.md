# Rodada 5 — validação da D25/D26 com o gate exercitado por pessoa

- **Data:** 2026-09-30 / 2026-10-01
- **Skill:** `feat/round5@7ef5932` (D1–D26). Lista de mudanças congelada em
  [`round5-changes.md`](round5-changes.md) antes da implementação.
- **Branch de execução:** `round5` (um commit por projeto: `78195c9`, o do eal e o do tma, nesta ordem)
- **Tags de partida (D3):** `run/code-smells-project/iter5`, `run/ecommerce-api-legacy/iter5`,
  `run/task-manager-api/iter7`
- **Transcripts (M-3):** [`p1-iter5`](../runs/p1-iter5.md), [`p2-iter5`](../runs/p2-iter5.md),
  [`p3-iter7`](../runs/p3-iter7.md)

## Como a rodada foi executada

- **Sequencial**, um subagente novo por projeto (D3), cada projeto commitado antes do próximo.
- **Sem `--yes`**: cada subagente parou no gate `[y/n]`; o orquestrador levou o resumo ao autor,
  que respondeu `y` nos três; a resposta voltou ao mesmo subagente. Os três relatórios registram
  `human-confirmed: y`. **É a primeira rodada em que a pausa da Fase 2 foi exercitada por pessoa.**
- **Instrução mínima (M-4)**: o subagente recebeu só a skill, o alvo e o pedido de parar no gate.
  Diferente da rodada 4, nenhuma lista extra de proibições. A rodada mede a skill sozinha.
- **Conferência do orquestrador**, em cada projeto: o replay final reclassificado fora da sessão do
  subagente com `probe.py compare --current` (os três idênticos aos relatórios), e a listagem de
  containers vazia.
- **Interrupção**: o subagente do tma parou por limite de uso da API no replay final, foi retomado
  com o contexto intacto, removeu pelo nome os quatro containers vivos e refez o replay do zero.

## Critérios de aceite (`instructions.md`)

| Critério | code-smells-project | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Fase 1 detecta a stack | ✓ Python 3.13 · Flask 3.1.1 · SQLite | ✓ Node 24 · Express 4.22.1 · sqlite3 | ✓ Python 3.13 · Flask 3.0.0 · Flask-SQLAlchemy · SQLite |
| Fase 2 encontra ≥ 5 findings | ✓ 29 | ✓ 17 | ✓ 28 |
| Fase 2 tem ≥ 1 CRITICAL/HIGH | ✓ 12 C · 7 H | ✓ 6 C · 5 H | ✓ 8 C · 7 H |
| Fase 3: a aplicação funciona | ✓ 45 PASS, 0 REGRESSION | ✓ 9 PASS, 0 REGRESSION, 1 UNVERIFIED declarado | ✓ 53 PASS, 0 REGRESSION |

## Rodada 4 → rodada 5

| | csp R4 | csp R5 | eal R4 | eal R5 | tma R4 | tma R5 |
|---|---|---|---|---|---|---|
| Confirmação | `--yes` | **humana** | `--yes` | **humana** | `--yes` | **humana** |
| Findings (C/H/M/L) | 19 (7/6/4/2) | 29 (12/7/6/4) | 17 (7/6/1/3) | 17 (6/5/3/3) | 31 (6/7/14/4) | 28 (8/7/9/4) |
| Entradas no replay | 31 | 54 | 9 | 10 | 27 | 59 |
| Replay | 25 PASS · 1 UNV | **45 PASS** | 8 PASS · 1 diff sancionado | **9 PASS · 1 UNV** | 24 PASS | **53 PASS** |
| Segurança | 5 FIXED | **9 FIXED** | — | **2 FIXED** | 2 FIXED · 1 NOT FIXED | **6 FIXED** |
| Resolvidos | 12/19 | 20/29 | 12/17 | 12/17 | 27/31 | 21/28 |
| Linha `Commands:` | — | ✓ 0 / 0 | — | ✓ 0 / 0 | — | ✓ 0 / 0 |
| Incidentes | 0 (1 bloqueio declarado) | **0** | 0 (laço recusado) | **0** | 1 (`;`) | **0** |

A superfície exercitada cresceu nos três projetos (sobretudo csp e tma). Não houve regressão.

## ⭐ D25/D26 sob teste

| Problema | Correção | Resultado na rodada 5 |
|---|---|---|
| R4-1 encadeamento de `docker` | D25 | ✓ 0 encadeamentos declarados nos três; nenhum bloqueio |
| R4-2 laço de polling | D26 `proc wait` | ✓ prontidão por `proc wait` dentro do container nos três; nenhum laço |
| R4-3 shell reescrevendo caminho de container | D26 shell na Fase 1 | ✓ escolhido e declarado no bloco da Fase 1 (csp, eal) |
| R4-4 violação reflexa | D25 checagem por comando | ✓ 0 `cd` / 0 encadeamentos declarados; nenhum `INCIDENT` |
| R4-5 bloco da Fase 1 ausente | D26 | ✓ impresso antes da Fase 2 e no topo dos três relatórios congelados |
| R4-6 deprecation só no import | D26 camada 1 no caminho real | ✓ tma: `datetime.utcnow` **e** `Query.get` achados já na Fase 2 (na R4, um só na Fase 3a e outro nunca) |
| C-1 ordenação | D26 | ✓ três relatórios em ordem |
| C-2 intervalo de arquivo inteiro | D26 | ✓ `controllers.py:1-292`, `AppManager.js:1-141`: última linha real |

**Aprovações de comando (contadas pelo autor, D24.1): 1 pedido, negado.** O autor não indicou o
projeto nem o comando, e nenhum dos três subagentes reporta comando negado. Ele não pode ser
atribuído. Comparado às rodadas anteriores (dezenas na rodada 3; quatro categorias na rodada 4), é
a menor contagem até agora, mas não é zero, e a causa ficou sem identificação.

## Problemas revelados nesta rodada

- **R5-1 — `proc start` dentro do container (csp, tma).** Dois subagentes tentaram rodar a
  aplicação com `proc start` *dentro* do container. A imagem slim não tem as ferramentas que o
  `proc` usa para registrar a identidade do processo, e ele se recusou (comportamento correto). O
  protocolo não pede isso; o fato de dois subagentes independentes repetirem sugere que o texto
  induz: o `proc` é apresentado como "a" ferramenta de ciclo de vida, e a D26 colocou o `proc wait`
  dentro do container.
- **R5-2 — boot como processo principal do container (csp, tma).** Depois do R5-1, os dois rodaram
  a aplicação como processo principal (`docker run -d ... <boot argv>`), em vez de `run sleep` →
  `exec` (instalação) → `exec -d` (boot). Funciona, cumpre a D25 (sem encadeamento) e tem uma
  vantagem real: a saída da aplicação, inclusive warnings de deprecation, fica em `docker logs`. O
  eal, que usou `exec -d`, perdeu justamente essa saída na Fase 2 (declarado como DEGRADED). O
  protocolo deveria **preferir** esta forma.
- **R5-3 — `unresolved` onde a regra manda `proposed` (eal).** Dois findings foram contados como
  `unresolved (failed)` cujo resto é exatamente o que o gate de contrato segurou (formato de e-mail;
  paginação do relatório). Pela D14.1, são `proposed`. A contagem certa seria 12 / 5 / 0.
- **R5-4 — `sh -c` com redirecionamento no primeiro boot (eal).** Quebra a regra de argv do §1.4,
  não a D25. Declarado pelo próprio subagente. O R5-2 remove o motivo (ler a saída da aplicação).
- **R5-5 — o mesmo achado com dois julgamentos.** Exigir no `PUT` de produto a mesma validação de
  categoria do `POST` foi **proposta** na rodada 4 e **aplicada** na rodada 5 (csp). As duas
  leituras do teste do uso legítimo (D15) são defensáveis; a variação é o dado.
- **R5-6 — recomendação sem verificação (tma), corrigida pelo próprio agente.** A Fase 2 afirmou,
  sem checar, que o upgrade do flask-cors para 4.0.2 não exigia configuração. Na Fase 3 o
  subagente leu as release notes, viu que era falso e corrigiu `audit-latest.md`, mantendo o
  relatório congelado. É conhecimento Tier D vazando para o campo `Recommendation:`. A regra de
  evidência hoje cobre findings, não recomendações.
- **R5-7 — dependência sem manutenção descoberta só na Fase 3 (eal).** O upgrade major do sqlite3
  foi aplicado, replayed e revertido (o binário exige glibc 2.38, ausente na imagem). Ao checar o
  changelog, o subagente viu que o upstream marca o repositório como sem manutenção. A Fase 2 não
  tinha visto. O gate de dependência da D18 funcionou exatamente como desenhado.

## Intervenções

- **Humanas:** três respostas `y` no gate (o objetivo desta rodada, não correção de rumo) e a
  negação de um pedido de aprovação.
- **Do orquestrador:** retomada do subagente do tma depois do limite de uso da API (mesma tarefa,
  com o pedido de encerrar primeiro os containers vivos). Nenhuma correção de conteúdo.

## Conclusão

A skill sozinha, sem a lista de proibições que a rodada 4 recebeu por fora, rodou os três projetos
com 0 regressões, 0 incidentes, 0 `cd`, 0 encadeamentos e prontidão sempre por ferramenta, com o
gate respondido por pessoa. As seis correções da D25/D26 se confirmaram nas três execuções. O que
sobra (R5-1 a R5-7) é ajuste de texto e de classificação, sem efeito nos critérios de aceite, e o
pedido de aprovação negado ainda sem causa.
