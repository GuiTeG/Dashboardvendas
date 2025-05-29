import streamlit as st
import pandas as pd
from datetime import date
from sqlalchemy import text

from Login.autenticar import login, cadastrar_usuario, carregar_usuarios, excluir_usuario, alterar_cadastro
from menu import menu_inicial
from conexoes import conectar_virtual_gate, conectar_faturamento, conectar_producao

from Lojas.santo_andre import mostrar_santo_andre
from Lojas.maua import mostrar_maua
from Lojas.televendas import mostrar_televendas
from Lojas.ecommerce import mostrar_ecommerce
from Lojas.comparativo_santo_andre import comparativo_santo_andre
from Lojas.comparativo_maua import comparativo_maua
from Lojas.comparativos_televendas import comparativo_televendas
from Lojas.comparativo_ecommerce import comparativo_ecommerce
from Lojas.vendedores_maua import mostrar_vendedores_maua
from Lojas.venda_assistida_maua import mostrar_venda_assistida_maua
from Lojas.vendedores_televendas import mostrar_vendedores_televendas
from Lojas.vendedores_santo_andre import mostrar_vendedores_santo_andre
from Lojas.ecommerce_canais import mostrar_ecommerce_canais
from Unificado.painel_unificado_resumido import painel_unificado_resumido
from Lojas.vendas_assistidas import mostrar_vendas_assistida

st.set_page_config(page_title="Copafer Inside", layout="wide")

pagina = st.session_state.get("pagina", "menu").lower().replace("-", "_")
logado = st.session_state.get("logado", False)

unidades = {
    "santo_andre": ("SANTO ANDRÉ", "#EB354D", "#FFFFFF", "5rem", "-9vh"),
    "maua": ("MAUÁ", "#E9633A", "#FFFFFF", "5rem", "-9vh"),
    "televendas": ("TELEVENDAS", "#4CAF50", "#FFFFFF", "5rem", "-9vh"),
    "ecommerce": ("E-COMMERCE", "#6C63FF", "#FFFFFF", "5rem", "-9vh"),
    "painel_unificado_resumido": ("PRINCIPAIS", "#003366", "#FFFFFF", "5rem", "-9vh"),
}

mapa_unidades_sidebar = {
    "santo_andre": "santo_andre",
    "vendedores_santo_andre": "santo_andre",
    "vendas_assistidas_santo_andre": "santo_andre",
    "maua": "maua",
    "venda_assistida_maua": "maua",   # Atenção aqui: chave exata da página (sem 's' no final)
    "vendedores_maua": "maua",
    "televendas": "televendas",
    "vendedores_televendas": "televendas",
    "ecommerce": "ecommerce",
    "ecommerce_canais": "ecommerce",
    "vendedores_ecommerce": "ecommerce",
    "painel_unificado_resumido": "painel_unificado_resumido",
}


if not logado or pagina == "menu":
    cor_sidebar = "#FFD600"
    texto_sidebar = "COPAFER"
    tamanho_fonte = "8rem"
else:
    unidade_base = mapa_unidades_sidebar.get(pagina, None)
    if unidade_base:
        texto_sidebar, cor_sidebar, _, tamanho_fonte, _ = unidades.get(
            unidade_base, ("COPAFER", "#EB354D", "#FFFFFF", "5rem", "0")
        )
    else:
        texto_sidebar, cor_sidebar, _, tamanho_fonte, _ = ("COPAFER", "#EB354D", "#FFFFFF", "5rem", "0")

with st.sidebar:
    nome_unidade, fundo, cor_letra, _, margin_top = unidades.get(
        mapa_unidades_sidebar.get(pagina, ""), ("COPAFER", "#FFD600", "#EB354D", "5rem", "0")
    )
    st.markdown(f"""
    <style>
      section[data-testid="stSidebar"] > div:first-child {{ padding: 0 !important; margin: 0 !important; border-radius: 0 !important; }}
      section[data-testid="stSidebar"] {{ overflow: visible !important; background: {fundo} !important; height: 100vh !important; width: 90px !important; min-width: 90px !important; }}
      section[data-testid="stSidebar"]::-webkit-scrollbar {{ width: 0 !important; background: transparent !important; display: none !important; }}
      [data-testid="stSidebarContent"] {{ overflow: visible !important; }}
      .sidebar-vertical-text {{ position: absolute; top: {margin_top}; left: 50%; transform: translateX(-50%); color: {cor_letra}; font-weight: 900; letter-spacing: 12px; font-family: Arial, sans-serif; writing-mode: vertical-lr; text-orientation: mixed; text-align: center; line-height: 1; user-select: none; white-space: nowrap; overflow: visible; padding: 10px 0; font-size: 4rem; }}
    </style>
    <div class="sidebar-vertical-text">{nome_unidade}</div>
    """, unsafe_allow_html=True)

def botao_voltar_menu():
    if st.button("🔙 Voltar ao Menu", key="voltar_menu_geral"):
        st.session_state["menu_config"] = ""
        st.session_state["pagina"] = "menu"
        st.rerun()

