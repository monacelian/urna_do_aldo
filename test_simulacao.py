import os
import sys
import sqlite3
from app import app, get_db

def run_tests():
    print("=" * 60)
    print(" INICIANDO TESTE COMPLETO DO SISTEMA DA URNA ELETRONICA")
    print("=" * 60)

    client = app.test_client()

    # 1. Limpar banco para comecar teste limpo
    conn = get_db()
    conn.execute("DELETE FROM votos")
    conn.execute("DELETE FROM candidatos")
    conn.execute("DELETE FROM cargos")
    conn.execute("DELETE FROM turmas")
    conn.execute("DELETE FROM sessao_votacao")
    conn.commit()
    conn.close()
    print("[OK] [1/7] Banco de dados limpo com sucesso.")

    # 2. Cadastrar Turmas
    turmas_teste = ["6o Ano A", "7o Ano B", "8o Ano C"]
    turma_ids = {}
    for t_nome in turmas_teste:
        res = client.post("/turma/add", data={"nome": t_nome})
        data = res.get_json()
        assert data["status"] == "ok", f"Erro ao adicionar turma {t_nome}: {data}"
    
    conn = get_db()
    for row in conn.execute("SELECT id, nome FROM turmas").fetchall():
        turma_ids[row["nome"]] = row["id"]
    conn.close()
    print(f"[OK] [2/7] Turmas cadastradas: {turma_ids}")

    # 3. Cadastrar Cargos
    res = client.post("/cargo/add", data={"nome": "Representante de Turma", "max_votos": 1, "ordem": 1})
    assert res.get_json()["status"] == "ok"
    res = client.post("/cargo/add", data={"nome": "Vice-Representante", "max_votos": 1, "ordem": 2})
    assert res.get_json()["status"] == "ok"

    cargo_ids = {}
    conn = get_db()
    for row in conn.execute("SELECT id, nome FROM cargos").fetchall():
        cargo_ids[row["nome"]] = row["id"]
    conn.close()
    print(f"[OK] [3/7] Cargos cadastrados: {cargo_ids}")

    # 4. Cadastrar Candidatos por Turma
    candidatos_esperados = [
        # 6o Ano A
        {"nome": "Ana Clara", "numero": "10", "cargo": "Representante de Turma", "turma": "6o Ano A"},
        {"nome": "Bruno Souza", "numero": "20", "cargo": "Representante de Turma", "turma": "6o Ano A"},
        {"nome": "Carlos Eduardo", "numero": "11", "cargo": "Vice-Representante", "turma": "6o Ano A"},
        {"nome": "Daniela Lima", "numero": "22", "cargo": "Vice-Representante", "turma": "6o Ano A"},
        
        # 7o Ano B (mesmos numeros 10 e 20 para testar isolamento de turma)
        {"nome": "Eduardo Ramos", "numero": "10", "cargo": "Representante de Turma", "turma": "7o Ano B"},
        {"nome": "Fernanda Silva", "numero": "20", "cargo": "Representante de Turma", "turma": "7o Ano B"},
        {"nome": "Gabriel Rocha", "numero": "11", "cargo": "Vice-Representante", "turma": "7o Ano B"},
    ]

    candidato_ids = {}
    for c in candidatos_esperados:
        t_id = turma_ids[c["turma"]]
        cg_id = cargo_ids[c["cargo"]]
        res = client.post("/candidato/add", data={
            "nome": c["nome"],
            "numero": c["numero"],
            "cargo_id": cg_id,
            "turma_id": t_id
        })
        assert res.get_json()["status"] == "ok", f"Erro ao adicionar candidato {c['nome']}: {res.get_json()}"

    conn = get_db()
    for row in conn.execute("SELECT id, nome, numero, turma_id FROM candidatos").fetchall():
        candidato_ids[(row["nome"], row["turma_id"])] = row["id"]
    conn.close()
    print(f"[OK] [4/7] Candidatos cadastrados com sucesso ({len(candidato_ids)} candidatos vinculados as turmas).")

    # 5. Simular Votacao - Turma 6o Ano A
    t6_id = turma_ids["6o Ano A"]
    res = client.get(f"/iniciar?turma_id={t6_id}")
    assert res.status_code == 302

    res = client.get("/status_urna")
    st = res.get_json()
    assert st["sessao_ativa"] == True
    assert st["turma_sessao"] == t6_id
    assert st["turma_sessao_nome"] == "6o Ano A"
    print("[OK] [5/7] Sessao iniciada para 6o Ano A.")

    # Aluno 1: Vota em Ana Clara (10) e Carlos Eduardo (11)
    cand_ana = candidato_ids[("Ana Clara", t6_id)]
    cand_carlos = candidato_ids[("Carlos Eduardo", t6_id)]
    rep_id = cargo_ids["Representante de Turma"]
    vice_id = cargo_ids["Vice-Representante"]

    res1 = client.post("/votar", data={"candidato_id": cand_ana, "cargo_id": rep_id, "turma_id": t6_id, "branco": 0})
    assert res1.get_json()["status"] == "ok"
    res2 = client.post("/votar", data={"candidato_id": cand_carlos, "cargo_id": vice_id, "turma_id": t6_id, "branco": 0})
    assert res2.get_json()["status"] == "ok"

    # Checar se sessao bloqueou apos o ultimo cargo
    res = client.get("/status_urna")
    st = res.get_json()
    assert st["bloqueada"] == True
    print("[OK] Bloqueio automatico de seguranca da urna funcionou apos o aluno votar!")

    # Testar REINICIAR SESSAO para o proximo aluno
    res = client.get("/reiniciar")
    assert res.status_code == 302, f"Reiniciar retornou {res.status_code}"
    
    res = client.get("/status_urna")
    st = res.get_json()
    assert st["sessao_ativa"] == True
    assert st["bloqueada"] == False
    print("[OK] Funcao 'Reiniciar Sessao' destravou a urna perfeitamente para o proximo eleitor!")

    # Aluno 2: Vota em Ana Clara (10) e Branco para Vice
    res1 = client.post("/votar", data={"candidato_id": cand_ana, "cargo_id": rep_id, "turma_id": t6_id, "branco": 0})
    assert res1.get_json()["status"] == "ok"
    res2 = client.post("/votar", data={"cargo_id": vice_id, "turma_id": t6_id, "branco": 1})
    assert res2.get_json()["status"] == "ok"

    # Reiniciar para Aluno 3
    client.get("/reiniciar")
    # Aluno 3: Vota em Bruno Souza (20) e Daniela Lima (22)
    cand_bruno = candidato_ids[("Bruno Souza", t6_id)]
    cand_daniela = candidato_ids[("Daniela Lima", t6_id)]
    client.post("/votar", data={"candidato_id": cand_bruno, "cargo_id": rep_id, "turma_id": t6_id, "branco": 0})
    client.post("/votar", data={"candidato_id": cand_daniela, "cargo_id": vice_id, "turma_id": t6_id, "branco": 0})

    # Encerrar 6o Ano A
    client.get("/encerrar")

    # Iniciar e Votar na Turma 7o Ano B
    t7_id = turma_ids["7o Ano B"]
    client.get(f"/iniciar?turma_id={t7_id}")
    cand_eduardo = candidato_ids[("Eduardo Ramos", t7_id)]
    cand_gabriel = candidato_ids[("Gabriel Rocha", t7_id)]
    
    # Aluno do 7o Ano B vota
    client.post("/votar", data={"candidato_id": cand_eduardo, "cargo_id": rep_id, "turma_id": t7_id, "branco": 0})
    client.post("/votar", data={"candidato_id": cand_gabriel, "cargo_id": vice_id, "turma_id": t7_id, "branco": 0})
    client.get("/encerrar")

    # 6. Conferir Apuracao de Resultados
    res = client.get("/api/resultados")
    apuracao = res.get_json()
    print("[OK] [6/7] Conferindo Apuracao:")
    print("   --- 6o Ano A ---")
    rep_6a = apuracao["6o Ano A"]["Representante de Turma"]
    for c in rep_6a:
        print(f"      * {c['nome']} (No {c['numero']}): {c['votos']} voto(s)")
    
    assert rep_6a[0]["nome"] == "Ana Clara" and rep_6a[0]["votos"] == 2
    assert rep_6a[1]["nome"] == "Bruno Souza" and rep_6a[1]["votos"] == 1

    vice_6a = apuracao["6o Ano A"]["Vice-Representante"]
    for c in vice_6a:
        print(f"      * {c['nome']} (No {c['numero']}): {c['votos']} voto(s)")
    nomes_vice = {c["nome"]: c["votos"] for c in vice_6a}
    assert nomes_vice["Carlos Eduardo"] == 1
    assert nomes_vice["Daniela Lima"] == 1
    assert nomes_vice["VOTO EM BRANCO"] == 1

    print("   --- 7o Ano B ---")
    rep_7b = apuracao["7o Ano B"]["Representante de Turma"]
    for c in rep_7b:
        print(f"      * {c['nome']} (No {c['numero']}): {c['votos']} voto(s)")
    assert rep_7b[0]["nome"] == "Eduardo Ramos" and rep_7b[0]["votos"] == 1

    # 7. Testar Deletar / Zerar Votos
    print("[OK] [7/7] Testando exclusao e zeresima de votos:")
    
    # 7.1 Zerar apenas votos do 6o Ano A
    res = client.post("/admin/zerar_votos_turma", data={"turma_id": t6_id})
    assert res.get_json()["status"] == "ok"
    
    # Conferir se 6o Ano A ficou com 0 votos e 7o Ano B manteve os votos
    res = client.get("/api/resultados")
    apuracao_pos_zerar_turma = res.get_json()
    assert "6o Ano A" not in apuracao_pos_zerar_turma or all(c["votos"] == 0 for cargo in apuracao_pos_zerar_turma.get("6o Ano A", {}).values() for c in cargo)
    assert apuracao_pos_zerar_turma["7o Ano B"]["Representante de Turma"][0]["votos"] == 1
    print("   [OK] Zerar votos de turma especifica funcionou perfeitamente (6o Ano A zerado, 7o Ano B preservado).")

    # 7.2 Zerar TODOS os votos (Zeresima Geral)
    res = client.post("/admin/zerar_todos_votos")
    assert res.get_json()["status"] == "ok"

    res = client.get("/api/resultados")
    apuracao_final = res.get_json()
    for turma, cargos in apuracao_final.items():
        for cargo, cands in cargos.items():
            for c in cands:
                assert c["votos"] == 0, f"Candidato {c['nome']} ainda tem votos!"
    print("   [OK] Zeresima Geral: Todos os votos foram zerados com sucesso mantendo os cadastros intactos.")

    print("=" * 60)
    print(" TODOS OS TESTES PASSARAM COM 100% DE SUCESSO! ")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
