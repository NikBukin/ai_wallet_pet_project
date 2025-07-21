import pandas as pd
from pars_info.pars_kotr import (
    get_cbr_currency_price,
    get_crypto_price_coingecko,
    get_moex_stock_price,
    get_foreign_stock_price,
)
from services.formatters import fmt, color_circle

# Словарь для отображения типов активов (эмодзи + название)
SLOV_TYPE = {
    "cripto": ("Криптовалюта", "🪙"),
    "stock_rus": ("Российские ценные бумаги", "📑"),
    "stock_for": ("Иностранные ценные бумаги", "📄"),
    "currency": ("Валюта", "💵"),
    "metal": ("Металл", "🥇"),
}


def det_text_to_report(df: pd.DataFrame) -> str:
    usd_rate = get_cbr_currency_price("USD")
    df = df.copy()
    df["total_buy_rub"] = df["amount_of_asset"] * df["purchase_price_of_one_asset_in_rubles"]
    df["total_buy_usd"] = df["amount_of_asset"] * df["purchase_price_of_one_asset_in_dollars"]

    df_grouped = (
        df
        .groupby(
            ["type_active", "name_of_the_asset", "second_name_of_the_asset"],
            as_index=False
        )
        .agg({
            "amount_of_asset": "sum",
            "total_buy_rub": "sum",
            "total_buy_usd": "sum",
        })
    )

    # 2) Для каждого сгруппированного актива запрашиваем текущую цену и считаем итоги
    rows = []
    for _, row in df_grouped.iterrows():
        ta = row["type_active"]
        symbol = row["second_name_of_the_asset"]
        name = row["name_of_the_asset"]
        cnt = row["amount_of_asset"]
        buy_rub = row["total_buy_rub"]
        buy_usd = row["total_buy_usd"]

        # вытаскиваем цену за единицу
        p_usd = p_rub = 0.0
        i = 1
        while p_usd == 0 and p_rub == 0 and i < 10:
            if ta == "cripto":
                try:
                    p_usd = get_crypto_price_coingecko(symbol, "usd")
                    p_rub = p_usd * usd_rate
                except:
                    pass
            elif ta == "stock_rus":
                try:
                    p_rub = get_moex_stock_price(ticker=symbol, board="TQBR")
                except:
                    p_rub = get_moex_stock_price(ticker=name,   board="TQBR")
                p_usd = p_rub / usd_rate
            elif ta in ("stock_for", "metal"):
                try:
                    p_usd = get_foreign_stock_price(symbol)
                except:
                    p_usd = get_foreign_stock_price(name)
                p_rub = p_usd * usd_rate
            elif ta == "currency":
                p_usd = 1.0
                p_rub = usd_rate
            else:
                p_usd = p_rub = 0.0
            i += 1

        total_rub = cnt * p_rub
        total_usd = cnt * p_usd
        diff_rub = total_rub - buy_rub
        diff_usd = total_usd - buy_usd

        rows.append({
            **row.to_dict(),
            "current_total_rub": total_rub,
            "current_total_usd": total_usd,
            "diff_rub": diff_rub,
            "diff_usd": diff_usd,
        })

    report_df = pd.DataFrame(rows)

    # 3) Считаем итоги по каждому type_active
    summary = (
        report_df
        .groupby("type_active", as_index=False)
        .agg({
            "total_buy_rub":    "sum",
            "total_buy_usd":    "sum",
            "current_total_rub":"sum",
            "current_total_usd":"sum",
            "diff_rub":         "sum",
            "diff_usd":         "sum",
        })
    )

    # 4) Генерируем текст отчёта
    lines = []
    for ta in summary["type_active"]:
        title, emoji = SLOV_TYPE[ta]
        lines.append(f"{emoji} *{title.upper()}*")

        block = report_df[report_df["type_active"] == ta]
        for _, r in block.iterrows():
            lines += [
                f"\n"
                f" 🔹 *{r['name_of_the_asset']}* — {r['amount_of_asset']:.4f}:",
                f"🛒 Покупка: {fmt(r['total_buy_rub'])}₽ / {fmt(r['total_buy_usd'])}$",
                f"📈 Текущая цена: {fmt(r['current_total_rub'])}₽ / {fmt(r['current_total_usd'])}$",
                f"{color_circle(r['diff_rub'], r['diff_usd'])} Разница: {fmt(r['diff_rub'])}₽ / {fmt(r['diff_usd'])}$",
            ]

        tot = summary[summary["type_active"] == ta].iloc[0]
        lines += [
            "",
            f"*Итого по {title.upper()}:*",
            f"🛒 Покупка: {fmt(tot['total_buy_rub'])}₽ / {fmt(tot['total_buy_usd'])}$",
            f"📈 Текущая цена: {fmt(tot['current_total_rub'])}₽ / {fmt(tot['current_total_usd'])}$",
            f"{color_circle(tot['diff_rub'], tot['diff_usd'])} Разница: {fmt(tot['diff_rub'])}₽ / {fmt(tot['diff_usd'])}$",
            "\n",
        ]

    # 5) Общий итог по всем активам
    all_tot = summary.agg({
        "total_buy_rub":     "sum",
        "total_buy_usd":     "sum",
        "current_total_rub": "sum",
        "current_total_usd": "sum",
        "diff_rub":          "sum",
        "diff_usd":          "sum",
    })

    lines += [
        "*ИТОГО ПО ВСЕМ АКТИВАМ*",
        f"🛒 Покупка: {fmt(all_tot['total_buy_rub'])}₽ / {fmt(all_tot['total_buy_usd'])}$",
        f"📈 Текущая цена: {fmt(all_tot['current_total_rub'])}₽ / {fmt(all_tot['current_total_usd'])}$",
        f"{color_circle(all_tot['diff_rub'], all_tot['diff_usd'])} Разница: {fmt(all_tot['diff_rub'])}₽ / {fmt(all_tot['diff_usd'])}$",
    ]

    return "\n".join(lines)