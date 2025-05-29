import streamlit as st
import pandas as pd
from sqlalchemy import text

def mostrar_venda_assistida_maua(conn_faturamento, conn_fluxo):
    st.markdown("## 🤝 Vendas Assistidas - Mauá")

    # Estilo global do botão
    st.markdown("""
        <style>
        div.stButton > button {
            background-color: #f0f2f6;
            color: #262730;
            font-weight: 600;
            border: 1px solid #ccc;
            border-radius: 0.5em;
            padding: 0.4em 1.2em;
            font-size: 15px;
            margin-top: 0.5em;
        }
        div.stButton > button:hover {
            background-color: #e0e2e8;
        }
        </style>
    """, unsafe_allow_html=True)

    # Layout dos filtros
    data_hoje = pd.to_datetime("today").normalize()
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        data_inicio = st.date_input("Data Inicial", data_hoje)
    with col2:
        data_fim = st.date_input("Data Final", data_hoje)

    # Consulta antecipada de vendedores da Mauá
    df_assistidas_raw = pd.read_sql(text("""
        SELECT DISTINCT vendedor
        FROM BI_VENDA_ASSISTIDA
        WHERE EMPRESA = 3
        AND DATAFATURAMENTO BETWEEN :inicio AND :fim
    """), conn_fluxo, params={"inicio": data_inicio, "fim": data_fim})

    vendedores_lista = sorted(df_assistidas_raw["vendedor"].dropna().unique())

    with col3:
        vendedor_selecionado = st.selectbox("Filtrar por vendedor", ["Todos"] + vendedores_lista)

    # Botão Voltar
    st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
    if st.button("🔙 Voltar", key="voltar_assistida_maua"):
        st.session_state["pagina"] = "maua"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Consulta total de vendas (BI_BIIF) para Mauá
    df_total_vendas = pd.read_sql(text("""
        SELECT
            BIIFDATA AS emissao,
            BIIFVEND AS usuario,
            COUNT(DISTINCT BIIFCPRI) AS total_vendas
        FROM BI_BIIF
        WHERE BIIFDATA BETWEEN :inicio AND :fim
          AND BIIFEMPE = 3
        GROUP BY BIIFDATA, BIIFVEND
    """), conn_faturamento, params={"inicio": data_inicio, "fim": data_fim})

    # Consulta vendas assistidas para Mauá
    df_assistidas = pd.read_sql(text("""
        SELECT *,
            CASE
                WHEN Vendas_totais = 0 THEN 0
                ELSE (CAST(total_app AS NUMERIC(10, 2)) / CAST(Vendas_totais AS NUMERIC(10, 2))) * 100
            END AS porcentagem
        FROM (
            SELECT
                DATAFATURAMENTO AS emissao,
                USUARIO,
                VENDEDOR,
                EMPRESA,
                SUM(TOTAL) AS total_app,
                SUM(TOTAL_VENDAS_DIA) AS Vendas_totais
            FROM BI_VENDA_ASSISTIDA
            WHERE DATAFATURAMENTO BETWEEN :inicio AND :fim
              AND EMPRESA = 3
            GROUP BY DATAFATURAMENTO, USUARIO, VENDEDOR, EMPRESA
        ) AS aux
    """), conn_fluxo, params={"inicio": data_inicio, "fim": data_fim})

    # Junta os dados e calcula indicadores
    df_indicadores = pd.merge(df_total_vendas, df_assistidas, how='left', on=['emissao', 'usuario'])
    df_indicadores.fillna({'total_app': 0, 'porcentagem': 0}, inplace=True)

    df_vendedor = df_indicadores.groupby(['usuario', 'vendedor']).agg({
        'total_vendas': 'sum',
        'total_app': 'sum'
    }).reset_index()

    df_vendedor['% Assistidas'] = df_vendedor.apply(
        lambda row: (row['total_app'] / row['total_vendas']) * 100 if row['total_vendas'] > 0 else 0,
        axis=1
    ).round(1)

    # Filtro por vendedor
    if vendedor_selecionado != "Todos":
        df_vendedor = df_vendedor[df_vendedor['vendedor'] == vendedor_selecionado]

    # Tabela formatada
    df_exibir = df_vendedor.rename(columns={
        'vendedor': 'Vendedor',
        'total_vendas': 'Totais',
        'total_app': 'Assistidas'
    }).sort_values(by='% Assistidas', ascending=False)

    st.markdown("### 📊 Indicadores de Venda Assistida por Vendedor - Mauá")
    st.dataframe(
        df_exibir[['Vendedor', 'Totais', 'Assistidas', '% Assistidas']].style.format({
            'Totais': '{:.0f}',
            'Assistidas': '{:.0f}',
            '% Assistidas': '{:.1f}%',
        }),
        use_container_width=True
    )
