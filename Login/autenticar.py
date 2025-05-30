import streamlit as st
import bcrypt
import json
import os
import psycopg2
import subprocess

# === Caminho para o JSON de usuários ===
def get_json_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "..", "Sincronizar", "usuarios.json")

def carregar_usuarios():
    try:
        with open(get_json_path(), 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def salvar_usuarios(usuarios):
    with open(get_json_path(), 'w', encoding='utf-8') as file:
        json.dump(usuarios, file, indent=4)

def criar_hash_senha(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def login(usuarios):
    st.markdown("### 🔐 Login")
    if "usuario" not in st.session_state:
        st.session_state["usuario"] = ""
    if "senha" not in st.session_state:
        st.session_state["senha"] = ""

    usuario = st.text_input("Usuário", value=st.session_state["usuario"])
    st.session_state["usuario"] = usuario

    senha = st.text_input("Senha", type="password", value=st.session_state["senha"])
    st.session_state["senha"] = senha

    if st.button("Entrar"):
        user_data = usuarios.get(usuario)
        if user_data and bcrypt.checkpw(senha.encode('utf-8'), user_data['senha'].encode('utf-8')):
            nome_real = user_data.get("nome", usuario)
            papel = user_data.get("papel", "viewer")
            abas_autorizadas = user_data.get("lojas", [])
            st.session_state.update({
                "usuario_logado": usuario,
                "nome_usuario": nome_real,
                "papel": papel,
                "lojas_autorizadas": abas_autorizadas,
                "logado": True
            })
            st.success(f"Bem-vindo, {nome_real}!")
            return {"tipo": papel, "nome": nome_real}
        else:
            st.error("Usuário ou senha inválidos!")

def cadastrar_usuario(usuarios):
    st.markdown("<h2>👤 Cadastro de Novo Usuário</h2>", unsafe_allow_html=True)

    campos = ["novo_usuario", "novo_nome", "nova_senha", "confirmar_senha", "lojas_input"]
    for campo in campos:
        if campo not in st.session_state:
            st.session_state[campo] = "" if "input" in campo else ""

    novo_usuario = st.text_input("Novo nome de usuário (login)", value=st.session_state["novo_usuario"])
    st.session_state["novo_usuario"] = novo_usuario

    novo_nome = st.text_input("Nome completo do usuário", value=st.session_state["novo_nome"])
    st.session_state["novo_nome"] = novo_nome

    nova_senha = st.text_input("Nova senha", type="password", value=st.session_state["nova_senha"])
    st.session_state["nova_senha"] = nova_senha

    confirmar_senha = st.text_input("Confirmar senha", type="password", value=st.session_state["confirmar_senha"])
    st.session_state["confirmar_senha"] = confirmar_senha

    papel = st.selectbox("Tipo de usuário", ["viewer", "admin"])

    abas_disponiveis = [
    {"id": "painel_unificado_resumido", "nome": "Painel Resumido"},
    {"id": "santo_andre", "nome": "Santo André"},
    {"id": "maua", "nome": "Mauá"},
    {"id": "televendas", "nome": "Televendas"},
    {"id": "ecommerce", "nome": "E-commerce"},
    {"id": "produtos", "nome": "Produtos"},
    {"id": "comparativo_santo_andre", "nome": "Comparativo Santo André"},
    {"id": "comparativo_maua", "nome": "Comparativo Mauá"},
    {"id": "comparativo_televendas", "nome": "Comparativo Televendas"},
    {"id": "comparativo_ecommerce", "nome": "Comparativo E-commerce"},
]

# Mapeia {id: nome} para exibição e seleção
    abas_opcoes = {aba["id"]: aba["nome"] for aba in abas_disponiveis}

    abas_selecionadas = st.multiselect(
    "Selecione as abas autorizadas",
    options=list(abas_opcoes.keys()),
    format_func=lambda x: abas_opcoes[x],
)

   

    if st.button("Cadastrar"):
        if not novo_usuario or not novo_nome or not nova_senha or not abas_selecionadas:
            st.warning("Preencha todos os campos, incluindo pelo menos uma aba.")
        elif nova_senha != confirmar_senha:
            st.error("As senhas não coincidem.")
        elif novo_usuario in usuarios:
            st.error("Usuário já existe.")
        else:
            abas_ids = [item.split(" - ")[0] for item in abas_selecionadas]

            usuarios[novo_usuario] = {
                "nome": novo_nome,
                "senha": criar_hash_senha(nova_senha),
                "papel": papel,
                "lojas": abas_ids,
            }

            salvar_usuarios(usuarios)

            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                sync_script = os.path.join(base_dir, "..", "Sincronizar", "sincronizar_usuarios.py")
                subprocess.call(["python", sync_script])
            except Exception as e:
                st.warning(f"Usuário cadastrado, mas erro ao sincronizar com o banco: {e}")

            st.success(f"Usuário '{novo_nome}' cadastrado com sucesso como '{papel}'!")

            for campo in campos:
                st.session_state[campo] = ""
            st.session_state["menu_config"] = ""
            st.rerun()


def excluir_usuario(usuarios):
    st.markdown("<h2>🗑️ Excluir Usuário</h2>", unsafe_allow_html=True)

    usuarios_disponiveis = [u for u in usuarios.keys() if u != st.session_state["usuario_logado"]]

    if not usuarios_disponiveis:
        st.info("Nenhum usuário disponível para exclusão.")
        return

    usuario_selecionado = st.selectbox("Selecione o usuário para excluir", usuarios_disponiveis)

    if st.checkbox("Confirmo que desejo excluir este usuário permanentemente"):
        if st.button("🚨 Excluir Usuário", type="primary"):
            try:
                usuarios.pop(usuario_selecionado)
                salvar_usuarios(usuarios)

                conn = psycopg2.connect(host="10.100.117.118", dbname="COPAFER_PROD", user="postgres", password="#nfFbt")
                cur = conn.cursor()
                cur.execute("SELECT id FROM usuariosinside WHERE usuario = %s", (usuario_selecionado,))
                res = cur.fetchone()
                if res:
                    usuario_id = res[0]
                    cur.execute("DELETE FROM usuario_lojasinside WHERE usuario_id = %s", (usuario_id,))
                    cur.execute("DELETE FROM usuariosinside WHERE id = %s", (usuario_id,))
                conn.commit()
                cur.close()
                conn.close()

                st.success(f"Usuário '{usuario_selecionado}' excluído com sucesso.")
                st.session_state["menu_config"] = ""
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir usuário: {e}")


def alterar_cadastro(usuarios):
    st.markdown("<h2>💠 Alterar Cadastro</h2>", unsafe_allow_html=True)

    usuario_atual = st.session_state.get("usuario_logado")
    papel = st.session_state.get("papel")
    dados = usuarios.get(usuario_atual)

    if not dados:
        st.error("Usuário não encontrado.")
        return

    novo_nome = st.text_input("Nome completo", value=dados.get("nome", usuario_atual))

    if papel == "admin":
        novo_login = st.text_input("Login (nome de usuário)", value=usuario_atual)
        lojas_input = st.text_input("Abas autorizadas (separadas por vírgula)", value=",".join(dados.get("lojas", [])))
    else:
        novo_login = usuario_atual
        lojas_input = None

    st.markdown("---")
    st.markdown("🔑 <strong>Alterar Senha (opcional)</strong>", unsafe_allow_html=True)

    senha_atual = st.text_input("Senha atual", type="password")
    nova_senha = st.text_input("Nova senha", type="password")
    confirmar_nova_senha = st.text_input("Confirmar nova senha", type="password")

    if st.button("📏 Salvar alterações"):
        if not novo_nome:
            st.warning("O nome não pode ficar em branco.")
            return

        if nova_senha or confirmar_nova_senha:
            if not senha_atual:
                st.warning("Informe a senha atual para alterar a senha.")
                return
            if not bcrypt.checkpw(senha_atual.encode("utf-8"), dados["senha"].encode("utf-8")):
                st.error("Senha atual incorreta.")
                return
            if nova_senha != confirmar_nova_senha:
                st.error("A nova senha e a confirmação não coincidem.")
                return
            senha_hash = criar_hash_senha(nova_senha)
        else:
            senha_hash = dados["senha"]

        if papel == "admin":
            abas = [aba.strip() for aba in lojas_input.split(",") if aba.strip()]

            if novo_login != usuario_atual:
                usuarios.pop(usuario_atual)
            usuarios[novo_login] = {
                "nome": novo_nome,
                "senha": senha_hash,
                "papel": papel,
                "lojas": abas
            }
        else:
            usuarios[usuario_atual]["nome"] = novo_nome
            usuarios[usuario_atual]["senha"] = senha_hash

        salvar_usuarios(usuarios)

        try:
            conn = psycopg2.connect(host="10.100.117.118", dbname="COPAFER_PROD", user="postgres", password="#nfFbt")
            cur = conn.cursor()
            cur.execute("""
                UPDATE usuariosinside SET nome = %s, senha = %s, usuario = %s
                WHERE usuario = %s
            """, (novo_nome, senha_hash, novo_login, usuario_atual))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            st.warning(f"Erro ao atualizar no banco: {e}")
            return

        st.session_state["nome_usuario"] = novo_nome
        if novo_login != usuario_atual:
            st.session_state["usuario_logado"] = novo_login
        if papel == "admin":
            st.session_state["lojas_autorizadas"] = abas

        st.success("Cadastro atualizado com sucesso.")
        st.session_state["menu_config"] = ""
        st.rerun()

__all__ = [
    "login",
    "carregar_usuarios",
    "salvar_usuarios",
    "criar_hash_senha",
    "cadastrar_usuario",
    "excluir_usuario",
    "alterar_cadastro"
]
