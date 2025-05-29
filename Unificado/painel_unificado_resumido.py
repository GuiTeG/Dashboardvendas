import streamlit as st
from sqlalchemy import text
from datetime import date, datetime

def botao_voltar_menu():
    if st.button("🔙 Voltar ao Menu", key="voltar_menu"):
        st.session_state.pagina = "menu"
        st.rerun()

def formatar_faturamento(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def mini_card(icone, titulo, valor, cor="#EB354D"):
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

def mini_gauge_card(label, valor_atual, meta, cor="#EB354D"):
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

def mostrar_kpis(
    nome, cor, loja_codigo, loja_codigo_fluxo, meta_total,
    conn_faturamento, conn_fluxo, campo_loja, desc_filtro,
    mostrar_fluxo=True, data_inicio=None, data_fim=None
):
    # data_inicio e data_fim devem ser objetos date (já são no seu fluxo)
    if data_inicio is None:
        data_inicio = date.today()
    if data_fim is None:
        data_fim = date.today()

    # Faturamento
    fat = conn_faturamento.execute(text(f"""
        SELECT SUM(BIIFVTOT) AS faturamento
        FROM bi_biif
        LEFT JOIN BI_CADA VEND ON VEND.BI_CADACODI = BIIFVEND
        LEFT JOIN BI_TABE ON BI_TABE.BI_TABECODI = VEND.BI_CADATPVN AND BI_TABE.BI_TABEINDI = 30
        WHERE BIIFDATA BETWEEN :inicio AND :fim AND {campo_loja} = :loja_codigo
          AND BI_TABE.BI_TABEDESC IN ({desc_filtro})
    """), {"loja_codigo": loja_codigo, "inicio": data_inicio, "fim": data_fim}).fetchone()
    faturamento_total = float(fat[0]) if fat and fat[0] else 0

    # Vendas
    vendas = conn_faturamento.execute(text(f"""
        SELECT COUNT(DISTINCT BIIFCPRI) AS vendas
        FROM bi_biif
        LEFT JOIN BI_CADA VEND ON VEND.BI_CADACODI = BIIFVEND
        LEFT JOIN BI_TABE ON BI_TABE.BI_TABECODI = VEND.BI_CADATPVN AND BI_TABE.BI_TABEINDI = 30
        WHERE BIIFDATA BETWEEN :inicio AND :fim AND {campo_loja} = :loja_codigo
          AND BIIFPVEN = 'S' AND BI_TABE.BI_TABEDESC IN ({desc_filtro})
    """), {"loja_codigo": loja_codigo, "inicio": data_inicio, "fim": data_fim}).fetchone()
    vendas_total = int(vendas[0]) if vendas and vendas[0] else 0

    # Fluxo (se mostrar_fluxo e loja_codigo_fluxo)
    if mostrar_fluxo and loja_codigo_fluxo:
        fluxo = conn_fluxo.execute(text("""
            SELECT SUM(fluxo) AS total
            FROM virtual_gate
            WHERE loja = :loja AND emissao BETWEEN :inicio AND :fim
        """), {"loja": loja_codigo_fluxo, "inicio": data_inicio, "fim": data_fim}).fetchone()
        fluxo_total = int(fluxo[0]) if fluxo and fluxo[0] else 0
        fluxo_str = str(fluxo_total)
        conversao = (vendas_total / fluxo_total * 100) if fluxo_total > 0 else 0
        conversao_str = f"{conversao:.2f}%"
    else:
        fluxo_str = None
        conversao_str = None

    ticket_medio = faturamento_total / max(vendas_total, 1)

    # Acumulado mês
    inicio_mes_acum = date(data_fim.year, data_fim.month, 1)
    acumulado = conn_faturamento.execute(text(f"""
        SELECT SUM(BIIFVTOT) AS total
        FROM bi_biif
        LEFT JOIN BI_CADA VEND ON VEND.BI_CADACODI = BIIFVEND
        LEFT JOIN BI_TABE ON BI_TABE.BI_TABECODI = VEND.BI_CADATPVN AND BI_TABE.BI_TABEINDI = 30
        WHERE {campo_loja} = :loja_codigo
          AND BIIFDATA BETWEEN :inicio_acum AND :fim
          AND BI_TABE.BI_TABEDESC IN ({desc_filtro})
    """), {"loja_codigo": loja_codigo, "inicio_acum": inicio_mes_acum, "fim": data_fim}).fetchone()
    acumulado_valor = float(acumulado[0]) if acumulado and acumulado[0] else 0

    # --- NOVOS INDICADORES ---
    sql_kpi = f"""
        SELECT
            COALESCE(SUM(BIIFVTOT),0) AS faturamento,
            COALESCE(SUM(BIIFPLIQ),0) AS venda_liq,
            COALESCE(SUM(BIIFCREP),0) AS cmv,
            COALESCE(SUM(BIIFVARI + BIIFCOMB + BIIFCOMC + BIIFICMC),0) AS custo_var,
            COALESCE(SUM(BIIFFIXO),0) AS custo_fixo,
            COALESCE(SUM(BIIFAVIS),0) AS venda_a_vista,
            COALESCE(SUM(BIIFPRAZ * BIIFPLIQ),0) AS prazo_recebimento,
            COALESCE(SUM(CASE WHEN BIIFVTOT < 0 THEN BIIFVTOT * -1 ELSE 0 END),0) AS devolucao_liq,
            COALESCE(SUM(CASE WHEN BIIFPTAB > BIIFPLIQ THEN BIIFPTAB - BIIFPLIQ ELSE 0 END),0) AS descontos
        FROM bi_biif
        LEFT JOIN BI_CADA VEND ON VEND.BI_CADACODI = BIIFVEND
        LEFT JOIN BI_TABE ON BI_TABE.BI_TABECODI = VEND.BI_CADATPVN AND BI_TABE.BI_TABEINDI = 30
        WHERE
            BIIFDATA BETWEEN :inicio AND :fim
            AND {campo_loja} = :loja_codigo
            AND BI_TABE.BI_TABEDESC IN ({desc_filtro})
    """
    params = {"loja_codigo": loja_codigo, "inicio": data_inicio, "fim": data_fim}
    dados = conn_faturamento.execute(text(sql_kpi), params).fetchone()

    fat = float(dados[0]) if dados and dados[0] else 0
    venda_liq = float(dados[1]) if dados and dados[1] else 0
    cmv = float(dados[2]) if dados and dados[2] else 0
    custo_var = float(dados[3]) if dados and dados[3] else 0
    custo_fixo = float(dados[4]) if dados and dados[4] else 0
    venda_vista = float(dados[5]) if dados and dados[5] else 0
    prazo_recebimento = float(dados[6]) if dados and dados[6] else 0
    devolucao_liq = float(dados[7]) if dados and dados[7] else 0
    descontos = float(dados[8]) if dados and dados[8] else 0

    perc_devolucao = (devolucao_liq / fat) * 100 if fat else 0
    perc_desconto = (descontos / fat) * 100 if fat else 0
    perc_vista = (venda_vista / fat) * 100 if fat else 0
    prazo_medio = (prazo_recebimento / venda_liq) if venda_liq else 0
    rentabilidade = venda_liq - cmv - custo_var - custo_fixo
    perc_rentabilidade = (rentabilidade / venda_liq) * 100 if venda_liq else 0

    # Exibição dos cards
    st.markdown(f"<h4 style='text-align:center; color:{cor};'>{nome}</h4>", unsafe_allow_html=True)
    st.markdown(mini_card("💰", "Faturamento", formatar_faturamento(faturamento_total), cor), unsafe_allow_html=True)
    st.markdown(mini_card("📟", "Vendas", str(vendas_total), cor), unsafe_allow_html=True)
    if mostrar_fluxo and fluxo_str is not None:
        st.markdown(mini_card("🧍‍♂️", "Fluxo de Pessoas", fluxo_str, cor), unsafe_allow_html=True)
    if conversao_str is not None:
        st.markdown(mini_card("🔁", "Conversão", conversao_str, cor), unsafe_allow_html=True)
    st.markdown(mini_card("🎟️", "Ticket Médio", formatar_faturamento(ticket_medio), cor), unsafe_allow_html=True)
    st.markdown(mini_gauge_card("Meta mensal", acumulado_valor, meta_total, cor), unsafe_allow_html=True)
    # Novos KPIs
    st.markdown(mini_card("🔁", "Devolução (R$)", formatar_faturamento(devolucao_liq), cor), unsafe_allow_html=True)
    st.markdown(mini_card("🌀", "% Devolução", f"{perc_devolucao:.2f}%", cor), unsafe_allow_html=True)
    st.markdown(mini_card("💸", "% Desconto", f"{perc_desconto:.2f}%", cor), unsafe_allow_html=True)
    st.markdown(mini_card("💵", "% Venda à Vista", f"{perc_vista:.2f}%", cor), unsafe_allow_html=True)
    st.markdown(mini_card("📆", "Prazo Médio Receb.", f"{prazo_medio:.1f} dias", cor), unsafe_allow_html=True)
    st.markdown(mini_card("🏆", "Rentabilidade (R$)", formatar_faturamento(rentabilidade), cor), unsafe_allow_html=True)
    st.markdown(mini_card("📈", "% Rentabilidade", f"{perc_rentabilidade:.2f}%", cor), unsafe_allow_html=True)

def painel_unificado_resumido(conn_faturamento, conn_fluxo):
    botao_voltar_menu()
    st.markdown("<h2 style='text-align: center; margin-bottom: 1.5rem;'>Painel Unificado - Copafer</h2>", unsafe_allow_html=True)

    hoje = datetime.now()

    col_f1, col_f2, _ = st.columns([1, 1, 8])

    with col_f1:
        data_inicio = st.date_input("Data Inicial", value=date.today())
    with col_f2:
        data_fim = st.date_input("Data Final", value=date.today())

    if data_inicio is None or data_fim is None:
        st.warning("Por favor, selecione as duas datas.")
        return

    if data_inicio > data_fim:
        st.warning("Data inicial não pode ser maior que a data final.")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        meta_sa = 6022608
        cor_sa = "#EB354D"
        mostrar_kpis(
            nome="Santo André",
            cor=cor_sa,
            loja_codigo=1,
            loja_codigo_fluxo="1",
            meta_total=meta_sa,
            conn_faturamento=conn_faturamento,
            conn_fluxo=conn_fluxo,
            campo_loja="BIIFEMPE",
            desc_filtro="'AUTO SERVICO','VENDEDORES LOJA FÍSICA'",
            mostrar_fluxo=True,
            data_inicio=data_inicio,
            data_fim=data_fim
        )

    with col2:
        meta_maua = 4525283
        cor_maua = "#E9633A"
        mostrar_kpis(
            nome="Mauá",
            cor=cor_maua,
            loja_codigo=3,
            loja_codigo_fluxo="3",
            meta_total=meta_maua,
            conn_faturamento=conn_faturamento,
            conn_fluxo=conn_fluxo,
            campo_loja="BIIFEMPE",
            desc_filtro="'AUTO SERVICO','VENDEDORES LOJA FÍSICA'",
            mostrar_fluxo=True,
            data_inicio=data_inicio,
            data_fim=data_fim
        )

    with col3:
        meta_tele = 1440977
        cor_tele = "#4CAF50"
        mostrar_kpis(
            nome="Televendas",
            cor=cor_tele,
            loja_codigo=1115,
            loja_codigo_fluxo=None,
            meta_total=meta_tele,
            conn_faturamento=conn_faturamento,
            conn_fluxo=conn_fluxo,
            campo_loja="BIIFGERE",
            desc_filtro="'TELEVENDAS'",
            mostrar_fluxo=False,
            data_inicio=data_inicio,
            data_fim=data_fim
        )

    with col4:
        meta_ecom = 1841774
        cor_ecom = "#6C63FF"
        mostrar_kpis(
            nome="E-commerce",
            cor=cor_ecom,
            loja_codigo=1122,
            loja_codigo_fluxo=None,
            meta_total=meta_ecom,
            conn_faturamento=conn_faturamento,
            conn_fluxo=conn_fluxo,
            campo_loja="BIIFGERE",
            desc_filtro="'E-COMMERCE'",
            mostrar_fluxo=False,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
