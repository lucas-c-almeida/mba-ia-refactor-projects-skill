# Plano de testes independentes da entrega (`release/delivery-r6`)

- **Objetivo:** verificar, por um agente que não participou da refatoração, que cada projeto entregue
  (a) provisiona do zero, (b) sobe, (c) preserva o contrato público do original, (d) fecha as
  operações privilegiadas da D27 sem fechar as de negócio, (e) não introduziu defeito novo, e (f) não
  carrega mudança acidental no repositório.
- **Independência:** os testes **não** reutilizam o `replay` da skill como prova. As requisições são
  escritas à mão pelo verificador, a partir do código e do README do projeto. O `probe.py` pode ser
  usado só como conferência cruzada, rotulada como tal.
- **Insumos:** worktree `.worktrees/verify-pN` (entrega, `364bd60`) e `.worktrees/orig-pN` (original,
  `7ef5932`). Nada fora do worktree `verify-pN`/`orig-pN`, do scratch e das portas abaixo é alterado.
- **Regra de comandos (CLAUDE.md §0/D25):** um comando por chamada, sem `cd`, sem encadeamento.
- **Portas:** entrega P1 5101, P2 5102, P3 5103; original P1 5201, P2 5202, P3 5203.

## Bloco A — Provisionamento (do zero)

| ID | Teste | Esperado |
|---|---|---|
| A1 | Árvore limpa: `git status` no worktree antes de qualquer coisa | sem alterações |
| A2 | Instalar dependências do manifesto (venv novo / `npm ci`), sem rede além do registry | instala sem erro; versões = manifesto |
| A3 | `.env.example` existe e cobre toda variável lida pelo módulo de configuração (conferir por leitura do código) | nenhuma variável obrigatória sem exemplo |
| A4 | Seed/migração documentada no README roda | termina com exit 0, cria o banco |
| A5 | Comando de boot do README sobe o servidor na porta escolhida | aceita conexão em ≤ 20 s |

## Bloco B — Boot e configuração

| ID | Teste | Esperado |
|---|---|---|
| B1 | Boot **sem** nenhuma variável de ambiente | ou sobe com padrão seguro, ou falha com mensagem clara; nunca stack trace opaco; **registrar qual** |
| B2 | Boot com o `.env.example` preenchido | sobe |
| B3 | Debug desligado por padrão: provocar um erro e inspecionar a resposta | sem stack trace, sem console interativo |
| B4 | Segredos no código: busca por literais atribuídos a identificadores de segredo/senha/token | nenhum literal (fixtures de teste e senhas de seed documentadas são exceção declarada) |

## Bloco C — Contrato público (diferencial contra o original)

Para **cada** rota do original (extrair do código original e do README), enviar a mesma requisição às
duas aplicações e comparar **status e conjunto de chaves/tipos do JSON** (não valores voláteis).

| ID | Teste | Esperado |
|---|---|---|
| C1 | Cada rota de leitura (GET) com id existente e inexistente | mesmo status e shape |
| C2 | Cada rota de escrita com corpo válido | mesmo status e shape |
| C3 | Cada rota de escrita com campo obrigatório ausente | mesmo status (e shape do erro) |
| C4 | Rota inexistente e método não permitido | 404 / 405 equivalentes |
| C5 | CORS: preflight `OPTIONS` e requisição com `Origin` | mesmos headers `Access-Control-*`, exceto os ajustados por upgrade de dependência (registrar) |
| C6 | Diferenças aceitas: listar **toda** divergência observada e classificá-la (intencional/D7, corrigiu bug, regressão) | zero regressões não explicadas |

## Bloco D — Operações privilegiadas (D27) e fronteira com o negócio

