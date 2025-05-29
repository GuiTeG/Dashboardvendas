import streamlit as st
import pandas as pd
from datetime import date
from sqlalchemy import text

def mostrar_vendedores_santo_andre(conn_faturamento):
    st.title("Vendedores - Santo André")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        data_inicio = st.date_input("Data Inicial", value=date.today(), key="data_inicio_vendedores")
    with col2:
        data_fim = st.date_input("Data Final", value=date.today(), key="data_fim_vendedores")

    query_vendedores = text("""
        SELECT DISTINCT V.BI_CADANOME AS vendedor
        FROM bi_biif B
        LEFT JOIN BI_CADA V ON V.BI_CADACODI = B.BIIFVEND
        WHERE
            B.BIIFEMPE = 1
            AND B.BIIFDATA BETWEEN :data_inicio AND :data_fim
            AND V.BI_CADANOME NOT IN ('WEB', 'VENDEDOR LOJA 01', 'MERCADO LIVRE')
    """)
    df_vendedores_unicos = pd.read_sql(query_vendedores, conn_faturamento, params={"data_inicio": data_inicio, "data_fim": data_fim})
    lista_vendedores = ["Todos"] + sorted(df_vendedores_unicos["vendedor"].dropna().unique().tolist())

    with col3:
        vendedor_selecionado = st.selectbox("Filtrar por vendedor", options=lista_vendedores, index=0)

    if st.button("🔙 Voltar", key="voltar_vendedores_sa"):
        st.session_state["pagina"] = "santo_andre"
        st.rerun()

    filtro_vendedor_sql = ""
    params = {"data_inicio": data_inicio, "data_fim": data_fim}
    if vendedor_selecionado != "Todos":
        filtro_vendedor_sql = "AND V.BI_CADANOME = :vendedor"
        params["vendedor"] = vendedor_selecionado

    query_geral = text(f"""
        SELECT
            V.BI_CADANOME AS vendedor,
            COUNT(DISTINCT BIIFCPRI) AS total_vendas,
            SUM(BIIFVTOT) AS faturamento_liquido,
            SUM(CASE WHEN BIIFVTOT < 0 THEN BIIFVTOT * -1 ELSE 0 END) AS devolucao_liq,
            ROUND(SUM(BIIFCREP), 2) AS cmv,
            SUM(BIIFVARI + BIIFCOMB + BIIFCOMC + BIIFICMC) AS custo_variavel,
            SUM(BIIFFIXO) AS custo_fixo,
            SUM(BIIFAVIS) AS venda_a_vista,
            SUM(BIIFAPRA) AS venda_a_prazo,
            SUM(BIIFPRAZ * BIIFPLIQ) AS prazo_medio_recebimento,
            SUM(BIIFQUAN) AS quantidade_sku,
            CASE WHEN SUM(BIIFVTOT) = 0 THEN 0 ELSE 
                (SUM(BIIFVTOT) - SUM(BIIFCREP) - SUM(BIIFVARI + BIIFCOMB + BIIFCOMC + BIIFICMC) - SUM(BIIFFIXO)) * 100.0 / SUM(BIIFVTOT) 
            END AS perc_rentabilidade,
            CASE WHEN SUM(BIIFVTOT) = 0 THEN 0 ELSE 
                SUM(BIIFAVIS) * 100.0 / SUM(BIIFVTOT) 
            END AS perc_venda_a_vista,
            CASE WHEN SUM(BIIFVTOT) = 0 THEN 0 ELSE 
                SUM(BIIFAPRA) * 100.0 / SUM(BIIFVTOT) 
            END AS perc_venda_a_prazo,
            CASE WHEN COUNT(DISTINCT BIIFCPRI) = 0 THEN 0 ELSE
                SUM(BIIFVTOT) / COUNT(DISTINCT BIIFCPRI)
            END AS ticket_medio
        FROM
            bi_biif B
        LEFT JOIN BI_CADA V ON V.BI_CADACODI = B.BIIFVEND
        LEFT JOIN BI_TABE ON BI_TABE.BI_TABECODI = V.BI_CADATPVN AND BI_TABE.BI_TABEINDI = 30
        WHERE
            B.BIIFEMPE = 1
            AND B.BIIFDATA BETWEEN :data_inicio AND :data_fim
            {filtro_vendedor_sql}
            AND V.BI_CADANOME NOT IN ('WEB', 'VENDEDOR LOJA 01', 'MERCADO LIVRE')
            AND BI_TABE.BI_TABEDESC IN ('AUTO SERVICO','VENDEDORES LOJA FÍSICA')
        GROUP BY
            V.BI_CADANOME
        ORDER BY
            faturamento_liquido DESC
        LIMIT 20;
    """)

    df_geral = pd.read_sql(query_geral, conn_faturamento, params=params)

    def formatar_moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def formatar_perc(valor):
        return f"{valor:.2f}%"

    def formatar_inteiro(valor):
        return f"{int(valor):,}".replace(",", ".")

    df_geral["total_vendas"] = df_geral["total_vendas"].map(formatar_inteiro)
    df_geral["faturamento_liquido"] = df_geral["faturamento_liquido"].map(formatar_moeda)
    df_geral["ticket_medio"] = df_geral["ticket_medio"].map(formatar_moeda)
    df_geral["perc_rentabilidade"] = df_geral["perc_rentabilidade"].map(formatar_perc)
    df_geral["perc_venda_a_vista"] = df_geral["perc_venda_a_vista"].map(formatar_perc)
    df_geral["perc_venda_a_prazo"] = df_geral["perc_venda_a_prazo"].map(formatar_perc)
    df_geral["devolucao_liq"] = df_geral["devolucao_liq"].map(formatar_moeda)
    df_geral["cmv"] = df_geral["cmv"].map(formatar_moeda)
    df_geral["custo_variavel"] = df_geral["custo_variavel"].map(formatar_moeda)
    df_geral["custo_fixo"] = df_geral["custo_fixo"].map(formatar_moeda)
    df_geral["venda_a_vista"] = df_geral["venda_a_vista"].map(formatar_moeda)
    df_geral["venda_a_prazo"] = df_geral["venda_a_prazo"].map(formatar_moeda)
    df_geral["quantidade_sku"] = df_geral["quantidade_sku"].map(formatar_inteiro)

    if "prazo_medio_recebimento" in df_geral.columns:
        df_geral = df_geral.drop(columns=["prazo_medio_recebimento"])

    df_geral.rename(columns={
        "vendedor": "Vendedor",
        "faturamento_liquido": "Faturamento",
        "total_vendas": "Vendas",
        "ticket_medio": "Ticket Médio",
        "devolucao_liq": "Devolução Líquida",
        "cmv": "CMV",
        "custo_variavel": "Custo Variável",
        "custo_fixo": "Custo Fixo",
        "venda_a_vista": "Venda à Vista",
        "perc_venda_a_vista": "% Venda à Vista",
        "venda_a_prazo": "Venda à Prazo",
        "perc_venda_a_prazo": "% Venda à Prazo",
        "quantidade_sku": "Quantidade SKU",
        "perc_rentabilidade": "% Rentabilidade"
    }, inplace=True)

    st.write("### Resumo Geral dos Vendedores")
    st.dataframe(df_geral, height=400)
