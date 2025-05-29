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
