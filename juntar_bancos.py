import sqlite3
import glob
import os

# Pasta com todos os bancos das urnas
PASTA_URNAS = "urnas"
CAMINHO_COMPLETO = os.path.join(os.getcwd(), PASTA_URNAS)

# Banco final
BANCO_FINAL = "resultado_final.db"

# Procurar todos os arquivos .db na pasta urnas
arquivos = glob.glob(os.path.join(CAMINHO_COMPLETO, "*.db"))

if not arquivos:
    print(f"⚠ Nenhum arquivo .db encontrado em {PASTA_URNAS}")
    exit()

# Dicionário para armazenar resultados
# chave = (numero, nome, cargo, turma) : votos
resultado = {}

# ==============================
# LER TODAS AS URNAS
# ==============================

for arquivo in arquivos:
    print(f"Lendo {arquivo}...")
    conn = sqlite3.connect(arquivo)
    cursor = conn.cursor()

    # Consulta votos válidos
    cursor.execute("""
        SELECT 
            c.numero,
            c.nome,
            cg.nome as cargo,
            t.nome as turma,
            COUNT(v.id) as total_votos
        FROM votos v
        JOIN candidatos c ON c.id = v.candidato_id
        JOIN cargos cg ON cg.id = v.cargo_id
        JOIN turmas t ON t.id = v.turma_id
        WHERE v.branco = 0 AND v.candidato_id IS NOT NULL
        GROUP BY t.nome, cg.nome, c.id
    """)

    for numero, nome, cargo, turma, votos in cursor.fetchall():
        key = (numero, nome, cargo, turma)
        resultado[key] = resultado.get(key, 0) + votos

    conn.close()

# ==============================
# SALVAR NO BANCO FINAL
# ==============================

conn_final = sqlite3.connect(BANCO_FINAL)
cursor_final = conn_final.cursor()

# Criar tabela resultado (limpa se já existir)
cursor_final.execute("""
CREATE TABLE IF NOT EXISTS resultado (
    numero TEXT,
    nome TEXT,
    cargo TEXT,
    turma TEXT,
    votos INTEGER
)
""")
cursor_final.execute("DELETE FROM resultado")  # limpa resultados antigos

# Inserir resultados somados
for (numero, nome, cargo, turma), votos in resultado.items():
    cursor_final.execute(
        "INSERT INTO resultado (numero, nome, cargo, turma, votos) VALUES (?, ?, ?, ?, ?)",
        (numero, nome, cargo, turma, votos)
    )

conn_final.commit()

# ==============================
# MOSTRAR RESULTADO NA TELA
# ==============================

# Definir larguras dinâmicas para alinhamento
max_num = max(len(str(num)) for num, *_ in resultado.keys())
max_nome = max(len(nome) for _, nome, *_ in resultado.keys())
max_cargo = max(len(cargo) for *_, cargo, _ in resultado.keys())
max_turma = max(len(turma) for *_, turma in resultado.keys())

header = f"{'Número':<{max_num}}  {'Nome':<{max_nome}}  {'Cargo':<{max_cargo}}  {'Turma':<{max_turma}}  Votos"
print("\n===== RESULTADO FINAL =====\n")
print(header)
print("-" * (len(header)+10))

# Ordenar por turma, cargo, número do candidato
for (numero, nome, cargo, turma), votos in sorted(resultado.items(), key=lambda x: (x[0][3], x[0][2], x[0][0])):
    print(f"{numero:<{max_num}}  {nome:<{max_nome}}  {cargo:<{max_cargo}}  {turma:<{max_turma}}  {votos}")

conn_final.close()

print(f"\n✔ Resultado final gerado no banco '{BANCO_FINAL}' e exibido na tela.")