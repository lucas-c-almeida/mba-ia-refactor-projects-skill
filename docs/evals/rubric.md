# Rubrica de avaliação de uma rodada (D8)

Cada rodada de um projeto gera um scorecard `run-p<N>-iter<K>.md`, preenchido **depois** da rodada e
contra o gabarito (`docs/gabarito.md`, cópia na seção A do README). O scorecard nunca é preenchido
pela sessão que executou a skill.

## 1. Checklist do enunciado (binário)

Os itens das seções "Validação" e "Critérios de Aceite" de `instructions.md`, marcados só quando
há evidência no relatório da rodada ou nos arquivos de captura (`surface.json`, `baseline.json`,
replays).

## 2. Casamento finding × gabarito

Casar por **categoria + arquivo**, não por contagem (gabarito A.5: o gabarito agrupa ocorrências
numa linha; a skill às vezes divide). Cada item do gabarito recebe um de três estados:

| Estado | Condição |
|---|---|
| ✓ encontrado | Algum finding da Fase 2 trata do mesmo problema, no mesmo arquivo (ou no mesmo trecho, quando o gabarito cita vários) |
| ◐ parcial | O finding cobre parte do item (um dos sub-problemas, ou o problema certo com o arquivo principal diferente), ou o item aparece só como observação dentro de outro finding, sem ser o assunto dele |
| ✗ não encontrado | Nenhum finding trata dele, nem como observação |

Um item que só apareceu depois do gate (achado na Fase 3a ou na re-auditoria como
`missed-in-phase-2`) conta como ◐: a skill viu, mas a auditoria da Fase 2 não.

## 3. Métricas

| Métrica | Como se conta |
|---|---|
| **Recall estrito** | ✓ / itens do gabarito |
| **Recall amplo** | (✓ + ◐) / itens do gabarito |
| **Falsos positivos** | Findings cujo código citado está correto (o problema descrito não existe ali) |
| **Findings inventados** | Findings cujo `File:` aponta arquivo inexistente, ou linhas que não contêm o que a descrição diz. Checado mecanicamente (arquivo existe, intervalo cabe no arquivo) e por leitura da primeira linha do intervalo |
| **Achados além do gabarito** | Findings legítimos (não falsos positivos) sobre um problema que nenhum item do gabarito cobre, nem parcialmente. Divergência de julgamento declarada no gabarito (A.5: "não listei") conta como além do gabarito só quando o gabarito disse não ter verificado, nunca quando disse ter decidido não listar |
| **Regressões** | `REGRESSION` no replay final, separando as sancionadas pelo contrato de erro (D22) |
| **Intervenções humanas** | Correções de rumo feitas por pessoa durante a execução |

## 4. O que o scorecard não mede

Qualidade do código refatorado além do que o replay e a re-auditoria verificam; e cobertura da
superfície pública, que é a própria skill que enumera. As duas lacunas são declaradas no
scorecard, não compensadas por estimativa.
