import streamlit as st

def botao_voltar_menu(pagina="menu"):
    if st.button("🔙 Voltar ao Menu", key=f"voltar_menu_{pagina}"):
        st.session_state.pagina = pagina
        st.rerun()

def menu_inicial():
    st.markdown("<h1 style='text-align: center;'>📊 Painel Integrado - Copafer</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Escolha abaixo qual painel deseja visualizar:</p>", unsafe_allow_html=True)
    st.markdown("---")

    papel = st.session_state.get("papel", "viewer")
    lojas_autorizadas = st.session_state.get("lojas_autorizadas", [])

    # Painel unificado apenas para admin
    if papel == "admin":
        if st.button("🧩 Painel Unificado Resumido", key="btn_unificado_resumido_menu_main"):
            st.session_state.pagina = "painel_unificado_resumido"
            st.rerun()

    col1, col2 = st.columns(2)

    with col1:
        if papel == "admin" or 1 in lojas_autorizadas:
            if st.button("🏬 Santo André - Painel Integrado", key="btn_painel_santo_andre"):
                st.session_state.pagina = "santo_andre"
                st.rerun()
        if papel == "admin" or 3 in lojas_autorizadas:
            if st.button("🏬 Mauá - Painel Integrado", key="btn_painel_maua"):
                st.session_state.pagina = "maua"
                st.rerun()
        if papel == "admin" or 1115 in lojas_autorizadas:
            if st.button("🏬 Televendas - Painel Integrado", key="btn_painel_televendas"):
                st.session_state.pagina = "televendas"
                st.rerun()
        if papel == "admin" or 1122 in lojas_autorizadas:
            if st.button("🛒 E-commerce - Painel Integrado", key="btn_painel_ecommerce"):
                st.session_state.pagina = "ecommerce"
                st.rerun()

    with col2:
        if papel == "admin" or 1 in lojas_autorizadas:
            if st.button("📊 Comparativo Santo André", key="btn_comp_santo_andre"):
                st.session_state.pagina = "comparativo_santo_andre"
                st.rerun()
        if papel == "admin" or 3 in lojas_autorizadas:
            if st.button("📊 Comparativo Mauá", key="btn_comp_maua"):
                st.session_state.pagina = "comparativo_maua"
                st.rerun()
        if papel == "admin" or 1115 in lojas_autorizadas:
            if st.button("📊 Comparativo Televendas", key="btn_comp_televendas"):
                st.session_state.pagina = "comparativo_televendas"
                st.rerun()
        if papel == "admin" or 1122 in lojas_autorizadas:
            if st.button("📊 Comparativo E-commerce", key="btn_comp_ecommerce"):
                st.session_state.pagina = "comparativo_ecommerce"
                st.rerun()

    st.markdown("---")
