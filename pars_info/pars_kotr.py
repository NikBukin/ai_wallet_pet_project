import requests
import datetime
import time
import xml.etree.ElementTree as ET
import pandas as pd
import yfinance as yf


## Криптовалюта

# Криптовалюта за период
def get_historical_prices(symbol_id="bitcoin", from_date="2025-01-01", to_date="2025-05-05"):
    url = f"https://api.coingecko.com/api/v3/coins/{symbol_id}/market_chart/range"
    from_ts = int(time.mktime(datetime.datetime.strptime(from_date, "%Y-%m-%d").timetuple()))
    to_ts = int(time.mktime(datetime.datetime.strptime(to_date, "%Y-%m-%d").timetuple()) + 86400)

    params = {
        "vs_currency": "usd",
        "from": from_ts,
        "to": to_ts
    }

    response = requests.get(url, params=params)
    data = response.json()

    result = {}
    for price_point in data['prices']:
        date = datetime.datetime.utcfromtimestamp(price_point[0] / 1000).strftime('%Y-%m-%d')
        result[date] = price_point[1]

    return sorted(result.items())


# btc_history = get_historical_prices("bitcoin", from_date="2025-01-01", to_date="2025-05-05")
# for row in btc_history:
#     print(row)


# Криптовалюта в моменте
def get_crypto_price_coingecko(symbol_id="bitcoin", vs_currency="usd"):
    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": symbol_id,
        "vs_currencies": vs_currency
    }
    r = requests.get(url, params=params)
    data = r.json()
    return data[symbol_id][vs_currency]


# print(get_crypto_price_coingecko("bitcoin", "usd"))


# Список крипты
def get_all_coins():
    url = "https://api.coingecko.com/api/v3/coins/list"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    coins = []
    for coin in data:
        coins.append({
            "id": coin["id"],
            "symbol": coin["symbol"],
            "name": coin["name"]
        })

    return coins


# coins = get_all_coins()
# df = pd.DataFrame(coins)
# print(df)


## Российские акции

# Российские акции в периоде
def get_moex_ohlc(ticker="SBER", board="TQBR", date_from="2024-01-01", date_to="2024-01-31"):
    base_url = f"https://iss.moex.com/iss/history/engines/stock/markets/shares/boards/{board}/securities/{ticker}.json"
    params = {
        "from": date_from,
        "till": date_to
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if 'history' not in data or 'data' not in data['history']:
        print("Нет данных")
        return []

    columns = data['history']['columns']
    records = data['history']['data']

    df = pd.DataFrame(records, columns=columns)
    df = df[["TRADEDATE", "CLOSE"]]
    return df

#
# df = get_moex_ohlc("SBER", date_from="2024-01-01", date_to="2024-04-30")
# print(df)


# Российские акции в моменте
def get_moex_stock_price(ticker="SBER", board="TQBR"):
    url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/{board}/securities/{ticker}.json"
    response = requests.get(url)
    data = response.json()
    price_index = data["marketdata"]["columns"].index("LAST")
    return data["marketdata"]["data"][0][price_index]


# print(get_moex_stock_price(ticker="SBER", board="TQBR"))


# Список российских акций
def get_moex_shares_list():
    url = "https://iss.moex.com/iss/engines/stock/markets/shares/securities.json"
    response = requests.get(url)
    data = response.json()

    columns = data['securities']['columns']
    records = data['securities']['data']

    df = pd.DataFrame(records, columns=columns)
    df = df[["SECID", "SHORTNAME", "ISIN", "REGNUMBER", "LATNAME"]]
    # df = df.dropna(subset=["SECID"])
    return df


# df = get_moex_shares_list()
# print(df.head(10))


## Иностранные акции

# Иностранные акции в периоде
def get_foreign_stock_data(ticker="AAPL", start="2024-01-01", end="2024-04-01"):
    data = yf.download(ticker, start=start, end=end, interval="1d")
    return data[["Close"]]


# df = get_foreign_stock_data("AAPL")
# print(df)


# Иностранные акции в моменте
def get_foreign_stock_price(ticker="AAPL"):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d", interval="1m")
    if data.empty:
        return None
    return float(data["Close"].iloc[-1])


# print(get_foreign_stock_price(ticker="AAPL"))

# Список иностранных акций
# S&P 500
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
all_stock_for = pd.read_html(url)[0]
# print(all_stock_for[["Symbol", "Security"]])


## Металлы

# Металлы в периоде
def get_metal_data(ticker="GC=F"):
    data = yf.download(ticker, period="1mo", interval="1d")
    return data[["Close"]]

#
# df = get_metal_data("GC=F")
# print(df)


# Металлы в моменте
def get_metal_price(ticker="GC=F"):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d", interval="1m")
    if data.empty:
        return None
    return float(data["Close"].iloc[-1])


# print(get_foreign_stock_price(ticker="GC=F"))


## Валюта

# Валюта в периоде
def get_cbr_history(currency_id="R01235", date_from="01/01/2025", date_to="01/05/2025"):
    """
    Получает курс валюты с сайта ЦБ РФ.
    Если на указанную дату курс не найден (выходной или праздник), идёт назад по дням, пока не найдёт ближайший рабочий день.
    """

    def fetch_and_parse(from_date_str, to_date_str):
        url = (
            "https://www.cbr.ru/scripts/XML_dynamic.asp"
            f"?date_req1={from_date_str}&date_req2={to_date_str}&VAL_NM_RQ={currency_id}"
        )
        resp = requests.get(url)
        tree = ET.fromstring(resp.content)

        records = []
        for record in tree.findall("Record"):
            date = datetime.datetime.strptime(record.attrib["Date"], "%d.%m.%Y").date()
            nominal = int(record.find("Nominal").text)
            value = float(record.find("Value").text.replace(",", "."))
            records.append({"date": date, "rate": value / nominal})
        return pd.DataFrame(records)

    # Одиночная дата
    if date_from == date_to:
        target_date = datetime.datetime.strptime(date_from, "%d/%m/%Y").date()

        # Идём назад по дням, пока не найдём курс
        while True:
            date_str = target_date.strftime("%d/%m/%Y")
            df = fetch_and_parse(date_str, date_str)
            if not df.empty:
                return df
            target_date -= datetime.timedelta(days=1)
            if target_date.year < 1995:  # Ограничим поиск, чтобы не уйти в бесконечность
                return None

    # Диапазон — возвращаем как есть
    df = fetch_and_parse(date_from, date_to)
    return df.sort_values("date")


# df = get_cbr_history("R01235", "01/01/2025", "30/04/2025")
# print(df)


# Валюта в моменте
def get_cbr_currency_price(code="USD"):
    today = datetime.datetime.today().strftime('%d/%m/%Y')
    url = f"https://www.cbr.ru/scripts/XML_daily.asp?date_req={today}"
    response = requests.get(url)
    tree = ET.fromstring(response.content)

    for valute in tree.findall("Valute"):
        if valute.find("CharCode").text == code.upper():
            nominal = int(valute.find("Nominal").text)
            value = float(valute.find("Value").text.replace(",", "."))
            return round(value / nominal, 4)
    return None


# # Пример
# print("USD/RUB:", get_cbr_currency_price("USD"))


# Сохранение списка активов
all_coins = pd.DataFrame(get_all_coins())
all_stock_rus = pd.DataFrame(get_moex_shares_list())
all_currency = {"USD": "R01235", "EUR": "R01239", "CNY": "R01375"}
