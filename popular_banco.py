import os
import sys
import sqlite3
from datetime import datetime
from db_setup import create_tables, create_connection
from app import get_db

def popular():
    create_tables()
    conn = get_db()

    # Limpar dados anteriores
    conn.execute("DELETE FROM votos")
    conn.execute("DELETE FROM candidatos")
    conn.execute("DELETE FROM cargos")
    conn.execute("DELETE FROM turmas")
    conn.execute("DELETE FROM sessao_votacao")
    conn.commit()

    # Inserir Turmas
    turmas = [
        "6º Ano A",
        "7º Ano A",
        "8º Ano A",
        "9º Ano A",
        "1º Ano Médio",
        "2º Ano Médio",
        "3º Ano Médio"
    ]
    turma_map = {}
    for t in turmas:
        cur = conn.execute("INSERT INTO turmas (nome) VALUES (?)", (t,))
        turma_map[t] = cur.lastrowid

    # Inserir Cargos
    cargos = [
        ("Representante de Turma", 1, 1),
        ("Vice-Representante", 1, 2)
    ]
    cargo_map = {}
    for nome, max_v, ordem in cargos:
        cur = conn.execute("INSERT INTO cargos (nome, max_votos, ordem) VALUES (?, ?, ?)", (nome, max_v, ordem))
        cargo_map[nome] = cur.lastrowid

    # Inserir Candidatos para as turmas
    candidatos = [
        # 6º Ano A
        ("Lucas Gabriel", "10", cargo_map["Representante de Turma"], turma_map["6º Ano A"]),
        ("Beatriz Santos", "20", cargo_map["Representante de Turma"], turma_map["6º Ano A"]),
        ("Matheus Oliveira", "11", cargo_map["Vice-Representante"], turma_map["6º Ano A"]),
        ("Mariana Costa", "22", cargo_map["Vice-Representante"], turma_map["6º Ano A"]),

        # 7º Ano A (demonstrando reutilização de números em salas diferentes)
        ("Pedro Henrique", "10", cargo_map["Representante de Turma"], turma_map["7º Ano A"]),
        ("Camila Rodrigues", "20", cargo_map["Representante de Turma"], turma_map["7º Ano A"]),
        ("Gustavo Alves", "11", cargo_map["Vice-Representante"], turma_map["7º Ano A"]),
        ("Larissa Fernandes", "22", cargo_map["Vice-Representante"], turma_map["7º Ano A"]),

        # 8º Ano A
        ("Rafael Silva", "1", cargo_map["Representante de Turma"], turma_map["8º Ano A"]),
        ("Juliana Martins", "2", cargo_map["Representante de Turma"], turma_map["8º Ano A"]),
        ("Felipe Souza", "10", cargo_map["Vice-Representante"], turma_map["8º Ano A"]),
        ("Amanda Lima", "20", cargo_map["Vice-Representante"], turma_map["8º Ano A"]),

        # 1º Ano Médio
        ("Gabriel Torres", "12", cargo_map["Representante de Turma"], turma_map["1º Ano Médio"]),
        ("Sophia Pereira", "15", cargo_map["Representante de Turma"], turma_map["1º Ano Médio"]),
        ("Enzo Dias", "13", cargo_map["Vice-Representante"], turma_map["1º Ano Médio"]),
        ("Helena Castro", "16", cargo_map["Vice-Representante"], turma_map["1º Ano Médio"]),
    ]

    for nome, num, c_id, t_id in candidatos:
        conn.execute("INSERT INTO candidatos (nome, numero, cargo_id, turma_id) VALUES (?, ?, ?, ?)",
                     (nome, num, c_id, t_id))

    # Iniciar sessão com a primeira turma (6º Ano A) pronta para votar
    conn.execute("INSERT INTO sessao_votacao (ativa, bloqueada, data_inicio, turma_id) VALUES (?, ?, ?, ?)",
                 (1, 0, datetime.now(), turma_map["6º Ano A"]))

    conn.commit()
    conn.close()
    print("[OK] Banco de dados populado com sucesso com turmas, cargos e candidatos!")
    print("[OK] Turma inicial ativa: 6o Ano A")

if __name__ == "__main__":
    popular()
