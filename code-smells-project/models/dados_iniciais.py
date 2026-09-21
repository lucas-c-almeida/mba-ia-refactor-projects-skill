"""Dados de exemplo carregados no primeiro boot (documentados no README).

As contas de exemplo com senhas conhecidas são um item PROPOSED, NOT APPLIED (AP-01):
removê-las muda quais logins funcionam para os clientes atuais. As senhas são gravadas
apenas como hash.
"""

PRODUTOS_EXEMPLO = (
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
)

USUARIOS_EXEMPLO = (
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
)


def carregar_se_vazio(conexao, usuarios):
    """Carrega os exemplos só quando não há produtos (mesma condição do original)."""
    if conexao.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] != 0:
        return False
    conexao.executemany(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        PRODUTOS_EXEMPLO,
    )
    usuarios.inserir_varios(USUARIOS_EXEMPLO)
    return True
