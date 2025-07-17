def fmt(value: float) -> str:
    """Форматирует число с разделителем-разрядов и убирает .00."""
    text = f"{value:,.2f}".replace(",", " ")
    return text[:-3] if text.endswith(".00") else text

def color_circle(dif_rub: float,dif_usd: float) -> str:
    if dif_rub >= 0 and dif_usd >= 0:
        return "🟢"
    elif dif_rub <= 0 and dif_usd <= 0:
        return "🔴"
    else:
        return "🟡"