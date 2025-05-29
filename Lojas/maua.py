import streamlit as st
import pandas as pd
from datetime import date, timedelta
from sqlalchemy import text
import plotly.graph_objects as go
import calendar

def gauge_rentabilidade(valor_atual, meta_percentual):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=valor_atual,
        number={'suffix': "%", 'font': {'size': 28}},  # aumentei aqui
        delta={
            'reference': meta_percentual,
            'increasing': {'color': "#4CAF50"},
            'decreasing': {'color': "#EB354D"},
            'position': "bottom",
            'font': {'size': 18}  # opcional: aumenta delta também
        },
        gauge={
            'shape': "angular",
            'axis': {'range': [0, max(20, meta_percentual * 1.5)], 'tickwidth': 0.5},
            'bar': {'color': "black", 'thickness': 0.3},
            'steps': [
                {'range': [0, meta_percentual], 'color': "#E9633A"},
                {'range': [meta_percentual, max(20, meta_percentual * 1.5)], 'color': '#dddddd'}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': valor_atual
            }
        },
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Meta Rentabilidade", 'font': {'size': 14}}
    ))

    fig.update_layout(
        margin=dict(t=10, b=0, l=0, r=0),
        height=120
    )
    return fig

def formatar_faturamento(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def mini_card(icone, titulo, valor, cor="#E9633A"):
    return f"""
    <div style="background: white; border-radius: 8px; border: 2px solid {cor}; width: 220px; height: 77px;
                display: flex; align-items: center; gap: 10px; padding: 10px; margin: 10px auto;">
        <div style="font-size: 24px; color: {cor};">{icone}</div>
        <div style="display: flex; flex-direction: column; line-height: 1.2;">
            <div style="font-size: 12px; font-weight: 600;">{titulo}</div>
            <div style="font-size: 16px; font-weight: bold; color: {cor};">{valor}</div>
        </div>
    </div>
    """

def mini_gauge_card(label, valor_atual, meta, cor="#E9633A"):
    if meta is None or valor_atual is None or meta <= 0:
        return ""
    percentual = round((valor_atual / meta) * 100, 2)
    largura = min(max(percentual, 0), 100)
    valor_formatado = formatar_faturamento(valor_atual)
    meta_formatada = formatar_faturamento(meta)
    cor_barra = cor if percentual < 100 else "#4CAF50"
    return f"""
    <div style="background: white; border-radius: 8px; border: 2px solid {cor}; width: 220px; height: 77px;
                display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 10px; margin: 10px auto;">
        <div style="font-size: 12px; font-weight: 600;">{label}</div>
        <div style="font-size: 16px; font-weight: bold; color: {cor};">{valor_formatado}</div>
        <div style="position: relative; background-color: #ddd; border-radius: 6px; width: 90%; height: 7px; margin: 4px 0 2px 0;">
            <div style="background-color: {cor_barra}; width: {largura}%; height: 100%; border-radius: 6px;"></div>
        </div>
        <div style="font-size: 11px; text-align:center;">
            🌟 Meta {meta_formatada} — <b>{percentual:.2f}%</b>
        </div>
    </div>
    """

def grafico_ultimos_7_dias(conn_faturamento, loja_codigo):
    hoje = date.today()
    data_fim_7d = hoje - timedelta(days=1)
    data_inicio_7d = data_fim_7d - timedelta(days=6)

    query_7d = text("""
        SELECT BIIFDATA::DATE AS data, SUM(BIIFVTOT) AS faturamento
        FROM bi_biif
        LEFT JOIN BI_CADA VEND ON VEND.BI_CADACODI = BIIFVEND
        LEFT JOIN BI_TABE ON BI_TABE.BI_TABECODI = VEND.BI_CADATPVN AND BI_TABE.BI_TABEINDI = 30
        WHERE BIIFEMPE = 3
          AND BIIFDATA BETWEEN :data_ini AND :data_fim
          AND BI_TABE.BI_TABEDESC IN ('AUTO SERVICO', 'VENDEDORES LOJA FÍSICA')
        GROUP BY data
        ORDER BY data;
    """)

    df_7d = pd.read_sql(query_7d, conn_faturamento, params={
        "loja_codigo": loja_codigo,
        "data_ini": data_inicio_7d,
        "data_fim": data_fim_7d
    })

    df_7d["data"] = pd.to_datetime(df_7d["data"], errors='coerce')
    df_7d = df_7d.set_index("data").reindex(pd.date_range(data_inicio_7d, data_fim_7d)).fillna(0).reset_index()
    df_7d.columns = ["Data", "Faturamento Líquido"]
    df_7d["DataFormatada"] = df_7d["Data"].dt.strftime("%d/%m")

    fig7d = go.Figure()
    fig7d.add_trace(go.Bar(
        x=df_7d["DataFormatada"],
        y=df_7d["Faturamento Líquido"],
        marker_color="#E9633A",
        text=[formatar_faturamento(valor) for valor in df_7d["Faturamento Líquido"]],
        textposition='inside',
        insidetextanchor='middle',
        textfont=dict(
            family="Arial",
            size=14,
            color="white"
        )
    ))

    fig7d.update_layout(
        xaxis_title="Data",
        yaxis_title="Faturamento Líquido (R$)",
        height=270,
        margin=dict(l=10, r=10, t=30, b=20),
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
        font=dict(size=13),
        showlegend=False,
    )

    fig7d.update_yaxes(tickprefix="R$ ", showgrid=True, zeroline=True)

    st.plotly_chart(fig7d, use_container_width=True)


def mostrar_maua(conn_faturamento, conn_fluxo):
    # Botão Voltar ao Menu
    if st.button("🔙 Voltar ao Menu", key="voltar_menu_maua"):
        st.session_state.pagina = "menu"
        st.rerun()

    # Botões iguais aos do Santo André
    col_a, col_b, col_c = st.columns([1, 1, 4])
    with col_a:
        if st.button("👥 Equipe Mauá", key="btn_vendedores_maua"):
            st.session_state["pagina"] = "vendedores_maua"
            st.rerun()
    with col_b:
        if st.button("📲 Venda Assistida Mauá", key="btn_assistida_maua"):
            st.session_state["pagina"] = "venda_assistida_maua"
            st.rerun()

    st.divider()

    st.markdown("<h2 style='text-align:center'>📍 Mauá - Painel Integrado</h2>", unsafe_allow_html=True)

    

    col1, col2, _ = st.columns([1, 1, 4])
    with col1:
        data_inicio = st.date_input("Data Inicial", value=date.today(), key="data_inicio_maua")
    with col2:
        data_fim = st.date_input("Data Final", value=date.today(), key="data_fim_maua")

    loja_codigo = 1132  # código Mauá
    loja_codigo_fluxo = "3"
    cor = "#E9633A"
    meta_total = 4525283  # ajuste a meta mensal conforme dados reais
    hoje = date.today()
    ano = hoje.year
    mes = hoje.month
    total_dias_mes = calendar.monthrange(ano, mes)[1]
    inicio_mes = hoje.replace(day=1)

    dias_corridos = (hoje - inicio_mes).days + 1
    dias_restantes = total_dias_mes - dias_corridos + 1

    # Consulta acumulado até ontem
    data_ontem = hoje - timedelta(days=1)
    query_acumulado_mes = text("""
        SELECT SUM(BIIFVTOT) AS total
        FROM bi_biif
        LEFT JOIN BI_CADA VEND ON VEND.BI_CADACODI = BIIFVEND
        LEFT JOIN BI_TABE ON BI_TABE.BI_TABECODI = VEND.BI_CADATPVN AND BI_TABE.BI_TABEINDI = 30
        WHERE BIIFEMPE = 3
          AND BIIFDATA BETWEEN :inicio AND :fim
          AND BI_TABE.BI_TABEDESC IN ('AUTO SERVICO','VENDEDORES LOJA FÍSICA')
    """)
    df_mes = pd.read_sql(query_acumulado_mes, conn_faturamento, params={
       "inicio": inicio_mes,
       "fim": data_ontem
    })    
    acumulado = float(df_mes["total"].iloc[0] or 0)

    meta_dinamica = (meta_total - acumulado) / dias_restantes if dias_restantes > 0 else 0

    meta_diaria = meta_total / total_dias_mes  # Meta diária fixa para comparação

    # Faturamento total
    query_faturamento = text("""
        SELECT SUM(BIIFVTOT) AS faturamento
        FROM bi_biif
        LEFT JOIN BI_CADA VEND ON VEND.BI_CADACODI = BIIFVEND
        LEFT JOIN BI_TABE ON BI_TABE.BI_TABECODI = VEND.BI_CADATPVN AND BI_TABE.BI_TABEINDI = 30
        WHERE BIIFDATA BETWEEN :data_inicio AND :data_fim
          AND BIIFEMPE = 3
          AND BI_TABE.BI_TABEDESC IN ('AUTO SERVICO','VENDEDORES LOJA FÍSICA')
    """)
    result_fat = conn_faturamento.execute(query_faturamento, {"data_inicio": data_inicio, "data_fim": data_fim}).fetchone()
    faturamento_total = float(result_fat[0]) if result_fat and result_fat[0] else 0

    # Vendas total
    query_vendas = text("""
        SELECT COUNT(DISTINCT BIIFCPRI) AS vendas
        FROM bi_biif
        LEFT JOIN BI_CADA VEND ON VEND.BI_CADACODI = BIIFVEND
        LEFT JOIN BI_TABE ON BI_TABE.BI_TABECODI = VEND.BI_CADATPVN AND BI_TABE.BI_TABEINDI = 30
        WHERE BIIFDATA BETWEEN :data_inicio AND :data_fim
          AND BIIFEMPE = 3
          AND BIIFPVEN = 'S'
          AND BI_TABE.BI_TABEDESC IN ('AUTO SERVICO','VENDEDORES LOJA FÍSICA')
    """)
    result_vendas = conn_faturamento.execute(query_vendas, {"data_inicio": data_inicio, "data_fim": data_fim}).fetchone()
    vendas_total = int(result_vendas[0]) if result_vendas and result_vendas[0] else 0

    # Fluxo de pessoas
    query_fluxo = """
        SELECT SUM(fluxo) AS total
        FROM virtual_gate
        WHERE loja = %s AND emissao BETWEEN %s AND %s
    """
    df_fluxo = pd.read_sql(query_fluxo, conn_fluxo, params=(loja_codigo_fluxo, data_inicio, data_fim))
    fluxo_total = int(df_fluxo["total"].iloc[0]) if not df_fluxo.empty and df_fluxo["total"].iloc[0] else 0

    ticket_medio = faturamento_total / max(vendas_total, 1)
    conversao = (vendas_total / fluxo_total * 100) if fluxo_total > 0 else 0

    # Rentabilidade
    query_rentabilidade = text("""
        SELECT 
            SUM(BIIFPLIQ) AS vendaliq,
            SUM(BIIFCREP) AS cmv,
            SUM(BIIFVARI + BIIFCOMB + BIIFCOMC + BIIFICMC) AS custovar,
            SUM(BIIFFIXO) AS custofixo
        FROM BI_BIIF
        LEFT JOIN BI_CADA VEND ON VEND.BI_CADACODI = BIIFVEND
        LEFT JOIN BI_TABE ON BI_TABE.BI_TABECODI = VEND.BI_CADATPVN AND BI_TABE.BI_TABEINDI = 30
        WHERE BIIFEMPE = 3
          AND BIIFDATA BETWEEN :inicio AND :fim
          AND BI_TABE.BI_TABEDESC IN ('AUTO SERVICO','VENDEDORES LOJA FÍSICA')
    """)
    df_rent = pd.read_sql(query_rentabilidade, conn_faturamento, params={
        "inicio": data_inicio,
        "fim": data_fim
    })

    if not df_rent.empty:
        vendaliq = float(df_rent["vendaliq"].iloc[0] or 0)
        cmv = float(df_rent["cmv"].iloc[0] or 0)
        custovar = float(df_rent["custovar"].iloc[0] or 0)
        custofixo = float(df_rent["custofixo"].iloc[0] or 0)
        rentabilidade = vendaliq - cmv - custovar - custofixo
        percentual_rentabilidade = (rentabilidade / vendaliq * 100) if vendaliq else 0
    else:
        rentabilidade = 0
        percentual_rentabilidade = 0

    st.markdown("<h4 style='text-align:center;'>📊 Visão Geral</h4>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2.2, 1])

    with col1:
        st.markdown(mini_card("💰", "Faturamento", formatar_faturamento(faturamento_total), cor), unsafe_allow_html=True)
        st.markdown(mini_card("📟", "Vendas", f"{vendas_total}", cor), unsafe_allow_html=True)
        st.markdown(mini_card("🧍‍♂️", "Fluxo de Pessoas", f"{fluxo_total}", cor), unsafe_allow_html=True)
        st.markdown(mini_card("🔁", "Conversão", f"{conversao:.2f}%", cor), unsafe_allow_html=True)
        st.markdown(mini_gauge_card("Meta mensal", acumulado, meta_total, cor), unsafe_allow_html=True)

    with col3:
        st.markdown(mini_card("🎟️", "Ticket Médio", formatar_faturamento(ticket_medio), cor), unsafe_allow_html=True)
        st.markdown(mini_card("🗓️", "Meta Diária Dinâmica", formatar_faturamento(meta_dinamica), cor), unsafe_allow_html=True)
        st.markdown(mini_card("📊", "% Rentabilidade", f"{percentual_rentabilidade:.2f}%", cor), unsafe_allow_html=True)
        st.markdown(mini_card("📈", "Rentabilidade", formatar_faturamento(rentabilidade), cor), unsafe_allow_html=True)
        meta_rentabilidade_percentual = 8.50
        st.plotly_chart(gauge_rentabilidade(percentual_rentabilidade, meta_rentabilidade_percentual), use_container_width=True)

    with col2:
        st.markdown("<h5 style='text-align:center; margin-bottom: 10px;'>📉 Faturamento Corrido x Meta Diária</h5>", unsafe_allow_html=True)
        query_faturamento_dias = text("""
            SELECT BIIFDATA::DATE AS data, SUM(BIIFVTOT) AS valor
            FROM bi_biif
            LEFT JOIN BI_CADA VEND ON VEND.BI_CADACODI = BIIFVEND
            LEFT JOIN BI_TABE ON BI_TABE.BI_TABECODI = VEND.BI_CADATPVN AND BI_TABE.BI_TABEINDI = 30
            WHERE BIIFEMPE =3
              AND BIIFDATA BETWEEN :data_ini AND :data_fim
              AND BI_TABE.BI_TABEDESC IN ('AUTO SERVICO','VENDEDORES LOJA FÍSICA')
            GROUP BY data
            ORDER BY data
        """)
        df_dias = pd.read_sql(query_faturamento_dias, conn_faturamento, params={
            "data_ini": inicio_mes,
            "data_fim": hoje
        })
        df_dias["data"] = pd.to_datetime(df_dias["data"])
        df_dias = df_dias.set_index("data").reindex(pd.date_range(inicio_mes, hoje)).fillna(0).reset_index()
        df_dias.columns = ["data", "valor"]

        df_dias["meta"] = meta_diaria
        df_dias["acima"] = df_dias["valor"].apply(lambda x: x if x >= meta_diaria else 0)
        df_dias["abaixo"] = df_dias["valor"].apply(lambda x: x if x < meta_diaria else 0)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_dias["data"], y=df_dias["acima"], name="Acima da meta", marker_color="#E9633A"))
        fig.add_trace(go.Bar(x=df_dias["data"], y=df_dias["abaixo"], name="Abaixo da meta", marker_color="#F1B19D"))
        fig.add_trace(go.Scatter(x=df_dias["data"], y=df_dias["meta"], mode="lines+markers", name="Meta Corridos", line=dict(color="black", dash="dash")))
        fig.update_layout(barmode="stack", height=320, margin=dict(l=10, r=10, t=10, b=30))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<h5 style='text-align:center; margin-top: 24px;'>📉 Faturamento Líquido - Últimos 7 Dias</h5>", unsafe_allow_html=True)
    grafico_ultimos_7_dias(conn_faturamento, loja_codigo)
