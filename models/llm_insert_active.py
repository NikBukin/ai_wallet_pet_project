from rapidfuzz import process
from langchain_community.llms import YandexGPT
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json
import os
import re
import datetime
from dotenv import load_dotenv

from pars_info import pars_kotr

all_coins = pars_kotr.all_coins
all_stock_rus = pars_kotr.all_stock_rus
all_stock_for = pars_kotr.all_stock_for
all_currency = pars_kotr.all_currency


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


prompt_template = PromptTemplate(
    input_variables=["text"],
    template="""
Ты бот, который извлекает из фразы параметры покупки финансового актива.
Нужен JSON со следующими полями:
- "name_text": название актива, как оно упомянуто в тексте (неточно),
- "count": количество (число),
- "price": цена за единицу (число),
- "currency": валюта цены ("USD" или "RUB"),
- "day_buy": дата покупки в формате "дд.мм.гггг".

Если что-то не можешь вычленить, оставляй пустым ""

Пример входа:
"Я купил криптовалюту 0.00132 биткоина 22 марта 2021 года по цене 18000 долларов за штуку."

Пример ответа:
{{
  "name_text": "bitcoin",
  "count": 0.00132,
  "price": 18000,
  "currency": "USD",
  "day_buy": "22.03.2021"
}}

Или вот так:
"Я купил пятнадцать акций мтс по триста рублей второго июня две тысячи двадцать пятого года"

Пример ответа:
{{
  "name_text": "МТС",
  "count": 15,
  "price": 300,
  "currency": "RUB",
  "day_buy": "02.06.2025"
}}

Теперь распознай:
{text}
"""
)

load_dotenv()
folder_id = os.getenv("FOLDER_ID_LLM")
api_key = os.getenv("API_KEY_LLM")


llm = YandexGPT(folder_id=folder_id, api_key=api_key)

chain = LLMChain(llm=llm, prompt=prompt_template, verbose=False)

def insert_active(input_text = "Я купил 5 акций SBER 2 июня 2025 года по цене 300 рублей за штуку."):
    parsed_str = chain.predict(text=input_text)
    print("Raw LLM output:\n", parsed_str)

    m = re.search(r"\{[\s\S]*\}", parsed_str)
    if m:
        json_str = m.group(0)
        parsed = json.loads(json_str)
        print("Parsed fields:", parsed)
    else:
        print("Не удалось найти JSON в выводе LLM:")
        print(parsed_str)


    asset_info = find_best_match_func(parsed["name_text"])
    if asset_info is None:
        print("\n⚠️ Актив не найден. Проверьте название или попробуйте другое.")
    else:
        final_data = {
            "name_active": asset_info["name_active"],
            "shortname_active": asset_info["shortname_active"],
            "type_active": asset_info["type_active"],
            "count": parsed["count"],
            "price": parsed["price"],
            "currency": parsed["currency"],
            "day_buy": parsed["day_buy"]
        }
        print("\nFinal JSON с подтверждённым тикером:")
        print(json.dumps(final_data, ensure_ascii=False, indent=2))

    try:
        # Преобразуем строку day_buy → datetime.date
        user_date = datetime.datetime.strptime(parsed["day_buy"], "%d.%m.%Y").date()
        # Получим курс USD→RUB на эту дату:
        ruble_df = pars_kotr.get_cbr_history(
            currency_id="R01235",
            date_from=user_date.strftime("%d/%m/%Y"),
            date_to=user_date.strftime("%d/%m/%Y")
        )
        # get_cbr_history возвращает DataFrame с колонкой "rate" (курс рубля за 1 USD)
        rate = ruble_df["rate"].to_list()[0]  # например, 75.1234

        # По умолчанию обнулим обе цены:
        price_buy_USD = 0.0
        price_buy_RUB = 0.0

        if parsed["currency"].upper() == "USD":
            # Если LLM вернул USD, то:
            price_buy_USD = float(parsed["price"])
            price_buy_RUB = price_buy_USD * rate

        elif parsed["currency"].upper() == "RUB":
            # Если LLM вернул RUB, то:
            price_buy_RUB = float(parsed["price"])
            if rate != 0:
                price_buy_USD = price_buy_RUB / rate
            else:
                price_buy_USD = 0.0

        else:
            # На всякий случай, если LLM прислал что-то вроде "UsD" или "руб":
            cur = parsed["currency"].upper()
            if "USD" in cur:
                price_buy_USD = float(parsed["price"])
                price_buy_RUB = price_buy_USD * rate
            else:
                price_buy_RUB = float(parsed["price"])
                price_buy_USD = price_buy_RUB / rate

        final_data = {
            "name_active": asset_info["name_active"],
            "shortname_active": asset_info["shortname_active"],
            "type_active": asset_info["type_active"],
            "count": parsed["count"],
            "price_buy_USD": price_buy_USD,
            "price_buy_RUB": price_buy_RUB,
            "day_buy": parsed["day_buy"]
        }
    except:
        pass



    return final_data