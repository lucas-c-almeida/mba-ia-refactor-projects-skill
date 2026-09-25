# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

Refatorado para uma arquitetura em camadas (Models / Views / Controllers) pela skill
`refactor-arch` — ver `reports/audit-latest.md` para o relatório completo de auditoria
e refatoração.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado
automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas
agora armazenadas com hash, não em texto plano).

## Configuração (opcional)

Todas as variáveis abaixo têm um default que preserva o comportamento de boot sem
configuração nenhuma — nenhuma é obrigatória para rodar localmente:

| Variável | Default | Efeito |
|---|---|---|
| `SECRET_KEY` | gerada por processo (efêmera) | Chave de assinatura do Flask. Defina um valor fixo fora de desenvolvimento local. |
| `DB_PATH` | `loja.db` | Caminho do arquivo SQLite. |
| `APP_DEBUG` | `false` | Modo debug do Flask (console interativo). Mantenha `false` fora de desenvolvimento local. |
| `APP_HOST` | `0.0.0.0` | Endereço de bind. |
| `APP_PORT` | `5000` | Porta. |
| `APP_CORS_ALLOW_ALL` | `true` | Política CORS. `true` reproduz o comportamento original (qualquer origem). |

## Estrutura

```
app.py                  ponto de entrada / composition root
src/
├── config/             leitura de configuração (única leitura de ambiente do projeto)
├── models/              entidades, regras e persistência (SQLite parametrizado)
├── controllers/          um caso de uso por método, sem objetos de requisição HTTP
├── views/                rotas Flask: parse -> chama controller -> renderiza
├── middlewares/          tratamento de erro centralizado
└── validation.py         validação de fronteira (schemas simples)
```
