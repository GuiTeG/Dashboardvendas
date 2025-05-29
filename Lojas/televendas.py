import streamlit as st
import pandas as pd
from datetime import date, timedelta
import calendar
from sqlalchemy import text
import plotly.graph_objects as go

def gauge_rentabilidade(valor_atual, meta_percentual):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=valor_atual,
        number={'suffix': "%", 'font': {'size': 28}},  # Aumentei o tamanho para 28
        delta={
            'reference': meta_percentual,
            'increasing': {'color': "#4CAF50"},
            'decreasing': {'color': "#EB354D"},
            'position': "bottom",
            'font': {'size': 18}  # opcional para delta
        },
        gauge={
            'shape': "angular",
            'axis': {'range': [0, max(20, meta_percentual * 1.5)], 'tickwidth': 0.5},
            'bar': {'color': "black", 'thickness': 0.3},
            'steps': [
                {'range': [0, meta_percentual], 'color': "#79A93B"},
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

def mini_card(icone, titulo, valor, cor="#79A93B"):
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

def mini_gauge_card(label, valor_atual, meta, cor="#79A93B"):
    if not meta or not valor_atual:
        return ""
    percentual = round((valor_atual / meta) * 100, 2)
    largura = min(percentual, 100)
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

def grafico_acumulado_meta(conn_faturamento, loja_codigo, inicio_mes, hoje, meta_diaria):
    query = text("""
        SELECT BIIFDATA::DATE AS data, SUM(BIIFVTOT) AS valor
        FROM bi_biif
        WHERE BIIFGERE = :loja_codigo
          AND BIIFDATA BETWEEN :inicio AND :fim
        GROUP BY data
        ORDER BY data
    """)
    df = pd.read_sql(query, conn_faturamento, params={
        "loja_codigo": loja_codigo,
        "inicio": inicio_mes,
        "fim": hoje
    })
    df["data"] = pd.to_datetime(df["data"])
    df = df.set_index("data").reindex(pd.date_range(inicio_mes, hoje)).fillna(0).reset_index()
    df.columns = ["data", "valor"]

    df["meta"] = meta_diaria
    df["acima"] = df["valor"].apply(lambda x: x if x >= meta_diaria else 0)
    df["abaixo"] = df["valor"].apply(lambda x: x if x < meta_diaria else 0)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["data"], y=df["acima"], name="Acima da meta", marker_color="#79A93B"))
    fig.add_trace(go.Bar(x=df["data"], y=df["abaixo"], name="Abaixo da meta", marker_color="#9EB383"))
    fig.add_trace(go.Scatter(x=df["data"], y=df["meta"], mode="lines+markers", name="Meta Diária", line=dict(color="black", dash="dash")))
    fig.update_layout(
        barmode="stack",
        height=320,
        margin=dict(l=10, r=10, t=10, b=30),
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
        width=700,
    )
    return fig

