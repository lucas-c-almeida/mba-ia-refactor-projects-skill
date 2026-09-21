"""Taxonomia de erros do domínio. Nenhum código HTTP aqui: o mapeamento fica na borda
(middlewares/tratamento_erros.py)."""


class ErroAplicacao(Exception):
    """Base de todos os erros esperados da aplicação."""


class ErroValidacao(ErroAplicacao):
    """Entrada malformada ou que viola uma regra de formato/invariante."""


class NaoEncontrado(ErroAplicacao):
    """O recurso referenciado não existe."""


class RegraNegocioViolada(ErroAplicacao):
    """A operação é bem formada, mas o estado atual do domínio a impede."""


class ErroDependencia(ErroAplicacao):
    """Uma dependência de infraestrutura (banco de dados) falhou."""
