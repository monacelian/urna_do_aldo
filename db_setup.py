import os
import sys
import sqlite3

def caminho_dados(rel_path):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, rel_path)

DB = caminho_dados("urna.db")

def create_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")  # importante para chaves estrangeiras
    return conn


def create_tables():
    """Cria todas as tabelas caso não existam."""
    conn = create_connection()
    c = conn.cursor()

    # ================= Turmas =================
    c.execute("""
    CREATE TABLE IF NOT EXISTS turmas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL
    )
    """)

    # ================= Cargos =================
    c.execute("""
    CREATE TABLE IF NOT EXISTS cargos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        max_votos INTEGER DEFAULT 1,
        ordem INTEGER DEFAULT 1
    )
    """)

    # ================= Candidatos =================
    c.execute("""
    CREATE TABLE IF NOT EXISTS candidatos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        numero TEXT NOT NULL,
        cargo_id INTEGER NOT NULL,
        turma_id INTEGER,
        FOREIGN KEY(cargo_id) REFERENCES cargos(id) ON DELETE CASCADE,
        FOREIGN KEY(turma_id) REFERENCES turmas(id) ON DELETE SET NULL
    )
    """)

    # ================= Sessões de Votação =================
    c.execute("""
    CREATE TABLE IF NOT EXISTS sessao_votacao(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ativa INTEGER DEFAULT 0,
        bloqueada INTEGER DEFAULT 0,
        turma_id INTEGER,
        data_inicio TEXT,
        data_fim TEXT,
        descricao TEXT,
        FOREIGN KEY(turma_id) REFERENCES turmas(id) ON DELETE SET NULL
    )
    """)

    # ================= Votos =================
    c.execute("""
    CREATE TABLE IF NOT EXISTS votos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sessao_id INTEGER,
        cargo_id INTEGER,
        candidato_id INTEGER,
        timestamp TEXT,
        turma_id INTEGER,
        branco INTEGER DEFAULT 0,
        FOREIGN KEY(sessao_id) REFERENCES sessao_votacao(id) ON DELETE CASCADE,
        FOREIGN KEY(cargo_id) REFERENCES cargos(id) ON DELETE CASCADE,
        FOREIGN KEY(candidato_id) REFERENCES candidatos(id) ON DELETE CASCADE,
        FOREIGN KEY(turma_id) REFERENCES turmas(id) ON DELETE SET NULL
    )
    """)

    # ================= Garantir coluna branco em bancos antigos =================
    try:
        c.execute("PRAGMA table_info(votos)")
        colunas = [col[1] for col in c.fetchall()]

        if "branco" not in colunas:
            c.execute("ALTER TABLE votos ADD COLUMN branco INTEGER DEFAULT 0")
            print("[OK] Coluna 'branco' adicionada a tabela votos.")
    except Exception as e:
        print("[AVISO] Erro ao verificar/adicionar coluna branco:", e)

    conn.commit()
    conn.close()
    print("[OK] Tabelas criadas ou ja existentes.")


# Evita que o código rode ao importar
if __name__ == "__main__":
    create_tables()