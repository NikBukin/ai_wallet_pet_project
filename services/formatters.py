def fmt(value: float) -> str:
    """Форматирует число с разделителем-разрядов и убирает .00."""
    text = f"{value:,.2f}".replace(",", " ")
    return text[:-3] if text.endswith(".00") else text

def color_circle(value: float) -> str:
    """🟢 если >=0, иначе 🔴."""
    return "🟢" if value >= 0 else "🔴"