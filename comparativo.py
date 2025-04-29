import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

def comparativo_12_meses(conn):
    st.markdown("<h1 style='text-align: center;'>📊 Comparativo Mês a Mês </h1>", unsafe_allow_html=True)
    st.divider()

    hoje = date.today()
    ano_atual = hoje.year
    ano_passado = ano_atual - 1

    query = f"""
        SELECT 
            EXTRACT(YEAR FROM emissao) AS ano,
            EXTRACT(MONTH FROM emissao) AS mes,
            SUM(fluxo) AS total_fluxo
        FROM virtual_gate
        WHERE loja = '1'
        AND emissao >= '{ano_passado}-01-01'
        AND emissao <= '{ano_atual}-12-31'
        GROUP BY ano, mes
        ORDER BY ano, mes
    """
    df = pd.read_sql_query(query, conn)

    if df.empty:
        st.warning("⚠️ Não há dados suficientes para comparação.")
    else:
        meses_nome = {
            1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
            7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
        }
        df["mes_nome"] = df["mes"].map(meses_nome)
        df_pivot = df.pivot(index="mes_nome", columns="ano", values="total_fluxo").reset_index()
        ordem = ["Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez", "Jan", "Fev", "Mar", "Abr"]
        df_pivot["mes_nome"] = pd.Categorical(df_pivot["mes_nome"], categories=ordem, ordered=True)
        df_pivot = df_pivot.sort_values("mes_nome")
        df_melt = df_pivot.melt(id_vars=["mes_nome"], var_name="Ano", value_name="Fluxo Total")

        fig = px.bar(
            df_melt,
            x="mes_nome",
            y="Fluxo Total",
            color="Ano",
            barmode="group",
            text_auto=".2s",
            template="plotly_white",
            color_discrete_map={ano_passado: "lightcoral", ano_atual: "red"}
        )

        fig.update_layout(
            title_font_size=24,
            title_x=0.5,
            xaxis_title="Mês",
            yaxis_title="Fluxo Total",
            legend_title="Ano",
            bargap=0.2,
        )
        st.plotly_chart(fig, use_container_width=True)
