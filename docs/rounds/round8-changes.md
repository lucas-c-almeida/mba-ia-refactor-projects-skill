# Rodada 8 — lista de mudanças congelada

- **Data do congelamento:** 2026-11-10
- **Origem:** revisão da entrega da rodada 7 contra o comentário do avaliador sobre AP-04. A D27 fechou
  as rotas administrativas e os agregados, mas ficou aberta uma operação com o mesmo raciocínio: trocar
  a senha, o papel ou o estado de uma conta qualquer, sem nenhuma credencial.
- **Decisão do autor (2026-11-10):** endurecer a regra e rodar de novo.
- **Regra:** só muda o que é atribuível a esta lista. Restrição permanente (CLAUDE.md §2): sinal
  observável e raciocínio, Teste do Quarto Projeto, sem nome de rota, arquivo, campo ou tabela dos alvos.

## ⚠ Contaminação declarada (D12)

O autor conhece o código, os relatórios e o gabarito dos três alvos, e o caso que motiva a mudança veio
de um deles. Como na rodada 6, a mudança é uma **regra de decisão**: a auditoria já detectava a operação
aberta, e o que muda é a Fase 3 corrigir em vez de propor. O recall não é evidência nova de
generalização, e nenhum quarto projeto é rodado.

## Decisão de desenho: emenda à D27 (D29)

**O raciocínio é o mesmo da exclusão de conta.** Sem modelo de identidade não existe "a conta do próprio
chamador". Quem troca a senha de uma conta escolhida pelo id da requisição não pode estar fazendo
autoatendimento. O novo sinal cobre as quatro formas de **tomar ou bloquear** uma conta existente:

- trocar o segredo que o login confere;
- trocar o identificador pelo qual o login encontra a conta;
- trocar o papel ou as permissões;
- trocar o estado que permite ou impede o login.

**A classificação é por efeito, não por rota.** Uma operação que aceita campos dos dois tipos é dividida
campo a campo. Só o pedido que **muda** um campo privilegiado exige a credencial de operador. O restante
continua operação de negócio, aberta e proposta. Segue a condição que o autor impôs no gate da rodada 7:
reenviar o valor guardado não é mudança.

**Alternativas descartadas.**

- *Proteger a operação inteira:* rejeitaria edição comum de perfil, que clientes legítimos fazem hoje.
  É mudança de contrato, e a D7 proíbe.
- *Incluir todo DELETE de registro de domínio:* contradiz a Emenda 1 da D27. Clientes usam essas rotas
  anonimamente em uso normal, e fechá-las exige decidir quem são os principais.
- *Manter no gate, caso a caso:* foi o que a rodada 7 fez. Deixa a correção depender da resposta de cada
  execução, e o `--yes` cairia em `proposed`.

**Custo aceito.**

- Num alvo sem modelo de identidade, usuários deixam de poder trocar a própria senha sem o operador. É o
  mesmo custo já aceito para a exclusão de conta, e o relatório nomeia a variável que habilita o caminho.
- Incluir o identificador de login faz uma edição de e-mail exigir a credencial quando o e-mail é o
  identificador. Sem isso, um anônimo bloquearia o acesso da vítima sem tocar na senha.

## Mudanças

| # | Mudança | Arquivo |
|---|---|---|
| S1 | Novo sinal de operação privilegiada: tomar ou bloquear conta existente por identificador vindo da requisição, sem modelo de identidade. Operação que exige o segredo atual já verifica credencial e não entra. | `04-architecture-guidelines.md` §6 |
| S2 | Regra de operação mista: classificação por campo, "mudar" é diferir do valor guardado (segredo com hash unidirecional é comparado por verificação), rejeição antes de qualquer escrita. | `04-architecture-guidelines.md` §6 |
| S3 | Lista do que **não** é privilegiado: edição de campos comuns de perfil; cadastro não toca conta existente. | `04-architecture-guidelines.md` §6 |
| S4 | Lista de sinais alinhada e ponteiro para a divisão por campo. | `SKILL.md` §3b |
| S5 | AP-04: sinal de detecção e nota de contrato da operação mista. | `02-antipattern-catalog.md` |
| S6 | RP-04: exceção alinhada e antes/depois da guarda por campo, em stack que não é a de nenhum alvo. | `05-refactoring-playbook.md` |
| S7 | Entradas de inventário da operação mista: anônimo mudando campo privilegiado → `security`/`rejected`; com credencial → entrada comum; campo comum e reenvio do valor guardado sem credencial → entradas comuns. | `06-validation-protocol.md` §2.1 |
| S8 | Registro: D29 em `CLAUDE.md` e `docs/decisions.md`. | documentação |

`probe.py`, `probe.mjs` e `proc` não mudam: as entradas usam tipos já existentes. O teste de
conformidade continua válido.

## Como a rodada roda

1. Lista e edições da skill commitadas em `feat/round8`, nessa ordem.
2. Partida do código original (`7ef5932`), com a skill da rodada 8 por cima. Um worktree e um branch por
   projeto: `.worktrees/r8-p{1,2,3}` e `round8/clean-p{1,2,3}`.
3. Tags: `run/code-smells-project/iter8`, `run/ecommerce-api-legacy/iter8` e `run/task-manager-api/iter10`.
4. Um subagente novo por projeto, sem contexto além da invocação da skill (D3).
5. Gate humano nos três, com a pergunta repassada literalmente. Nenhuma execução com `--yes`.
6. Entrega em `release/delivery-r8`: código, relatórios, cópias da skill (D2.2), README e
   `round8-report.md`.

Os três projetos rodam, embora se espere efeito em poucos deles. O avaliador pediu os três, e a skill
copiada em cada projeto precisa ser a mesma que gerou o relatório dele.

## Critério de saída

- Nos três projetos, nenhuma operação cujo efeito cai num sinal privilegiado termina `proposed` por falta
  de identidade.
- Cada operação coberta por S1 tem entrada anônima `FIXED` e caminho do operador `PASS`.
- Edição comum sem credencial continua `PASS`: a divisão por campo não virou proteção da rota inteira.
- `0 REGRESSION`, `0 NOT ROBUST`, comandos sem `cd` nem encadeamento.
- O caso que na rodada 7 foi ao gate como decisão de privilégio de conta não reaparece como ambíguo.

## Fora desta rodada

- Modelo de identidade, ownership e papéis para operações de negócio (D15).
- DELETE e edição de registros de domínio.
- Papel escolhido no próprio cadastro: é sinal já existente de AP-04, e a regra de cadastro não muda.
- Pendências do `round7-report.md` §7 (verificação independente, scorecards, header de preflight,
  stderr com processo destacado, campo `Root cause of:`).