if "logado" not in st.session_state:
    st.session_state.update({
        "logado": False,
        "tipo_usuario": "",
        "usuario_logado": "",
        "nome_usuario": "",
        "menu_config": "",
        "pagina": "menu"
    })

pagina = st.session_state.get("pagina", "menu").lower().replace("-", "_")

if not st.session_state["logado"]:
    st.title("Copafer Inside")
    usuarios = carregar_usuarios()
    dados_usuario = login(usuarios)
    if dados_usuario:
        st.session_state.update({
            "logado": True,
            "tipo_usuario": dados_usuario["tipo"],
            "usuario_logado": dados_usuario["nome"],
            "nome_usuario": dados_usuario["nome"],
            "menu_config": "",
            "pagina": "menu"
        })
        st.rerun()
else:
    loja_map = {
        "santo_andre": 1,
        "vendedores_santo_andre": 1,
        "vendas_assistidas_santo_andre": 1,
        "maua": 3,
        "vendedores_maua": 3,
        "televendas": 1115,
        "vendedores_televendas": 1115,
        "ecommerce": 1122,
        "ecommerce_canais": 1122,
        "vendedores_ecommerce": 1122,
        "painel_unificado_resumido": "TODAS"
    }

    usuario_lojas = st.session_state.get("lojas_autorizadas", [])
    usuario_papel = st.session_state.get("papel", "viewer")

    if pagina in loja_map and usuario_papel != "admin":
        loja_alvo = loja_map[pagina]
        if loja_alvo != "TODAS" and loja_alvo not in usuario_lojas:
            st.error("🚫 Você não tem permissão para acessar esta unidade.")
            st.stop()

    if pagina == "menu":
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"👤 **Bem Vindo:** {st.session_state['nome_usuario']}")
            with col2:
                with st.expander("⚙️ Conta", expanded=False):
                    if st.button("➕ Cadastrar Usuário", key="btn_cadastrar_usuario"):
                            st.session_state["menu_config"] = "cadastrar"
                            st.rerun()
                    if st.button("✏️ Alterar Cadastro", key="btn_alterar_cadastro"):
                        st.session_state["menu_config"] = "editar"
                        st.rerun()
                    if st.session_state.get("papel") == "admin":
                        if st.button("🗑️ Excluir Usuário", key="btn_excluir_usuario"):
                            st.session_state["menu_config"] = "excluir"
                            st.rerun()
                    if st.button("🚪 Logout", key="btn_logout"):
                        st.session_state.clear()
                        st.rerun()

    if st.session_state["menu_config"] == "cadastrar":
        botao_voltar_menu()
        cadastrar_usuario(carregar_usuarios())
        st.stop()
    elif st.session_state["menu_config"] == "excluir":
        botao_voltar_menu()
        excluir_usuario(carregar_usuarios())
        st.stop()
    elif st.session_state["menu_config"] == "editar":
        botao_voltar_menu()
        alterar_cadastro(carregar_usuarios())
        st.stop()

    conn_fluxo = conectar_virtual_gate()
    conn_faturamento = conectar_faturamento()
    conn_producao = conectar_producao()

    if pagina == "menu":
        menu_inicial()
    elif pagina == "painel_unificado_resumido":
        painel_unificado_resumido(conn_faturamento, conn_fluxo)
    elif pagina == "santo_andre":
        mostrar_santo_andre(conn_faturamento, conn_fluxo)
    elif pagina == "vendas_assistidas_santo_andre":
        mostrar_vendas_assistida(conn_faturamento, conn_fluxo)
    elif pagina == "maua":
        mostrar_maua(conn_faturamento, conn_fluxo)
    elif pagina == "televendas":
        mostrar_televendas(conn_faturamento)
    elif pagina == "vendedores_televendas":
        mostrar_vendedores_televendas(conn_faturamento)
    elif pagina == "ecommerce":
        mostrar_ecommerce(conn_faturamento, conn_fluxo)
    elif pagina == "ecommerce_canais":
        mostrar_ecommerce_canais(conn_faturamento)
    elif pagina == "comparativo_santo_andre":
        comparativo_santo_andre(conn_faturamento, conn_fluxo)
    elif pagina == "comparativo_maua":
        comparativo_maua(conn_faturamento, conn_fluxo)
    elif pagina == "comparativo_televendas":
        comparativo_televendas(conn_faturamento)
    elif pagina == "comparativo_ecommerce":
        comparativo_ecommerce(conn_faturamento)
    elif pagina == "vendedores_santo_andre":
        mostrar_vendedores_santo_andre(conn_faturamento)
    elif pagina == "vendedores_maua":
        mostrar_vendedores_maua(conn_faturamento)
    elif pagina == "venda_assistida_maua":
        mostrar_venda_assistida_maua(conn_faturamento, conn_fluxo)

    else:
        st.error("Página não encontrada.")
