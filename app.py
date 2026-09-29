import os
import sys
import webbrowser
import threading

from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
from datetime import datetime
from db_setup import create_tables, create_connection
import socket

def caminho_recurso(rel_path):
    """Funciona dentro do PyInstaller para arquivos embutidos (templates, static, sons)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, rel_path)

def caminho_dados(rel_path):
    """Caminho persistente para o banco de dados fora do executavel"""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, rel_path)

# Garante que as tabelas existem antes de usar
create_tables()

# Conexão com o banco
conn = create_connection()
cursor = conn.cursor()
app = Flask(
    __name__,
    static_folder=caminho_recurso("static"),
    template_folder=caminho_recurso("templates")
)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
DB = caminho_dados("urna.db")

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# ==================== Admin ====================
@app.route("/admin")
def admin():
    conn = get_db()

    turmas = [dict(r) for r in conn.execute("SELECT * FROM turmas ORDER BY nome").fetchall()]
    cargos = [dict(r) for r in conn.execute("SELECT * FROM cargos ORDER BY ordem").fetchall()]
    candidatos = [dict(r) for r in conn.execute("""
        SELECT c.*, ca.nome AS cargo_nome, t.nome AS turma_nome
        FROM candidatos c
        LEFT JOIN cargos ca ON c.cargo_id = ca.id
        LEFT JOIN turmas t ON c.turma_id = t.id
        ORDER BY t.nome ASC, ca.ordem ASC, CAST(c.numero AS INTEGER) ASC, c.numero ASC
    """).fetchall()]

    urna_ativa_row = conn.execute(
        "SELECT * FROM sessao_votacao ORDER BY id DESC LIMIT 1"
    ).fetchone()

    urna_ativa = bool(urna_ativa_row["ativa"]) if urna_ativa_row else False
    sessao_bloqueada = bool(urna_ativa_row["bloqueada"]) if urna_ativa_row else False
    turma_votacao = (
        urna_ativa_row["turma_id"]
        if urna_ativa_row and urna_ativa_row["turma_id"]
        else None
    )

    # 🔴 BUSCAR NOME DA TURMA
    turma_votacao_nome = "Nenhuma turma selecionada"
    if turma_votacao:
        t = conn.execute(
            "SELECT nome FROM turmas WHERE id=?",
            (turma_votacao,)
        ).fetchone()
        if t:
            turma_votacao_nome = t["nome"]

    # 🔴 PEGAR IP LOCAL
    try:
        ip_local = socket.gethostbyname(socket.gethostname())
    except:
        ip_local = "127.0.0.1"

    conn.close()

    return render_template(
        "admin.html",
        turmas=turmas,
        cargos=cargos,
        candidatos=candidatos,
        urna_ativa=urna_ativa,
        sessao_bloqueada=sessao_bloqueada,
        urna_ativa_row=urna_ativa_row,
        turma_votacao=turma_votacao,
        turma_votacao_nome=turma_votacao_nome,
        ip_local=ip_local
    )

# ==================== CRUD Turma ====================
@app.route("/turma/add", methods=["POST"])
def turma_add():
    nome = request.form.get("nome")
    if not nome:
        return jsonify({"status": "erro", "mensagem": "Preencha o nome da turma!"})

    conn = get_db()
    try:
        conn.execute("INSERT INTO turmas(nome) VALUES(?)", (nome,))
        conn.commit()
        return jsonify({"status": "ok", "mensagem": "Turma adicionada com sucesso!"})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)})
    finally:
        conn.close()

@app.route("/turma/edit", methods=["POST"])
def turma_edit():
    id = request.form.get("id")
    nome = request.form.get("nome")
    if not id or not nome:
        return jsonify({"status":"erro","mensagem":"Preencha todos os campos!"})

    conn = get_db()
    conn.execute("UPDATE turmas SET nome=? WHERE id=?", (nome, id))
    conn.commit()
    conn.close()
    return jsonify({"status":"ok"})

@app.route("/turma/delete/<int:id>")
def turma_delete(id):
    conn = get_db()
    conn.execute("DELETE FROM turmas WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

# ==================== CRUD Cargos ====================
@app.route("/cargo/add", methods=["POST"])
def cargo_add():
    nome = request.form.get("nome")
    max_votos = int(request.form.get("max_votos", 1))
    ordem = int(request.form.get("ordem", 1))

    if not nome:
        return jsonify({"status":"erro","mensagem":"Preencha o nome do cargo!"})

    conn = get_db()
    conn.execute("INSERT INTO cargos(nome,max_votos,ordem) VALUES(?,?,?)", (nome, max_votos, ordem))
    conn.commit()
    conn.close()
    return jsonify({"status":"ok"})

@app.route("/cargo/edit", methods=["POST"])
def cargo_edit():
    id = request.form.get("id")
    nome = request.form.get("nome")
    max_votos = int(request.form.get("max_votos", 1))
    ordem = int(request.form.get("ordem", 1))

    if not id or not nome:
        return jsonify({"status":"erro","mensagem":"Preencha todos os campos!"})

    conn = get_db()
    conn.execute("UPDATE cargos SET nome=?, max_votos=?, ordem=? WHERE id=?", (nome, max_votos, ordem, id))
    conn.commit()
    conn.close()
    return jsonify({"status":"ok"})

@app.route("/cargo/delete/<int:id>")
def cargo_delete(id):
    conn = get_db()
    conn.execute("DELETE FROM cargos WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

# ==================== CRUD Candidatos ====================
@app.route("/candidato/add", methods=["POST"])
def candidato_add():
    nome = request.form.get("nome")
    numero = request.form.get("numero")
    cargo_id = request.form.get("cargo_id")
    turma_id = request.form.get("turma_id")

    if not nome or not numero or not cargo_id or not turma_id:
        return jsonify({"status": "erro", "mensagem": "Preencha todos os campos obrigatórios (incluindo a turma)!"})

    conn = get_db()
    
    # Checa se o número já existe para este cargo nesta turma
    existente = conn.execute(
        "SELECT * FROM candidatos WHERE numero=? AND cargo_id=? AND turma_id=?",
        (numero, cargo_id, turma_id)
    ).fetchone()

    if existente:
        conn.close()
        return jsonify({"status": "erro", "mensagem": "Número já cadastrado para este cargo nesta turma!"})

    # Insere o candidato
    conn.execute(
        "INSERT INTO candidatos(nome, numero, cargo_id, turma_id) VALUES (?, ?, ?, ?)",
        (nome, numero, cargo_id, turma_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route("/candidato/edit", methods=["POST"])
def candidato_edit():
    id = request.form.get("id")
    nome = request.form.get("nome")
    numero = request.form.get("numero")
    cargo_id = request.form.get("cargo_id")
    turma_id = request.form.get("turma_id")

    if not id or not nome or not numero or not cargo_id or not turma_id:
        return jsonify({"status": "erro", "mensagem": "Preencha todos os campos obrigatórios (incluindo a turma)!"})

    conn = get_db()
    
    # Checa se o número já existe para outro candidato do mesmo cargo na mesma turma
    existente = conn.execute(
        "SELECT * FROM candidatos WHERE numero=? AND cargo_id=? AND turma_id=? AND id<>?",
        (numero, cargo_id, turma_id, id)
    ).fetchone()

    if existente:
        conn.close()
        return jsonify({"status": "erro", "mensagem": "Número já cadastrado para este cargo nesta turma!"})

    # Atualiza candidato
    conn.execute(
        "UPDATE candidatos SET nome=?, numero=?, cargo_id=?, turma_id=? WHERE id=?",
        (nome, numero, cargo_id, turma_id, id)
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route("/candidato/delete/<int:id>")
def candidato_delete(id):
    conn = get_db()
    conn.execute("DELETE FROM candidatos WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

# ==================== Urna ====================
@app.route("/urna")
def urna():
    conn = get_db()
    sessao = conn.execute(
        "SELECT * FROM sessao_votacao WHERE ativa=1 ORDER BY id DESC LIMIT 1"
    ).fetchone()

    sessao_ativa = bool(sessao) if sessao else False
    bloqueada = False
    turma_sessao_id = None
    turma_sessao_nome = ""

    if sessao and sessao["turma_id"]:
        bloqueada = bool(sessao["bloqueada"])
        turma_sessao_id = sessao["turma_id"]
        turma_row = conn.execute(
            "SELECT nome FROM turmas WHERE id=?",
            (turma_sessao_id,)
        ).fetchone()
        if turma_row:
            turma_sessao_nome = turma_row["nome"]

        # Candidatos válidos da turma
        candidatos_rows = conn.execute("""
            SELECT * FROM candidatos
            WHERE turma_id = ?
        """, (sessao["turma_id"],)).fetchall()
    else:
        candidatos_rows = []
        sessao_ativa = False

    cargo_ids_validos = set([r["cargo_id"] for r in candidatos_rows])
    if cargo_ids_validos:
        placeholders = ",".join(["?"] * len(cargo_ids_validos))
        cargos_rows = conn.execute(
            f"SELECT * FROM cargos WHERE id IN ({placeholders}) ORDER BY ordem",
            tuple(cargo_ids_validos)
        ).fetchall()
    else:
        cargos_rows = []

    cargos = [dict(r) for r in cargos_rows]

    candidatos = []
    for r in candidatos_rows:
        d = dict(r)
        d["turma_id_nome"] = turma_sessao_nome
        candidatos.append(d)

    conn.close()

    return render_template(
        "urna.html",
        cargos=cargos,
        candidatos=candidatos,
        turma_sessao=turma_sessao_id,
        turma_sessao_nome=turma_sessao_nome,
        sessao_ativa=sessao_ativa,
        sessao_bloqueada=bloqueada
    )

# ==================== Votar ====================
@app.route("/votar", methods=["POST"])
def votar():
    candidato_id = request.form.get("candidato_id")
    cargo_id = request.form.get("cargo_id")
    turma_id = request.form.get("turma_id")
    branco = int(request.form.get("branco", 0))  # 0 = voto normal, 1 = voto em branco

    conn = get_db()

    # Pega a sessão ativa mais recente
    sessao = conn.execute(
        "SELECT * FROM sessao_votacao WHERE ativa=1 ORDER BY id DESC LIMIT 1"
    ).fetchone()

    if not sessao or not sessao["turma_id"] or sessao["bloqueada"]:
        conn.close()
        return jsonify({"status": "erro", "mensagem": "Sessão bloqueada ou não ativa"}), 400

    # Validação do candidato (somente se não for branco)
    if not branco:
        if not candidato_id:
            conn.close()
            return jsonify({"status": "erro", "mensagem": "Candidato não selecionado"}), 400

        candidato = conn.execute(
            "SELECT * FROM candidatos WHERE id=? AND turma_id=?", (candidato_id, sessao["turma_id"])
        ).fetchone()

        if not candidato:
            conn.close()
            return jsonify({"status": "erro", "mensagem": "Candidato inválido para a turma da sessão"}), 400
    else:
        candidato_id = None  # marca como nulo no banco

    # Pega o máximo de votos permitido para o cargo
    max_votos = conn.execute(
        "SELECT max_votos FROM cargos WHERE id=?", (cargo_id,)
    ).fetchone()[0]

    # Conta quantos votos já foram feitos para este cargo na sessão e turma
    votos_atuais = conn.execute(
        "SELECT COUNT(*) FROM votos WHERE sessao_id=? AND cargo_id=? AND turma_id=?",
        (sessao["id"], cargo_id, sessao["turma_id"])
    ).fetchone()[0]

    if votos_atuais >= max_votos:
        conn.close()
        return jsonify({"status": "erro", "mensagem": f"Máximo de votos ({max_votos}) para este cargo atingido"}), 400

    # Insere o voto no banco
    timestamp = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO votos(candidato_id, cargo_id, sessao_id, timestamp, turma_id, branco) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (candidato_id, cargo_id, sessao["id"], timestamp, sessao["turma_id"], branco)
    )
    conn.commit()

    # ================= Bloqueia sessão se todos os cargos da turma atingirem max_votos =================
    cargos_sessao = conn.execute("""
        SELECT DISTINCT c.id, c.max_votos FROM cargos c
        JOIN candidatos cd ON cd.cargo_id = c.id
        WHERE cd.turma_id = ?
    """, (sessao["turma_id"],)).fetchall()

    todos_max = True
    for c in cargos_sessao:
        votos_cargo = conn.execute("""
            SELECT COUNT(*) FROM votos
            WHERE sessao_id=? AND cargo_id=? AND turma_id=?
        """, (sessao["id"], c["id"], sessao["turma_id"])).fetchone()[0]
        if votos_cargo < c["max_votos"]:
            todos_max = False
            break

    if todos_max:
        conn.execute("UPDATE sessao_votacao SET bloqueada=1 WHERE id=?", (sessao["id"],))
        conn.commit()

    conn.close()
    return jsonify({"status": "ok"})


# ==================== Resultados ====================
@app.route("/api/resultados")
def api_resultados():
    conn = get_db()

    # Pega todas as turmas e cargos
    turmas_rows = conn.execute("SELECT * FROM turmas ORDER BY nome").fetchall()
    turmas = [dict(r) for r in turmas_rows]

    cargos_rows = conn.execute("SELECT * FROM cargos ORDER BY ordem").fetchall()
    cargos = [dict(r) for r in cargos_rows]

    resultados = {}

    for turma in turmas:
        turma_tem_dados = False
        turma_resultado = {}

        for cargo in cargos:
            # Pega votos normais
            candidatos = conn.execute("""
                SELECT c.id, c.nome, c.numero, COUNT(v.id) AS votos
                FROM candidatos c
                LEFT JOIN votos v 
                    ON v.candidato_id = c.id AND v.turma_id = c.turma_id
                WHERE c.cargo_id=? AND c.turma_id=?
                GROUP BY c.id
                ORDER BY votos DESC, c.nome ASC
            """, (cargo["id"], turma["id"])).fetchall()

            lista_candidatos = [
                {
                    "nome": c["nome"],
                    "numero": c["numero"],
                    "votos": c["votos"],
                    "max_vencedores": cargo["max_votos"]
                }
                for c in candidatos
            ]

            # Conta votos em branco para este cargo e turma
            votos_branco_row = conn.execute("""
                SELECT COUNT(*) AS votos
                FROM votos
                WHERE cargo_id=? AND turma_id=? AND branco=1
            """, (cargo["id"], turma["id"])).fetchone()
            
            votos_branco = votos_branco_row["votos"] if votos_branco_row else 0

            if votos_branco > 0:
                lista_candidatos.append({
                    "nome": "VOTO EM BRANCO",
                    "numero": "",
                    "votos": votos_branco,
                    "max_vencedores": 0
                })

            if lista_candidatos:
                turma_resultado[cargo["nome"]] = lista_candidatos
                turma_tem_dados = True

        if turma_tem_dados:
            resultados[turma["nome"]] = turma_resultado

    conn.close()
    return jsonify(resultados)

@app.route("/resultados")
def resultados():
    return render_template("resultados.html")

# ==================== Iniciar / Encerrar ====================
@app.route("/iniciar")
def iniciar():
    turma_id = request.args.get("turma_id")
    if not turma_id:
        return redirect("/admin")
    conn = get_db()
    conn.execute("UPDATE sessao_votacao SET ativa=0 WHERE ativa=1")
    conn.execute("INSERT INTO sessao_votacao (ativa, bloqueada, data_inicio, turma_id) VALUES (?, ?, ?, ?)",
                 (1, 0, datetime.now(), turma_id))
    conn.commit()
    conn.close()
    return redirect("/admin")

@app.route("/encerrar")
def encerrar():
    conn = get_db()
    conn.execute("UPDATE sessao_votacao SET ativa=0 WHERE id=(SELECT MAX(id) FROM sessao_votacao)")
    conn.commit()
    conn.close()
    return redirect("/admin")

# ==================== Bloquear / Liberar ====================
@app.route("/sessao/liberar/<int:sessao_id>")
def liberar_sessao(sessao_id):
    conn = get_db()
    conn.execute("UPDATE sessao_votacao SET bloqueada=0 WHERE id=?", (sessao_id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

@app.route("/sessao/bloquear/<int:sessao_id>")
def bloquear_sessao(sessao_id):
    conn = get_db()
    conn.execute("UPDATE sessao_votacao SET bloqueada=1 WHERE id=?", (sessao_id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

# ==================== Reiniciar / Liberar sessão ====================
@app.route("/liberar")
def liberar_votos():
    conn = get_db()
    sessao = conn.execute("SELECT * FROM sessao_votacao WHERE ativa=1 ORDER BY id DESC LIMIT 1").fetchone()
    if not sessao:
        conn.close()
        return redirect("/admin")
    conn.execute("UPDATE sessao_votacao SET bloqueada=0 WHERE id=?", (sessao["id"],))
    conn.commit()
    conn.close()
    return redirect("/admin")

@app.route("/reiniciar")
def reiniciar_sessao():
    conn = get_db()
    sessao = conn.execute("SELECT * FROM sessao_votacao WHERE ativa=1 ORDER BY id DESC LIMIT 1").fetchone()
    if not sessao or not sessao["turma_id"]:
        conn.close()
        return redirect("/admin")
    conn.execute("UPDATE sessao_votacao SET ativa=0 WHERE id=?", (sessao["id"],))
    conn.execute("INSERT INTO sessao_votacao (ativa, bloqueada, data_inicio, turma_id) VALUES (?, ?, ?, ?)",
                 (1, 0, datetime.now(), sessao["turma_id"]))
# ==================== Zerar Votos ====================
@app.route("/admin/zerar_todos_votos", methods=["POST"])
def zerar_todos_votos():
    conn = get_db()
    conn.execute("DELETE FROM votos")
    conn.execute("UPDATE sessao_votacao SET ativa=0, bloqueada=0")
    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "mensagem": "Todos os votos foram apagados com sucesso!"})

@app.route("/admin/zerar_votos_turma", methods=["POST"])
def zerar_votos_turma():
    turma_id = request.form.get("turma_id")
    if not turma_id:
        return jsonify({"status": "erro", "mensagem": "Selecione uma turma válida!"})
    conn = get_db()
    conn.execute("DELETE FROM votos WHERE turma_id=?", (turma_id,))
    conn.execute("UPDATE sessao_votacao SET bloqueada=0 WHERE turma_id=?", (turma_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "mensagem": "Votos da turma apagados com sucesso!"})

# ==================== Status automática ====================
@app.route("/status_urna")
def status_urna():
    conn = get_db()
    sessao = conn.execute("SELECT * FROM sessao_votacao WHERE ativa=1 ORDER BY id DESC LIMIT 1").fetchone()
    if not sessao or not sessao["turma_id"]:
        conn.close()
        return jsonify({"sessao_ativa": False})

    sessao_ativa = bool(sessao["ativa"])
    bloqueada = bool(sessao["bloqueada"])
    turma_sessao_id = sessao["turma_id"]
    turma_sessao_nome = ""

    turma_row = conn.execute("SELECT nome FROM turmas WHERE id=?", (turma_sessao_id,)).fetchone()
    if turma_row:
        turma_sessao_nome = turma_row["nome"]

    candidatos_rows = conn.execute("""
        SELECT * FROM candidatos
        WHERE turma_id = ?
    """, (turma_sessao_id,)).fetchall()

    cargo_ids_validos = set([r["cargo_id"] for r in candidatos_rows])
    if cargo_ids_validos:
        placeholders = ",".join(["?"] * len(cargo_ids_validos))
        cargos_rows = conn.execute(
            f"SELECT * FROM cargos WHERE id IN ({placeholders}) ORDER BY ordem",
            tuple(cargo_ids_validos)
        ).fetchall()
    else:
        cargos_rows = []

    cargos = [dict(r) for r in cargos_rows]
    candidatos = []
    for r in candidatos_rows:
        d = dict(r)
        d["turma_id_nome"] = turma_sessao_nome
        candidatos.append(d)

    conn.close()
    return jsonify({
        "sessao_ativa": sessao_ativa,
        "bloqueada": bloqueada,
        "turma_sessao": turma_sessao_id,
        "turma_sessao_nome": turma_sessao_nome,
        "cargos": cargos,
        "candidatos": candidatos,
        "sessao_id": sessao["id"]
    })

def obter_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "127.0.0.1"
    return ip

def abrir_navegador():
    ip = obter_ip_local()
    webbrowser.open(f"http://{ip}:5000/admin")

from waitress import serve

if __name__ == "__main__":
    ip_local = obter_ip_local()
    print(f">> Servidor rodando em: http://{ip_local}:5000")

    threading.Timer(1.5, abrir_navegador).start()
    serve(app, host="0.0.0.0", port=5000)