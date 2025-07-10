from pars_info import pars_kotr

all_coins = pars_kotr.all_coins
all_stock_rus = pars_kotr.all_stock_rus
all_stock_for = pars_kotr.all_stock_for
all_currency = pars_kotr.all_currency

def search_active_from_pars(type_active):
    if type_active == "cripto":
        all_cactive_name = all_coins["id"].to_list()
        combined = [f"{row.id} - {row.name}" for row in all_coins.itertuples()]
        select_active = {f"{row.id} - {row.name}": [row.id, row.name] for row in all_coins.itertuples()}
        slov = {row.id: row.name for row in all_coins.itertuples()}
    elif type_active == "stock_rus":
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

    return all_cactive_name, combined, select_active, slov