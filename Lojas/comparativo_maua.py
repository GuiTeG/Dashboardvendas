import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from sqlalchemy import text
from menu import botao_voltar_menu

def comparativo_maua(conn_faturamento, conn_fluxo):
    botao_voltar_menu("menu")  # ou "comparativo_maua", conforme seu fluxo

    st.markdown("<h2 style='text-align:center'>📊 Comparativos - Mauá</h2>", unsafe_allow_html=True)
    st.divider()

    hoje = date.today()
    ano_atual = hoje.year
    ano_passado = ano_atual - 1

    meses_nome = {
        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
    }

    cores = {
        str(ano_passado): "#F1B19D",
        str(ano_atual): "#E9633A"
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

    def plot_porcentagem(df, titulo, y_label):
        df["mes_nome"] = df["mes"].map(meses_nome)
        df["ano"] = df["ano"].astype(str)
        ordem = ["Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez", "Jan", "Fev", "Mar", "Abr", "Mai"]
        df["mes_nome"] = pd.Categorical(df["mes_nome"], categories=ordem, ordered=True)
        df = df.sort_values(["ano", "mes"])

        fig = px.bar(
            df,
            x="mes_nome",
            y="valor",
            color="ano",
            barmode="group",
            text=df["valor"].map(lambda x: f"{x:.1f}%"),
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
    df_fat = pd.DataFrame()
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
                BIIFEMPE = 3
                AND BI_TABE.BI_TABEDESC IN ('AUTO SERVICO', 'VENDEDORES LOJA FÍSICA')
                AND BIIFDATA BETWEEN '{ano_passado}-01-01' AND '{ano_atual}-12-31'
            GROUP BY ano, mes
            ORDER BY ano, mes
        """)
        df_fat = pd.read_sql(query_fat, conn_faturamento)
        if not df_fat.empty:
            plot_comparativo(df_fat, "Faturamento Mensal Mauá", "Faturamento")
        else:
            st.info("Nenhum dado de faturamento disponível.")
    except Exception as e:
        st.error(f"Erro ao buscar faturamento: {e}")

    # --- Fluxo ---
    st.subheader("🧑 Fluxo de Pessoas Mensal")
    df_fluxo = pd.DataFrame()
    try:
        query_fluxo = text(f"""
            SELECT 
                EXTRACT(YEAR FROM emissao)::int AS ano,
                EXTRACT(MONTH FROM emissao)::int AS mes,
                SUM(fluxo) AS valor
            FROM virtual_gate
            WHERE 
                loja = '3'
                AND emissao BETWEEN '{ano_passado}-01-01' AND '{ano_atual}-12-31'
            GROUP BY ano, mes
            ORDER BY ano, mes
        """)
        df_fluxo = pd.read_sql(query_fluxo, conn_fluxo)
        if not df_fluxo.empty:
            plot_comparativo(df_fluxo, "Fluxo de Pessoas Mensal Mauá", "Fluxo")
        else:
            st.info("Nenhum dado de fluxo disponível.")
    except Exception as e:
        st.error(f"Erro ao buscar fluxo: {e}")

    # --- Vendas ---
    st.subheader("🧾 Quantidade de Vendas Mensal")
    df_vendas = pd.DataFrame()
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
                BIIFEMPE = 3
                AND BIIFPVEN = 'S'
                AND BI_TABE.BI_TABEDESC IN ('AUTO SERVICO', 'VENDEDORES LOJA FÍSICA')
                AND BIIFDATA BETWEEN '{ano_passado}-01-01' AND '{ano_atual}-12-31'
            GROUP BY ano, mes
            ORDER BY ano, mes
        """)
        df_vendas = pd.read_sql(query_vendas, conn_faturamento)
        if not df_vendas.empty:
            plot_comparativo(df_vendas, "Quantidade de Vendas Mensal Mauá", "Quantidade de Vendas")
        else:
            st.info("Nenhum dado de vendas disponível.")
    except Exception as e:
        st.error(f"Erro ao buscar vendas: {e}")

    # --- Conversão ---
    st.subheader("📊 % Conversão de Vendas")
    try:
        if not df_vendas.empty and not df_fluxo.empty:
            df_vendas_conv = df_vendas.rename(columns={"valor": "valor_vendas"})
            df_fluxo_conv = df_fluxo.rename(columns={"valor": "valor_fluxo"})
            df_conv = pd.merge(df_vendas_conv, df_fluxo_conv, on=["ano", "mes"])
            df_conv["valor"] = (df_conv["valor_vendas"] / df_conv["valor_fluxo"].replace(0, None)) * 100
            df_conv = df_conv.dropna(subset=["valor"])
            df_conv["valor"] = df_conv["valor"].round(2)
            plot_porcentagem(df_conv, "% Conversão de Vendas - Mauá", "Conversão (%)")
        else:
            st.info("Dados insuficientes para calcular conversão.")
    except Exception as e:
        st.error(f"Erro ao calcular conversão: {e}")
