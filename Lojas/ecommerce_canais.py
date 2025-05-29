import streamlit as st
import pandas as pd
from datetime import date
from sqlalchemy import text

def formatar_faturamento(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_percentual(valor):
    return f"{valor:.2f}%"

def mini_card_valor(label, valor, cor="#6C63FF"):
    return f"""
    <div style="background: white; border: 1px solid {cor}; border-radius: 8px; padding: 6px 10px;
                width: 160px; text-align: center; margin: 8px auto; box-shadow: 1px 1px 4px rgba(0,0,0,0.1);">
        <div style="font-size: 11px; color: #555;">{label}</div>
        <div style="font-size: 15px; font-weight: bold; color: {cor};">{valor}</div>
    </div>
    """

def titulo_canal(icone, titulo, cor):
    return f"""
    <div style="text-align: center; margin-bottom: 10px;">
        <span style="font-size: 18px; font-weight: bold; color: {cor};">{icone} {titulo}</span>
    </div>
    """

def mostrar_ecommerce_canais(conn_faturamento):
    if st.button("🔙 Voltar ao Painel E-commerce", key="voltar_ecommerce_canais"):
        st.session_state["pagina"] = "ecommerce"
        st.rerun()

    st.markdown("<h2 style='text-align:center; margin-bottom: 20px;'>🛍️ E-commerce - Canais de Venda</h2>", unsafe_allow_html=True)

    hoje = date.today()
    col1, col2, _ = st.columns([1, 1, 4])
    with col1:
        data_inicio = st.date_input("Data Inicial", value=hoje, key="data_inicio_ecommerce_canais")
    with col2:
        data_fim = st.date_input("Data Final", value=hoje, key="data_fim_ecommerce_canais")

    query = text("""
        SELECT
            CASE
                WHEN BIIFVEND = 1137 THEN 'Magazine Luiza'
                WHEN BIIFVEND = 1134 THEN 'Mercado Livre'
                WHEN BIIFVEND = 1114 THEN 'Web'
                WHEN BIIFVEND = 1135 THEN 'MadeiraMadeira'
                ELSE 'Outros'
            END AS canal_venda,
            SUM(CASE WHEN BIIFVTOT > 0 THEN BIIFVTOT ELSE 0 END) AS faturamento,
            SUM(CASE WHEN BIIFVTOT < 0 THEN BIIFVTOT * -1 ELSE 0 END) AS devolucao,
            SUM(BIIFAPRA) AS venda_prazo,
            SUM(BIIFAVIS) AS venda_vista,
            COUNT(DISTINCT BIIFCPRI) AS vendas,
            ROUND(SUM(BIIFVTOT) / NULLIF(COUNT(DISTINCT BIIFCPRI), 0), 2) AS ticket_medio,
            ROUND((SUM(CASE WHEN BIIFVTOT < 0 THEN BIIFVTOT * -1 ELSE 0 END) / NULLIF(SUM(CASE WHEN BIIFVTOT > 0 THEN BIIFVTOT ELSE 0 END), 0)) * 100, 2) AS perc_devolucao,
            ROUND((SUM(BIIFAPRA) / NULLIF(SUM(BIIFVTOT), 0)) * 100, 2) AS perc_prazo,
            ROUND((SUM(BIIFAVIS) / NULLIF(SUM(BIIFVTOT), 0)) * 100, 2) AS perc_vista
        FROM BI_BIIF
        LEFT JOIN BI_CADA VEND ON VEND.BI_CADACODI = BIIFVEND
        LEFT JOIN BI_TABE ON BI_TABE.BI_TABECODI = VEND.BI_CADATPVN AND BI_TABE.BI_TABEINDI = 30
        WHERE BIIFDATA BETWEEN :data_inicio AND :data_fim
          AND BIIFGERE = 1122
        GROUP BY canal_venda
        ORDER BY faturamento DESC;
    """)

    df = pd.read_sql(query, conn_faturamento, params={
        "data_inicio": data_inicio,
        "data_fim": data_fim
    })

    if df.empty:
        st.warning("Nenhum dado de venda encontrado para o período.")
        return

    canais_info = {
        "Web": {"cor": "#6C63FF", "icone": "🌐"},
        "Mercado Livre": {"cor": "#AEC41D", "icone": "🟡"},
        "Magazine Luiza": {"cor": "#E91E63", "icone": "🛖"},
        "MadeiraMadeira": {"cor": "#003399", "icone": "🪕"},
        "Outros": {"cor": "#888", "icone": "❓"}
    }

    st.markdown("### 📋 Visão Geral")
    col1, col2, col3, col4 = st.columns(4)
    colunas = [col1, col2, col3, col4]

    for idx, canal in enumerate(["Web", "Mercado Livre", "Magazine Luiza", "MadeiraMadeira"]):
        row = df[df["canal_venda"] == canal]
        if not row.empty:
            dados = row.iloc[0]
            info = canais_info.get(canal, canais_info["Outros"])
            with colunas[idx]:
                st.markdown(titulo_canal(info["icone"], canal, info["cor"]), unsafe_allow_html=True)
                st.markdown(mini_card_valor("Faturamento", formatar_faturamento(dados['faturamento']), info["cor"]), unsafe_allow_html=True)
                st.markdown(mini_card_valor("Devolução", formatar_faturamento(dados['devolucao']), info["cor"]), unsafe_allow_html=True)
                st.markdown(mini_card_valor("% Devolução", formatar_percentual(dados['perc_devolucao']), info["cor"]), unsafe_allow_html=True)
                st.markdown(mini_card_valor("Venda a Prazo", formatar_faturamento(dados['venda_prazo']), info["cor"]), unsafe_allow_html=True)
                st.markdown(mini_card_valor("% Prazo", formatar_percentual(dados['perc_prazo']), info["cor"]), unsafe_allow_html=True)
                st.markdown(mini_card_valor("Ticket Médio", formatar_faturamento(dados['ticket_medio']), info["cor"]), unsafe_allow_html=True)
                st.markdown(mini_card_valor("Vendas", str(int(dados['vendas'])), info["cor"]), unsafe_allow_html=True)
                st.markdown(mini_card_valor("Venda à Vista", formatar_faturamento(dados['venda_vista']), info["cor"]), unsafe_allow_html=True)
                st.markdown(mini_card_valor("% Vista", formatar_percentual(dados['perc_vista']), info["cor"]), unsafe_allow_html=True)
