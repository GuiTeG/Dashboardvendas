import streamlit as st
from sqlalchemy import create_engine

def conectar_virtual_gate():
    creds = st.secrets
    engine = create_engine(
        f"postgresql://{creds.DB_USER}:{creds.DB_PASSWORD}@{creds.DB_HOST}:{creds.DB_PORT}/{creds.DB_NAME}"
    )
    return engine.connect()

def conectar_faturamento():
    creds = st.secrets
    engine = create_engine(
        f"postgresql://{creds.FATURAMENTO_DB_USER}:{creds.FATURAMENTO_DB_PASSWORD}@"
        f"{creds.FATURAMENTO_DB_HOST}:{creds.FATURAMENTO_DB_PORT}/{creds.FATURAMENTO_DB_NAME}"
    )
    return engine.connect()

def conectar_producao():
    creds = st.secrets["PROD_DB"]
    engine = create_engine(
        f"postgresql://{creds['PROD_DB_USER']}:{creds['PROD_DB_PASSWORD']}@"
        f"{creds['PROD_DB_HOST']}:{creds['PROD_DB_PORT']}/{creds['PROD_DB_NAME']}"
    )
    return engine.connect()



