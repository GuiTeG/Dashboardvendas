import streamlit as st
from sqlalchemy import text
from datetime import date

# Funções utilitárias para o visual dos cards
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

# Função para gerar os cards resumidos de cada unidade
def mostrar_resumido(nome, cor, loja_codigo, loja_codigo_fluxo, meta_total, conn_faturamento, conn_fluxo):
    hoje = date.today()
    inicio_mes = hoje.replace(day=1)

    # Faturamento
    fat = conn_faturamento.execute(text("""
        SELECT SUM(BIIFVTOT) AS faturamento
        FROM bi_biif
        LEFT JOIN BI_CADA VEND ON VEND.BI_CADACODI = BIIFVEND
        LEFT JOIN BI_TABE ON BI_TABE.BI_TABECODI = VEND.BI_CADATPVN AND BI_TABE.BI_TABEINDI = 30
        WHERE BIIFDATA = CURRENT_DATE AND BIIFEMPE = :loja_codigo
          AND BI_TABE.BI_TABEDESC IN ('AUTO SERVICO','VENDEDORES LOJA FÍSICA')
    """), {"loja_codigo": loja_codigo}).fetchone()
    faturamento_total = float(fat[0]) if fat and fat[0] else 0

    # Vendas
    vendas = conn_faturamento.execute(text("""
        SELECT COUNT(DISTINCT BIIFCPRI) AS vendas
        FROM bi_biif
        LEFT JOIN BI_CADA VEND ON VEND.BI_CADACODI = BIIFVEND
        LEFT JOIN BI_TABE ON BI_TABE.BI_TABECODI = VEND.BI_CADATPVN AND BI_TABE.BI_TABEINDI = 30
        WHERE BIIFDATA = CURRENT_DATE AND BIIFEMPE = :loja_codigo
          AND BIIFPVEN = 'S' AND BI_TABE.BI_TABEDESC IN ('AUTO SERVICO','VENDEDORES LOJA FÍSICA')
    """), {"loja_codigo": loja_codigo}).fetchone()
    vendas_total = int(vendas[0]) if vendas and vendas[0] else 0

    # Fluxo
    fluxo = conn_fluxo.execute(text("""
        SELECT SUM(fluxo) AS total
        FROM virtual_gate
        WHERE loja = :loja AND emissao = CURRENT_DATE
    """), {"loja": loja_codigo_fluxo}).fetchone()
    fluxo_total = int(fluxo[0]) if fluxo and fluxo[0] else 0

    ticket_medio = faturamento_total / max(vendas_total, 1)
    conversao = (vendas_total / fluxo_total * 100) if fluxo_total > 0 else 0

    # Acumulado mês
    acumulado = conn_faturamento.execute(text("""
        SELECT SUM(BIIFVTOT) AS total
        FROM bi_biif
        LEFT JOIN BI_CADA VEND ON VEND.BI_CADACODI = BIIFVEND
        LEFT JOIN BI_TABE ON BI_TABE.BI_TABECODI = VEND.BI_CADATPVN AND BI_TABE.BI_TABEINDI = 30
        WHERE BIIFEMPE = :loja_codigo
          AND BIIFDATA BETWEEN :inicio AND :fim
          AND BI_TABE.BI_TABEDESC IN ('AUTO SERVICO','VENDEDORES LOJA FÍSICA')
    """), {"loja_codigo": loja_codigo, "inicio": inicio_mes, "fim": hoje}).fetchone()
    acumulado_valor = float(acumulado[0]) if acumulado and acumulado[0] else 0

    st.markdown(f"<h4 style='text-align:center; color:{cor};'>{nome}</h4>", unsafe_allow_html=True)
    st.markdown(mini_card("💰", "Faturamento", formatar_faturamento(faturamento_total), cor), unsafe_allow_html=True)
    st.markdown(mini_card("📟", "Vendas", str(vendas_total), cor), unsafe_allow_html=True)
    st.markdown(mini_card("🧍‍♂️", "Fluxo de Pessoas", str(fluxo_total), cor), unsafe_allow_html=True)
    st.markdown(mini_card("🔁", "Conversão", f"{conversao:.2f}%", cor), unsafe_allow_html=True)
    st.markdown(mini_card("🎟️", "Ticket Médio", formatar_faturamento(ticket_medio), cor), unsafe_allow_html=True)
    st.markdown(mini_gauge_card("Meta mensal", acumulado_valor, meta_total, cor), unsafe_allow_html=True)

# --------- INÍCIO DO APP ---------
st.set_page_config(page_title="Painel Resumido - Santo André e Mauá", layout="wide")
st.title("Painel Resumido - Santo André e Mauá")

# Conexões (ajuste para seu contexto)
from conexoes import conectar_faturamento, conectar_virtual_gate
conn_faturamento = conectar_faturamento()
conn_fluxo = conectar_virtual_gate()

col1, col2 = st.columns(2)

with col1:
    mostrar_resumido("Santo André", "#EB354D", 1, "1", 6022608, conn_faturamento, conn_fluxo)
with col2:
    mostrar_resumido("Mauá", "#E9633A", 1132, "3", 4525283, conn_faturamento, conn_fluxo)
