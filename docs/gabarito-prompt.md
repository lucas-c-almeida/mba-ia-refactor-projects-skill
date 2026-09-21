# Prompt da sessão cega do gabarito (rodada 2, passo 1)

**Como usar:**

```bash
git worktree add ../gabarito 6d1ce62
cd ../gabarito
claude
```

Cole o prompt abaixo na sessão nova, sem acrescentar nada. Ele foi escrito para não carregar nenhuma
pista sobre o catálogo da skill nem sobre os achados da rodada 1. Por isso cita só o que o próprio
enunciado já diz, e nenhuma categoria de anti-pattern.

Ao terminar, copie `../gabarito/GABARITO.md` para a seção A do README, revise o conteúdo e remova a
worktree com `git worktree remove ../gabarito`.

---

```text
Você vai fazer uma revisão de código manual, como um engenheiro sênior que acabou de herdar três
projetos legados. O resultado vai servir de gabarito independente, então o valor dele está no seu
julgamento próprio.

Contexto: o README.md na raiz é o enunciado de um desafio. Leia-o inteiro. Execute APENAS a tarefa
da seção "1. Análise Manual dos Projetos". Ignore as seções 2 e 3: você não vai criar skill nem
refatorar nada.

Regras:
- Leia o código-fonte dos três projetos: code-smells-project/, ecommerce-api-legacy/ e
  task-manager-api/. Leia os arquivos inteiros, não trechos.
- Não modifique nenhum arquivo existente. Não rode comandos git que alterem estado. Pode executar
  as aplicações, se quiser confirmar um comportamento, desde que não altere arquivos versionados.
- Não use subagentes. Não pesquise na web por estes projetos.
- Use a escala de severidade definida no README (CRITICAL, HIGH, MEDIUM, LOW), aplicada ao impacto
  real no contexto do projeto.
- Todo problema precisa de evidência: arquivo e intervalo de linhas exatos, que você leu. Se não
  conseguir apontar a linha, não liste.
- O mínimo do enunciado é 5 problemas por projeto (≥1 CRITICAL ou HIGH, ≥2 MEDIUM, ≥2 LOW). Isso é
  um piso, não uma meta: liste tudo o que você considerar um problema real, de segurança, de
  arquitetura, de desempenho ou de qualidade. Não infle a lista com itens duvidosos.

Saída: crie o arquivo GABARITO.md na raiz, em português, com esta estrutura:

## <nome-do-projeto> (<linguagem> / <framework>)

| # | Severidade | Problema | Arquivo:linhas | Por que é relevante |
|---|---|---|---|---|

Dentro de cada projeto, ordene por severidade (CRITICAL → LOW). Depois dos três projetos, inclua
uma tabela de cobertura mínima (≥1 C/H, ≥2 M, ≥2 L, total ≥5 por projeto) e uma seção curta
"Dúvidas", com os itens em que você hesitou na severidade ou em que não teve certeza se eram
problema, e o motivo.
```
