import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from sqlalchemy import text
from menu import botao_voltar_menu  # Usa só o import!

def comparativo_televendas(conn_faturamento):
    botao_voltar_menu("menu")  # Ou "comparativo_televendas" se preferir voltar para essa tela

    st.markdown("<h2 style='text-align:center'>📊 Comparativos - Televendas</h2>", unsafe_allow_html=True)
    st.divider()

    hoje = date.today()
    ano_atual = hoje.year
    ano_passado = ano_atual - 1

    meses_nome = {
        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
    }

    cores = {
        str(ano_passado): "#9EB383",
        str(ano_atual): "#79A93B"
    }

    def plot_comparativo(df, titulo, y_label):
        df["ano"] = df["ano"].astype(str)
        df["mes_nome"] = df["mes"].map(meses_nome)
        ordem = ["Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez", "Jan", "Fev", "Mar", "Abr", "Mai"]
        df["mes_nome"] = pd.Categorical(df["mes_nome"], categories=ordem, ordered=True)
        df = df.sort_values(["ano", "mes"])

        fig = px.bar(
            df,
            x="mes_nome",
            y="valor",
            color="ano",
            barmode="group",
            text_auto=".2s",
            template="plotly_white",
            title=titulo,
            color_discrete_map=cores
        )

        fig.update_layout(
            xaxis_title="Mês",
            yaxis_title=y_label,
            legend_title="Ano",
            bargap=0.2
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- Faturamento ---
    st.subheader("💰 Faturamento Mensal")
    try:
        query_fat = text(f"""
            SELECT 
                EXTRACT(YEAR FROM BIIFDATA)::int AS ano,
                EXTRACT(MONTH FROM BIIFDATA)::int AS mes,
                SUM(BIIFVTOT) AS valor
            FROM bi_biif
            LEFT JOIN BI_CADA VEND ON VEND.BI_CADACODI = BIIFVEND
            LEFT JOIN BI_TABE ON BI_TABE.BI_TABECODI = VEND.BI_CADATPVN AND BI_TABE.BI_TABEINDI = 30
            WHERE 
                biifgere = 1115
                AND BI_TABE.BI_TABEDESC = 'TELEVENDAS'
                AND BIIFDATA BETWEEN '{ano_passado}-01-01' AND '{ano_atual}-12-31'
            GROUP BY ano, mes
            ORDER BY ano, mes
        """)
        df_fat = pd.read_sql(query_fat, conn_faturamento)
        if not df_fat.empty:
            plot_comparativo(df_fat, "Faturamento Mensal Televendas", "Faturamento")
        else:
            st.info("Nenhum dado de faturamento disponível.")
    except Exception as e:
        st.error(f"Erro ao buscar faturamento: {e}")

    # --- Vendas ---
    st.subheader("🧾 Quantidade de Vendas Mensal")
    try:
        query_vendas = text(f"""
            SELECT 
                EXTRACT(YEAR FROM BIIFDATA)::int AS ano,
                EXTRACT(MONTH FROM BIIFDATA)::int AS mes,
                COUNT(DISTINCT BIIFCPRI) AS valor
            FROM bi_biif
            LEFT JOIN BI_CADA VEND ON VEND.BI_CADACODI = BIIFVEND
            LEFT JOIN BI_TABE ON BI_TABE.BI_TABECODI = VEND.BI_CADATPVN AND BI_TABE.BI_TABEINDI = 30
            WHERE 
                biifgere = 1115
                AND BIIFPVEN = 'S'
                AND BI_TABE.BI_TABEDESC = 'TELEVENDAS'
                AND BIIFDATA BETWEEN '{ano_passado}-01-01' AND '{ano_atual}-12-31'
            GROUP BY ano, mes
            ORDER BY ano, mes
        """)
        df_vendas = pd.read_sql(query_vendas, conn_faturamento)
        if not df_vendas.empty:
            plot_comparativo(df_vendas, "Quantidade de Vendas Mensal Televendas", "Quantidade de Vendas")
        else:
            st.info("Nenhum dado de vendas disponível.")
    except Exception as e:
        st.error(f"Erro ao buscar vendas: {e}")
