# Rodada 6 — lista de mudanças congelada

- **Data do congelamento:** 2026-10-08
- **Origem:** mensagem de correção do avaliador sobre a entrega da rodada 5. Os relatórios marcam
  AP-04 como CRITICAL nos 3 projetos, mas a Fase 3 só o propõe: no projeto 1, `reset-db` e `query`
  administrativos continuam abertos a qualquer anônimo, exatamente o Impact que o relatório descreve.
- **Pedido:** (1) ajustar o teste de uso legítimo para que rotas administrativas ou destrutivas sem
  uso anônimo legítimo sejam protegidas ou removidas na Fase 3; (2) rodar a skill de novo nos 3.
- **Regra:** só muda o que é atribuível a esta lista. Restrição permanente (CLAUDE.md §2): escrever
  como sinal observável e raciocínio, passar no Teste do Quarto Projeto, sem nome de rota, arquivo
  ou tabela dos alvos.

## ⚠ Contaminação declarada (D12)

O autor leu os relatórios da rodada 5, que citam as rotas concretas. A mudança é uma **regra de
decisão** (quem é rejeitado), não uma varredura nova: o que a auditoria procura não muda, muda o que
a Fase 3 faz com um finding de AP-04 que já era detectado. Por isso o recall não é afetado; o que
muda é a coluna `resolved` versus `proposed`, e é isso que o scorecard da rodada 6 mede.

## Mudança planejada (D27, emenda à D15)

**Operação privilegiada.** Distinguir, na decisão do gate, operação de **negócio** de operação
**privilegiada**.

| # | Mudança | Arquivo |
|---|---|---|
| W1 | Definição por sinal observável de operação privilegiada: executa consulta/código arbitrário vindo do cliente; destrói ou redefine dados em massa; é de manutenção/diagnóstico; ou expõe dados agregados de todos os principais (relatório gerencial). Nenhum cliente legítimo a chama anonimamente, então o novo bloqueio só atinge uso ilegítimo. | `04-architecture-guidelines.md` §6 |
| W2 | Nova linha na tabela do teste: sem modelo de identidade **e** operação privilegiada → **safe, aplicar**. Sem identidade e operação de negócio → continua contract-changing. Ambíguo → propõe. | `04-architecture-guidelines.md` §6 |
| W3 | Ordem de correção: **remover** da superfície pública quando a operação é intrinsecamente insegura (executa entrada arbitrária) ou reinicia dados; **proteger** com guarda de operador lida de configuração, fail-closed (desligada sem a credencial configurada), comparação em tempo constante, nunca literal no código. A guarda não é um modelo de identidade. | `04-architecture-guidelines.md` §6, `05-refactoring-playbook.md` RP-04 |
| W4 | RP-04 ganha o caminho "operação privilegiada" com antes/depois e `Contract: safe`. | `05-refactoring-playbook.md` |
| W5 | Bullet da Fase 3 alinhado à regra. | `SKILL.md` |
| W6 | AP-04: sinal de detecção "operação privilegiada sem guarda" e nota de contrato. | `02-antipattern-catalog.md` |
| W7 | `Contract:` e a re-auditoria: AP-04 de operação privilegiada não termina em `proposed` por falta de identidade. | `03-report-template.md` |
| W8 | Entrada de segurança para a operação privilegiada: anônimo → rejeitado; com credencial de operador → mesmo shape do baseline. Reaproveita `kind: "security"` (D17). | `06-validation-protocol.md` |

## Fora desta rodada

Modelo de identidade, ownership e papéis para operações de negócio continuam propostas (D15).
