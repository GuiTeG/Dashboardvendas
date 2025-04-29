import bcrypt
import json
import streamlit as st

def carregar_usuarios():
    try:
        with open('usuarios.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def salvar_usuarios(usuarios):
    with open('usuarios.json', 'w') as file:
        json.dump(usuarios, file, indent=4)

def criar_hash_senha(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def login(usuarios):
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if usuario in usuarios and bcrypt.checkpw(senha.encode('utf-8'), usuarios[usuario]['senha'].encode('utf-8')):
            return usuarios[usuario].get("papel", "viewer")
        else:
            st.error("Usuário ou senha inválidos!")

def cadastrar_usuario(usuarios):
    st.markdown("<h2>👤 Cadastro de Novo Usuário</h2>", unsafe_allow_html=True)
    
    novo_usuario = st.text_input("Novo nome de usuário")
    nova_senha = st.text_input("Nova senha", type="password")
    confirmar_senha = st.text_input("Confirmar senha", type="password")
    papel = st.selectbox("Tipo de usuário", ["viewer", "admin"])

    if st.button("Cadastrar"):
        if not novo_usuario or not nova_senha:
            st.warning("Preencha todos os campos.")
        elif nova_senha != confirmar_senha:
            st.error("As senhas não coincidem.")
        elif novo_usuario in usuarios:
            st.error("Usuário já existe.")
        else:
            usuarios[novo_usuario] = {
                "senha": criar_hash_senha(nova_senha),
                "papel": papel
            }
            salvar_usuarios(usuarios)
            st.success(f"Usuário '{novo_usuario}' cadastrado com sucesso como '{papel}'!")

def alterar_senha(usuarios):
    st.markdown("<h2>🔒 Alterar Senha</h2>", unsafe_allow_html=True)

    usuario_logado = st.session_state.get("usuario_logado")
    if not usuario_logado:
        st.error("Erro: Usuário não identificado.")
        return

    senha_atual = st.text_input("Senha atual", type="password")
    nova_senha = st.text_input("Nova senha", type="password")
    confirmar_nova_senha = st.text_input("Confirmar nova senha", type="password")

    # Botão de Alteração de Senha com key exclusivo
    if st.button("Alterar Senha", key="alterar_senha_button"):
        if not senha_atual or not nova_senha or not confirmar_nova_senha:
            st.warning("Preencha todos os campos.")
        elif not bcrypt.checkpw(senha_atual.encode('utf-8'), usuarios[usuario_logado]['senha'].encode('utf-8')):
            st.error("Senha atual incorreta.")
        elif nova_senha != confirmar_nova_senha:
            st.error("A nova senha não confere.")
        else:
            usuarios[usuario_logado]['senha'] = criar_hash_senha(nova_senha)
            salvar_usuarios(usuarios)
            st.success("Senha alterada com sucesso.")
