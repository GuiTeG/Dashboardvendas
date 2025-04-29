import streamlit as st
import pandas as pd
from datetime import date
import time

def mostrar_kpi(conn):
    st.markdown("<h1 style='text-align: center;'>📌 Fluxo - Loja 1</h1>", unsafe_allow_html=True)
    st.divider()

    # Seleção de datas
    data_inicio = st.date_input("Data de Início", min_value=pd.to_datetime('2020-01-01'), max_value=date.today())
    data_fim = st.date_input("Data de Fim", min_value=data_inicio, max_value=date.today())

    # Garantir que as datas selecionadas sejam do tipo 'date'
    data_inicio = data_inicio.strftime('%Y-%m-%d')
    data_fim = data_fim.strftime('%Y-%m-%d')

    # Função para obter o total de fluxo entre duas datas
    def obter_total_fluxo(data_inicio, data_fim):
        query = f"""
            SELECT SUM(fluxo) as total
            FROM virtual_gate
            WHERE loja = '1'
            AND emissao BETWEEN '{data_inicio}' AND '{data_fim}'
        """
        resultado = pd.read_sql_query(query, conn)
        return int(resultado["total"].fillna(0).values[0])

    # KPIs principais com base nas datas selecionadas
    fluxo_hoje = obter_total_fluxo(data_inicio, data_fim)

    # Dividir as colunas para exibir os KPIs
    col1, = st.columns(1)  # Para exibir uma única coluna
    with col1:
        st.markdown(kpi_card("Fluxo Hoje", fluxo_hoje), unsafe_allow_html=True)

    # Função para atualizar automaticamente a cada 5 minutos
    while True:
        time.sleep(300)  # Aguarda 5 minutos (300 segundos)
        st.experimental_rerun()  # Força a atualização da página

def kpi_card(titulo, valor):
    return f"""
    <div class='kpi-card'>
        <div class='kpi-title'>{titulo}</div>
        <div class='kpi-value'>{valor}</div>
    </div>
    """ 
