import json
import psycopg2
import os

# Caminho absoluto para o JSON
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, 'usuarios.json')

# Conexão com o banco
conn = psycopg2.connect(
    host="10.100.117.118",
    dbname="COPAFER_PROD",
    user="postgres",          # <-- Coloque seu usuário real aqui
    password="#nfFbt"      # <-- E sua senha aqui
)
cur = conn.cursor()

try:
    with open(json_path, encoding="utf-8") as f:
        usuarios = json.load(f)

    for usuario, dados in usuarios.items():
        nome = dados.get("nome", usuario)
        senha = dados["senha"]
        papel = dados["papel"]
        lojas = dados["lojas"]

        # Inserir ou atualizar o usuário
        cur.execute("""
            INSERT INTO usuariosinside (nome, usuario, senha, papel)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (usuario) DO UPDATE
            SET nome = EXCLUDED.nome,
                senha = EXCLUDED.senha,
                papel = EXCLUDED.papel
            RETURNING id;
        """, (nome, usuario, senha, papel))
        usuario_id = cur.fetchone()[0]

        # Atualiza as lojas
        cur.execute("DELETE FROM usuario_lojasinside WHERE usuario_id = %s", (usuario_id,))
        for loja_id in lojas:
            cur.execute("""
                INSERT INTO usuario_lojasinside (usuario_id, loja_id)
                VALUES (%s, %s)
            """, (usuario_id, loja_id))

    conn.commit()
    print("✅ Usuários sincronizados com sucesso.")

except Exception as e:
    conn.rollback()
    print("❌ Erro ao sincronizar usuários:", e)

finally:
    cur.close()
    conn.close()
