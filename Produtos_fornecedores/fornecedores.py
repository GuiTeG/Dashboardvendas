import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import date, timedelta

def mini_card(icone, titulo, valor, cor="#008080"):
    return f"""
    <div style="
        background: white;
        border-radius: 8px;
        border: 2px solid {cor};
        width: 220px;
        height: 80px;
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        margin: 8px auto;
        font-family: Arial, sans-serif;
        user-select: none;
    ">
        <div style="font-size: 24px; color: {cor};">{icone}</div>
        <div style="display: flex; flex-direction: column; line-height: 1.2;">
            <div style="font-size: 12px; font-weight: 600;">{titulo}</div>
            <div style="font-size: 18px; font-weight: bold; color: {cor};">{valor}</div>
        </div>
    </div>
    """

def formatar_faturamento(valor):
    return f"R$ {valor:,.2f}"

def get_opcoes_fornecedor(conn, inicio, fim, filtros_sql="", params={}):
    sql = text(f"""
        SELECT DISTINCT FABRICANTE.BI_CADANOME AS nome_fornecedor
        FROM BI_BIIF
        LEFT JOIN BI_PROD PRODUTO ON PRODUTO.BI_PRODCODI = BI_BIIF.BIIFCODI
        LEFT JOIN BI_CADA FABRICANTE ON FABRICANTE.BI_CADACODI = PRODUTO.BI_PRODFORN
        WHERE BIIFDATA BETWEEN :inicio AND :fim
        {filtros_sql}
        ORDER BY nome_fornecedor
    """)
    df = pd.read_sql(sql, conn, params={**params, "inicio": inicio, "fim": fim})
    return df["nome_fornecedor"].dropna().tolist()