def grafico_ultimos_7_dias(conn_faturamento, loja_codigo):
    hoje = date.today()
    data_fim_7d = hoje - timedelta(days=1)
    data_inicio_7d = data_fim_7d - timedelta(days=6)

    query_7d = text("""
        SELECT BIIFDATA::DATE AS data, SUM(BIIFVTOT) AS faturamento
        FROM bi_biif
        WHERE BIIFGERE = :loja_codigo
          AND BIIFDATA BETWEEN :data_ini AND :data_fim
        GROUP BY data
        ORDER BY data
    """)

    df_7d = pd.read_sql(query_7d, conn_faturamento, params={
        "loja_codigo": loja_codigo,
        "data_ini": data_inicio_7d,
        "data_fim": data_fim_7d
    })

    df_7d["data"] = pd.to_datetime(df_7d["data"])
    df_7d = df_7d.set_index("data").reindex(pd.date_range(data_inicio_7d, data_fim_7d)).fillna(0).reset_index()
    df_7d.columns = ["Data", "Faturamento Líquido"]
    df_7d["DataFormatada"] = df_7d["Data"].dt.strftime("%d/%m")

    fig7d = go.Figure()

    fig7d.add_trace(go.Bar(
        x=df_7d["DataFormatada"],
        y=df_7d["Faturamento Líquido"],
        marker_color="#79A93B",  # Cor do gráfico
        text=[formatar_faturamento(valor) for valor in df_7d["Faturamento Líquido"]],
        textposition='inside',  # Colocando o texto dentro das barras
        insidetextanchor='middle',  # Centraliza o texto dentro das barras
        textfont=dict(
            family="Arial",  # Fonte personalizada
            size=14,         # Tamanho da fonte
            color="white"    # Cor da fonte
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
    return fig7d

def mostrar_televendas(conn_faturamento):
    if st.button("🔙 Voltar ao Menu", key="voltar_menu_televendas"):
        st.session_state["pagina"] = "menu"
        st.rerun()

    # Botão para abrir aba vendedores Televendas
    if st.button("👥 Equipe Televendas", key="btn_vendedores_televendas"):
        st.session_state["pagina"] = "vendedores_televendas"
        st.rerun()

    st.markdown("<h2 style='text-align:center'>📞 Televendas - Painel Integrado</h2>", unsafe_allow_html=True)

    st.divider()

    # ... resto do código da sua dashboard aqui ...


    # (restante do código)


    # Filtros data lado a lado, colunas pequenas
    col1, col2, _ = st.columns([1, 1, 4])
    with col1:
        data_inicio = st.date_input("Data Inicial", value=date.today(), key="data_inicio_maua")
    with col2:
        data_fim = st.date_input("Data Final", value=date.today(), key="data_fim_maua")

    loja_codigo = 1115
    cor = "#79A93B"
    meta_total = 1440977

    hoje = date.today()
    ontem = hoje - timedelta(days=1)
    ano = hoje.year
    mes = hoje.month
    total_dias_mes = calendar.monthrange(ano, mes)[1]
    inicio_mes = hoje.replace(day=1)

    meta_diaria = meta_total / total_dias_mes  # Meta fixa diária

    # Função para contar domingos entre duas datas
    def contar_domingos(inicio, fim):
        count = 0
        current = inicio
        while current <= fim:
            if current.weekday() == 6:  # domingo = 6
                count += 1
            current += timedelta(days=1)
        return count

    dias_corridos_ate_ontem = (ontem - inicio_mes).days + 1

    inicio_periodo_restante = ontem + timedelta(days=1)
    fim_periodo = hoje.replace(day=total_dias_mes)

    domingos_restantes = contar_domingos(inicio_periodo_restante, fim_periodo)

    dias_restantes_uteis = total_dias_mes - dias_corridos_ate_ontem - domingos_restantes

    # Consultas básicas
    query_fat = text("""
        SELECT SUM(BIIFVTOT) AS faturamento
        FROM bi_biif
        WHERE BIIFDATA BETWEEN :data_inicio AND :data_fim
          AND BIIFGERE = :loja_codigo
    """)
    result_fat = conn_faturamento.execute(query_fat, {"data_inicio": data_inicio, "data_fim": data_fim, "loja_codigo": loja_codigo}).fetchone()
    faturamento_total = float(result_fat[0]) if result_fat and result_fat[0] else 0

    query_vendas = text("""
        SELECT COUNT(DISTINCT BIIFCPRI) AS vendas
        FROM bi_biif
        WHERE BIIFDATA BETWEEN :data_inicio AND :data_fim
          AND BIIFGERE = :loja_codigo
    """)
    result_vendas = conn_faturamento.execute(query_vendas, {"data_inicio": data_inicio, "data_fim": data_fim, "loja_codigo": loja_codigo}).fetchone()
    vendas_total = int(result_vendas[0]) if result_vendas and result_vendas[0] else 0

    ticket_medio = faturamento_total / max(vendas_total, 1)

    # Consulta acumulado mês para meta dinâmica (até ontem)
    query_acumulado = text("""
        SELECT SUM(BIIFVTOT) AS total
        FROM bi_biif
        WHERE BIIFGERE = :loja_codigo
          AND BIIFDATA BETWEEN :inicio AND :fim
    """)
    df_mes = pd.read_sql(query_acumulado, conn_faturamento, params={
        "loja_codigo": loja_codigo,
        "inicio": inicio_mes,
        "fim": ontem
    })
    acumulado = float(df_mes["total"].iloc[0] or 0)

    meta_dinamica = (meta_total - acumulado) / dias_restantes_uteis if dias_restantes_uteis > 0 else 0

    # Consulta rentabilidade e cálculo % rentabilidade
    query_rent = text("""
        SELECT 
            SUM(BIIFPLIQ) AS vendaliq,
            SUM(BIIFCREP) AS cmv,
            SUM(BIIFVARI + BIIFCOMB + BIIFCOMC + BIIFICMC) AS custovar,
            SUM(BIIFFIXO) AS custofixo
        FROM BI_BIIF
        WHERE BIIFGERE = :loja_codigo
          AND BIIFDATA BETWEEN :data_inicio AND :data_fim
    """)
    df_rent = pd.read_sql(query_rent, conn_faturamento, params={
        "loja_codigo": loja_codigo,
        "data_inicio": data_inicio,
        "data_fim": data_fim
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

    # Layout dos cards e gráfico central
    st.markdown("<h4 style='text-align:center;'>📊 Visão Geral</h4>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2.2, 1])

    with col1:
        st.markdown(mini_card("💰", "Faturamento", formatar_faturamento(faturamento_total), cor), unsafe_allow_html=True)
        st.markdown(mini_card("🧾", "Vendas", f"{vendas_total}", cor), unsafe_allow_html=True)
        st.markdown(mini_card("🎟️", "Ticket Médio", formatar_faturamento(ticket_medio), cor), unsafe_allow_html=True)
        st.markdown(mini_gauge_card("Meta mensal", acumulado, meta_total, cor), unsafe_allow_html=True)

    with col2:
        st.markdown("<h5 style='text-align:center; margin-bottom: 10px;'>📈 Faturamento Acumulado x Meta Diária</h5>", unsafe_allow_html=True)
        fig_acum = grafico_acumulado_meta(conn_faturamento, loja_codigo, inicio_mes, hoje, meta_diaria)
        st.plotly_chart(fig_acum, use_container_width=True)

    with col3:
        st.markdown(mini_card("🗓️", "Meta Diária Dinâmica", formatar_faturamento(meta_dinamica), cor), unsafe_allow_html=True)
        st.markdown(mini_card("📊", "% Rentabilidade", f"{percentual_rentabilidade:.2f}%", cor), unsafe_allow_html=True)
        st.markdown(mini_card("📈", "Rentabilidade", formatar_faturamento(rentabilidade), cor), unsafe_allow_html=True)
        meta_rentabilidade_percentual = 13.51
        st.plotly_chart(gauge_rentabilidade(percentual_rentabilidade, meta_rentabilidade_percentual), use_container_width=True)

    # Gráfico últimos 7 dias
    st.markdown("<h5 style='text-align:center; margin-top: 24px;'>📉 Faturamento Líquido - Últimos 7 Dias</h5>", unsafe_allow_html=True)
    fig_7d = grafico_ultimos_7_dias(conn_faturamento, loja_codigo)
    st.plotly_chart(fig_7d, use_container_width=True)
