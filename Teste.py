import streamlit as st
import psycopg2
from login import login, cadastrar_usuario, carregar_usuarios, alterar_senha
from dashboard import mostrar_kpi
from comparativo import comparativo_12_meses

# Configuração da página
st.set_page_config(page_title="Dashboard de Fluxo", layout="wide")

# Carregar usuários do arquivo
usuarios = carregar_usuarios()

# Sessão
if "logado" not in st.session_state:
    st.session_state["logado"] = False
    st.session_state["tipo_usuario"] = ""

if "menu_config" not in st.session_state:
    st.session_state["menu_config"] = ""

# --- TELA DE LOGIN ---
if not st.session_state["logado"]:
    st.title("Login - Dashboard de Fluxo")
    menu_login = st.sidebar.radio("Acesso", ["Entrar"])

    if menu_login == "Entrar":
        tipo_usuario = login(usuarios)
        if tipo_usuario:
            st.session_state["logado"] = True
            st.session_state["tipo_usuario"] = tipo_usuario
            st.session_state["usuario_logado"] = tipo_usuario
            st.rerun()

# --- DASHBOARD PROTEGIDO ---
if st.session_state["logado"]:
    # Layout superior com o botão de logout e engrenagem
    col1, col2 = st.columns([8, 1])  # Ajuste para os botões ficarem alinhados

    with col1:
        st.title("📊 Dashboard de Fluxo")

    with col2:
        # Botão de Logout
        if st.button("Logout", key="logout_button"):
            st.session_state["logado"] = False
            st.session_state["tipo_usuario"] = ""
            st.session_state["usuario_logado"] = ""
            st.session_state["menu_config"] = ""
            st.rerun()

        # Engrenagem para configurações
        with st.expander("⚙️", expanded=False):
            if st.session_state["tipo_usuario"] == "admin":
                if st.button("Cadastrar Novo Usuário", key="cadastrar_usuario_button"):
                    st.session_state["menu_config"] = "cadastrar"
            if st.button("Alterar Senha", key="alterar_senha_button"):
                st.session_state["menu_config"] = "senha"

    # Mensagem de boas-vindas
    st.sidebar.text(f"Bem-vindo, {st.session_state['tipo_usuario'].capitalize()}!")

    # Menu lateral principal
    menu = st.sidebar.selectbox("Menu", ["KPI", "Comparativo 12 meses"])

    # Conexão com banco
    conn = psycopg2.connect(
        host=st.secrets["DB_HOST"],
        port=st.secrets["DB_PORT"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"]
    )

    # CSS
    st.markdown(""" 
        <style>
        .kpi-card {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            height: 150px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .kpi-title {
            font-size: 20px;
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
        }
        .kpi-value {
            font-size: 36px;
            font-weight: bold;
            color: #0072C6;
        }
        .stDateInput > div > input {
            width: 120px;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    # Exibição de configurações se acionadas
    if st.session_state["menu_config"] == "cadastrar":
        cadastrar_usuario(usuarios)
        st.session_state["menu_config"] = ""
    elif st.session_state["menu_config"] == "senha":
        alterar_senha(usuarios)
        st.session_state["menu_config"] = ""
    else:
        # Execução do menu lateral
        if menu == "KPI":
            mostrar_kpi(conn)
        elif menu == "Comparativo 12 meses":
            comparativo_12_meses(conn)