| ID | Teste | Esperado |
|---|---|---|
| D1 | Cada rota privilegiada **sem** `X-Operator-Token` e **sem** `OPERATOR_TOKEN` no ambiente | 403 (ou 404 se removida) |
| D2 | Com `OPERATOR_TOKEN` configurado: sem header, header errado, header vazio, header com prefixo/sufixo do token | todos rejeitados (403) |
| D3 | Com `OPERATOR_TOKEN` configurado e header correto | status e shape do original |
| D4 | Rota removida (se houver): `POST`, `GET` e `OPTIONS` | 404 |
| D5 | Rotas de **negócio** continuam abertas (CRUD de domínio, listagens, login, cadastro, checkout) | mesmo comportamento do original |
| D6 | A guarda compara em tempo constante (leitura do código) e lê o token só da configuração | sim; sem literal |
| D7 | Rota privilegiada alcançável por outro caminho (variação de caso, barra final, `//`, método alternativo, `HEAD`) | não contorna a guarda |

## Bloco E — Segurança e robustez

| ID | Teste | Esperado |
|---|---|---|
| E1 | SQL injection: aspas/`' OR '1'='1` em login, busca e criação | sem 500; sem bypass; o dado é tratado como dado |
| E2 | Corpo malformado (JSON inválido, array no lugar de objeto, `null`, tipo errado em cada campo) em cada rota de escrita | 4xx com corpo de erro; **nunca 500 nem queda do processo** |
| E3 | Credenciais/hashes não aparecem em nenhuma resposta (listagens, detalhe, login, health) | campo ausente ou mascarado |
| E4 | `/health` ou equivalente não devolve segredo nem caminho interno | sem segredo |
| E5 | Senha: criar usuário e conferir (por leitura do banco) que o armazenamento é hash com salt; login correto passa, errado falha | sim |
| E6 | Corpo grande e array grande | não derruba o processo |
| E7 | Idempotência/estado: executar a mesma escrita duas vezes (e-mail duplicado, pedido repetido) | sem 500; comportamento coerente |

## Bloco F — Fluxos de negócio ponta a ponta

Por projeto, um roteiro que cria, lê, altera e (onde permitido) apaga, conferindo o **valor** (não só
a forma) em cada passo:

- **P1:** produto → pedido (estoque baixa) → pedido sem estoque → atualizar status → relatório de
  vendas com operador (valores batem com os pedidos criados).
- **P2:** checkout de aluno novo e existente, cartão negado, curso inexistente → relatório financeiro
  com operador (receita e contagem batem; valores em reais, não em centavos) → exclusão de usuário com
  operador.
- **P3:** usuário → categoria → tarefa → filtrar/buscar → mudar status → estatísticas → relatórios com
  operador → exclusão com operador.

## Bloco G — Estrutura e higiene do repositório

| ID | Teste | Esperado |
|---|---|---|
| G1 | MVC: camadas existem, controllers sem acesso direto a SQL, rotas sem regra de negócio (amostragem por leitura) | conforme `04-architecture-guidelines.md` |
| G2 | Arquivos legados removidos; nenhum import quebrado (importar todos os módulos) | sim |
| G3 | Depois de toda a execução: `git status` no worktree | **sem arquivo novo rastreável** (banco, `.env`, logs, `__pycache__`, `node_modules` ignorados) |
| G4 | `.gitignore` do projeto cobre `.env`, banco, `.venv`/`node_modules`, caches | sim |
| G5 | Arquivos de relatório em `reports/` não contêm segredo real (somente fixtures declaradas) | sim |
| G6 | Cópia da skill dentro do projeto idêntica à da raiz do repositório | `diff -rq` vazio |
| G7 | Higiene do repositório inteiro (feita por quem orquestra): arquivos fora do esperado, binários, tamanhos | nada acidental |

## Saída exigida de cada verificador

1. Tabela por ID: comando/requisição resumido, esperado, observado, **PASS / FAIL / NOT RUN**.
2. Lista de divergências contra o original, cada uma classificada.
3. Defeitos encontrados, com passos para reproduzir (não corrigir o código entregue).
4. Declaração do que **não** foi testado e por quê.
5. Confirmação de que todos os processos iniciados foram encerrados.
