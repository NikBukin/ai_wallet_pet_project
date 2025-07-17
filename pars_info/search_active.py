from pars_info import pars_kotr
from rapidfuzz import process


all_coins = pars_kotr.all_coins
all_stock_rus = pars_kotr.all_stock_rus
all_stock_for = pars_kotr.all_stock_for
all_currency = pars_kotr.all_currency

def search_active_from_pars(type_active):
    if type_active == "stock_rus":
        all_cactive_name = all_stock_rus["SECID"].to_list()
        combined = [f"{row.SECID} - {row.SHORTNAME}" for row in all_stock_rus.itertuples()]
        select_active = {f"{row.SECID} - {row.SHORTNAME}" : [row.SECID, row.SHORTNAME] for row in all_stock_rus.itertuples()}
        slov = {row.SECID: row.SHORTNAME for row in all_stock_rus.itertuples()}
    elif type_active == "stock_for" or type_active == "metal":
        all_cactive_name = all_stock_for["Symbol"].to_list()
        combined = [f"{row.Symbol} - {row.Security}" for row in all_stock_for.itertuples()]
        select_active = {f"{row.Symbol} - {row.Security}": [row.Symbol, row.Security] for row in all_stock_for.itertuples()}
        slov = {row.Symbol: row.Security for row in all_stock_for.itertuples()}
    elif type_active == "currency":
        all_cactive_name = all_currency.keys()
        combined = [f"{list(all_currency.keys())[row]} - {all_currency[list(all_currency.keys())[row]]}" for row in range(len(all_cactive_name))]
        select_active = {f"{list(all_currency.keys())[row]} - {all_currency[list(all_currency.keys())[row]]}":
            [list(all_currency.keys())[row], all_currency[list(all_currency.keys())[row]]] for row in
                              range(len(all_cactive_name))}
        slov = all_currency
    elif type_active == "cripto":
        all_cactive_name = all_coins["id"].to_list()
        combined = [f"{row.id} - {row.name}" for row in all_coins.itertuples()]
        select_active = {f"{row.id} - {row.name}": [row.id, row.name] for row in all_coins.itertuples()}
        slov = {row.id: row.name for row in all_coins.itertuples()}

    return all_cactive_name, combined, select_active, slov


def find_best_match_func(name: str) -> dict:
    """
    Ищет лучший актив по неточному названию из всех категорий.
    Возвращает словарь: {"type_active": ..., "shortname_active": ..., "name_active": ...}
    """
    candidates = []
    # Российские акции
    for row in all_stock_rus.itertuples():
        candidates.append((f"{row.SECID} - {row.SHORTNAME}", "stock_rus", row.SECID, row.SHORTNAME))
    # Иностранные акции / металлы
    for row in all_stock_for.itertuples():
        candidates.append((f"{row.Symbol} - {row.Security}", "stock_for", row.Symbol, row.Security))
    # Валюты
    for k, v in all_currency.items():
        candidates.append((f"{k} - {v}", "currency", k, k))
    # Криптовалюты
    for row in all_coins.itertuples():
        candidates.append((f"{row.id} - {row.name}", "cripto", row.id, row.name))

    search_list = [c[0] for c in candidates]
    matches = process.extract(name, search_list, limit=1, score_cutoff=50)

    if not matches:
        return None

    best = matches[0][0]
    for c in candidates:
        if c[0] == best:
            return {"type_active": c[1], "shortname_active": c[2], "name_active": c[3]}
    return None