def aba_produtos(conn):
    if st.button("🔙 Voltar ao Menu", key="btn_voltar_menu"):
        st.session_state["pagina"] = "menu"
        st.rerun()

    hoje = date.today()
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data Inicial", hoje, key="data_inicio")
    with col2:
        data_fim = st.date_input("Data Final", hoje, key="data_fim")

    if data_inicio > data_fim:
        st.error("Data inicial não pode ser maior que data final.")
        return

    fornecedores_selecionados = st.multiselect(
        "Fornecedor",
        options=get_opcoes_fornecedor(conn, data_inicio, data_fim),
        key="filtro_fornecedor",
        help="Filtrar por fornecedor"
    )

    filtros_where = []
    params = {"data_inicio": data_inicio, "data_fim": data_fim}

    if fornecedores_selecionados:
        filtros_where.append("FABRICANTE.BI_CADANOME IN :fornecedores")
        params["fornecedores"] = tuple(fornecedores_selecionados)

    where_sql = " AND ".join(filtros_where)
    if where_sql:
        where_sql = "AND " + where_sql

    sql = text(f"""
        SELECT
            BIIFCPRI AS produto_id,
            PRODUTO.bi_proddesc AS descricao_produto,
            SUM(BIIFPLIQ) AS receita_liquida,
            SUM(BIIFCREP + BIIFVARI + BIIFCOMB + BIIFCOMC + BIIFICMC) AS custo_variavel_total,
            ROUND(SUM(BIIFPLIQ - BIIFCREP - (BIIFVARI + BIIFCOMB + BIIFCOMC + BIIFICMC)), 2) AS rentabilidade,
            CASE WHEN SUM(BIIFPLIQ) > 0 THEN
                ROUND(SUM(BIIFPLIQ - BIIFCREP - (BIIFVARI + BIIFCOMB + BIIFCOMC + BIIFICMC)) / SUM(BIIFPLIQ) * 100, 2)
            ELSE 0 END AS margem_percentual,
            ROUND(SUM(CASE WHEN BIIFPTAB > BIIFPLIQ THEN BIIFPTAB - BIIFPLIQ ELSE 0 END), 2) AS desconto_valor,
            CASE WHEN SUM(BIIFPTAB) > 0 THEN
                ROUND(SUM(CASE WHEN BIIFPTAB > BIIFPLIQ THEN BIIFPTAB - BIIFPLIQ ELSE 0 END) / SUM(BIIFPTAB) * 100, 2)
            ELSE 0 END AS desconto_percentual,
            TIPOPRODUTO.BI_TABEDESC AS tipo_produto,
            FABRICANTE.BI_CADANOME AS fabricante,
            VENDEDOR.BI_CADANOME AS vendedor
        FROM BI_BIIF
        LEFT JOIN BI_PROD PRODUTO ON PRODUTO.BI_PRODCODI = BIIFCODI
        LEFT JOIN BI_TABE TIPOPRODUTO ON TIPOPRODUTO.BI_TABECODI = PRODUTO.BI_PRODTIPO AND TIPOPRODUTO.BI_TABEINDI = 100
        LEFT JOIN BI_CADA FABRICANTE ON FABRICANTE.BI_CADACODI = PRODUTO.BI_PRODFORN
        LEFT JOIN BI_CADA VENDEDOR ON VENDEDOR.BI_CADACODI = BIIFVEND
        WHERE BIIFDATA BETWEEN :data_inicio AND :data_fim
        {where_sql}
        GROUP BY BIIFCPRI, PRODUTO.bi_proddesc, TIPOPRODUTO.BI_TABEDESC, FABRICANTE.BI_CADANOME, VENDEDOR.BI_CADANOME
        ORDER BY rentabilidade DESC
    """)

    df = pd.read_sql(sql, conn, params=params)

    if df.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    faturamento_total = float(df["receita_liquida"].sum())
    total_produtos = df["produto_id"].nunique()
    rentabilidade_percentual = float(df["margem_percentual"].mean())
    desconto_total = float(df["desconto_valor"].sum())

    dias_intervalo = (data_fim - data_inicio).days + 1
    periodo_anterior_fim = data_inicio - timedelta(days=1)
    periodo_anterior_inicio = periodo_anterior_fim - timedelta(days=dias_intervalo - 1)

    sql_crescimento = text("""
        SELECT SUM(BIIFPLIQ) AS faturamento
        FROM BI_BIIF
        WHERE BIIFDATA BETWEEN :inicio_anterior AND :fim_anterior
    """)
    result_crescimento = conn.execute(sql_crescimento, {
        "inicio_anterior": periodo_anterior_inicio,
        "fim_anterior": periodo_anterior_fim
    }).fetchone()

    faturamento_periodo_anterior = float(result_crescimento[0]) if result_crescimento and result_crescimento[0] else 0.0
    crescimento = ((faturamento_total - faturamento_periodo_anterior) / faturamento_periodo_anterior * 100
                   if faturamento_periodo_anterior > 0 else None)

    df["participacao_faturamento_perc"] = (df["receita_liquida"] / faturamento_total * 100).round(2)
    df["margem_contribuicao"] = (df["receita_liquida"] - df["custo_variavel_total"]).round(2)

    cor = "#008080"
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(mini_card("💰", "Faturamento Total", formatar_faturamento(faturamento_total), cor), unsafe_allow_html=True)
        st.markdown(mini_card("🎟️", "Ticket Médio (R$)", formatar_faturamento(faturamento_total / total_produtos if total_produtos else 0), cor), unsafe_allow_html=True)

    with col2:
        st.markdown(mini_card("📈", "Crescimento vs. Período Anterior (%)", f"{crescimento:.2f} %" if crescimento is not None else "N/A", cor), unsafe_allow_html=True)
        st.markdown(mini_card("📉", "Desconto Total (R$)", formatar_faturamento(desconto_total), cor), unsafe_allow_html=True)

    with col3:
        st.markdown(mini_card("🛒", "Produtos Únicos", f"{total_produtos}", cor), unsafe_allow_html=True)
        st.markdown(mini_card("📊", "Rentabilidade (%)", f"{rentabilidade_percentual:.2f} %", cor), unsafe_allow_html=True)

    col4, col5, _ = st.columns(3)
    with col4:
        st.markdown(mini_card("📌", "Participação Máx. no Faturamento (%)", f"{df['participacao_faturamento_perc'].max():.2f} %", cor), unsafe_allow_html=True)
    with col5:
        st.markdown(mini_card("🧾", "Maior Margem Contribuição (R$)", formatar_faturamento(df["margem_contribuicao"].max()), cor), unsafe_allow_html=True)
