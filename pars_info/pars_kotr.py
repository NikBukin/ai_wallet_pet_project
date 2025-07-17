import requests
import datetime
import time
import xml.etree.ElementTree as ET
import pandas as pd
import yfinance as yf


## Криптовалюта

# Криптовалюта за период
def get_historical_prices(symbol_id:str, from_date:str, to_date:str)->list:
    """
    Формирует список со стоимостью криптовалюты по заданному периоду
    :param symbol_id: тикер криптовалюты (например, bitcoin)
    :param from_date: Дата начала формата %Y-%m-%d
    :param to_date: Дата окончания формата %Y-%m-%d
    """
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


# Криптовалюта в моменте
def get_crypto_price_coingecko(symbol_id:str, vs_currency:str)->float:
    """
    Выводит текущую стоимость монеты
    :param symbol_id: тикер криптовалюты (например, bitcoin)
    :param vs_currency: валюта, в которой необходимо выдать стоимость криптовалюты
    """
    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": symbol_id,
        "vs_currencies": vs_currency
    }
    r = requests.get(url, params=params)
    data = r.json()
    return data[symbol_id][vs_currency]



# Список крипты
def get_all_coins()->list:
    """
    Выводит список криптовалют с наименованием, тикером и его id
    """
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


## Российские акции

# Российские акции в периоде
def get_moex_ohlc(ticker:str, board:str, date_from:str, date_to:str)->pd.DataFrame:
    """
    Формирует список со стоимостью российской акции по заданному периоду
    :param ticker: тикер акции (например, SBER)
    :param board: Торговая площадка (например, TQBR)
    :param date_from: Дата начала формата %Y-%m-%d
    :param date_to: Дата окончания формата %Y-%m-%d
    """
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


# Российские акции в моменте
def get_moex_stock_price(ticker:str, board:str)->float:
    """
    Выводит текущую стоимость российской акции
    :param ticker: тикер акции (например, SBER)
    :param board: Торговая площадка (например, TQBR)
    """
    url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/{board}/securities/{ticker}.json"
    response = requests.get(url)
    data = response.json()
    price_index = data["marketdata"]["columns"].index("LAST")
    return data["marketdata"]["data"][0][price_index]



# Список российских акций
def get_moex_shares_list()->pd.DataFrame:
    """
    Выводит список российских акций
    """
    url = "https://iss.moex.com/iss/engines/stock/markets/shares/securities.json"
    response = requests.get(url)
    data = response.json()

    columns = data['securities']['columns']
    records = data['securities']['data']

    df = pd.DataFrame(records, columns=columns)
    df = df[["SECID", "SHORTNAME", "ISIN", "REGNUMBER", "LATNAME"]]
    return df


## Иностранные акции

# Иностранные акции в периоде
def get_foreign_stock_data(ticker:str, start:str, end:str):
    """
    Формирует список со стоимостью иностранной акции по заданному периоду
    :param ticker: тикер акции (например, AAPL)
    :param start: Дата начала формата %Y-%m-%d
    :param end: Дата окончания формата %Y-%m-%d
    """
    data = yf.download(ticker, start=start, end=end, interval="1d")
    return data[["Close"]]


# Иностранные акции в моменте
def get_foreign_stock_price(ticker:str)->float:
    """
    Выводит текущую стоимость иностранной акции
    :param ticker: тикер акции (например, AAPL)
    """
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d", interval="1m")
    if data.empty:
        return None
    return float(data["Close"].iloc[-1])


# Список иностранных акций
# S&P 500
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
all_stock_for = pd.read_html(url)[0]

## Металлы

# Металлы в периоде
def get_metal_data(ticker="GC=F"):
    data = yf.download(ticker, period="1mo", interval="1d")
    return data[["Close"]]



# Металлы в моменте
def get_metal_price(ticker="GC=F"):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d", interval="1m")
    if data.empty:
        return None
    return float(data["Close"].iloc[-1])



## Валюта

# Валюта в периоде
def get_cbr_history(currency_id:str, date_from:str, date_to:str)->pd.DataFrame:
    """
    Получает курс валюты с сайта ЦБ РФ.
    Если на указанную дату курс не найден (выходной или праздник), идёт назад по дням, пока не найдёт ближайший рабочий день.
    :param currency_id: id валюты (например, "R01235")
    :param date_from: Дата начала формата %d/%m/%Y
    :param date_to: Дата окончания формата %d/%m/%Y
    """

    def fetch_and_parse(from_date_str, to_date_str)->pd.DataFrame:
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


# Валюта в моменте
def get_cbr_currency_price(code="USD"):
    """
    Выводит текущую стоимость валюты в рублях
    :param code: код валюты (например, USD)
    """
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




# Сохранение списка активов
all_coins = pd.DataFrame(get_all_coins())
all_stock_rus = pd.DataFrame(get_moex_shares_list())
all_currency = {"USD": "R01235", "EUR": "R01239", "CNY": "R01375"}
