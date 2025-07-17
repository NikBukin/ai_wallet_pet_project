from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import StructuredOutputParser, ResponseSchema # Добавляем импорты
import json
import datetime

from pars_info import pars_kotr, search_active


# Формирование структуры для вывода в json-формате
response_schemas = [
    ResponseSchema(name="name_text", description="название актива, как оно упомянуто в тексте"),
    ResponseSchema(name="count", description="количество (число)"),
    ResponseSchema(name="price", description="цена за единицу (число)"),
    ResponseSchema(name="currency", description="валюта цены ('USD' или 'RUB')"),
    ResponseSchema(name="day_buy", description="дата покупки в формате 'дд.мм.гггг'")
]
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
format_instructions = output_parser.get_format_instructions()

# prompt_template с использованием format_instructions
prompt_template = PromptTemplate(
    input_variables=["text"],
    partial_variables={"format_instructions": format_instructions},
    template="""
Ты бот, который извлекает из фразы параметры покупки финансового актива.
{format_instructions}

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


def llm_insert_active(input_text: str, llm) -> dict:
    """
    Создание json структуры из запроса пользователя
    :param input_text: входное сообщение пользователя
    :param llm: llm модель
    :return:
    """
    chain = LLMChain(llm=llm, prompt=prompt_template, verbose=False)
    parsed_str = chain.predict(text=input_text)

    # Парсинг json из результата llm
    try:
        parsed = output_parser.parse(parsed_str)
        print("Parsed fields:", parsed)
    except Exception as e:
        print(f"Ошибка при парсинге JSON: {e}")
        print("Сырой вывод LLM:\n", parsed_str)
        return None

    # Поиск тикера по неточному соответствию
    asset_info = search_active.find_best_match_func(parsed["name_text"])

    if asset_info is None:
        print("\n⚠️ Актив не найден. Проверьте название или попробуйте другое.")
        return None

    final_data = {
        "name_active": asset_info["name_active"],
        "shortname_active": asset_info["shortname_active"],
        "type_active": asset_info["type_active"],
        "count": float(parsed["count"]) if parsed["count"] else 0.0,
        "price": float(parsed["price"]) if parsed["price"] else 0.0,
        "currency": parsed["currency"].upper() if parsed["currency"] else "",
        "day_buy": parsed["day_buy"] if parsed["day_buy"] else ""
    }

    # Инициализируем price_buy_USD и price_buy_RUB
    final_data["price_buy_USD"] = 0.0
    final_data["price_buy_RUB"] = 0.0

    # Обработка даты, курса валют и получения информации о стоимости актива в рублях\долларах
    if final_data["day_buy"] and final_data["currency"] and final_data["price"] > 0:
        try:
            user_date = datetime.datetime.strptime(final_data["day_buy"], "%d.%m.%Y").date()
            ruble_df = pars_kotr.get_cbr_history(
                currency_id="R01235",
                date_from=user_date.strftime("%d/%m/%Y"),
                date_to=user_date.strftime("%d/%m/%Y")
            )

            rate = 0.0
            if not ruble_df.empty and "rate" in ruble_df.columns:
                rate = ruble_df["rate"].to_list()[0]
            else:
                print(f"Не удалось получить курс валюты на дату {final_data['day_buy']}.")


            if final_data["currency"].upper() == "USD":
                final_data["price_buy_USD"] = final_data["price"]
                final_data["price_buy_RUB"] = final_data["price_buy_USD"] * rate
            elif final_data["currency"].upper() == "RUB":
                final_data["price_buy_RUB"] = final_data["price"]
                if rate != 0:
                    final_data["price_buy_USD"] = final_data["price_buy_RUB"] / rate
                else:
                    final_data["price_buy_USD"] = 0.0
            else:
                print(f"Неизвестная валюта при расчете: {final_data['currency']}. Использую как USD.")
                final_data["price_buy_USD"] = final_data["price"]
                final_data["price_buy_RUB"] = final_data["price_buy_USD"] * rate

        except ValueError as ve:
            print(f"Ошибка формата даты: {ve}. Пожалуйста, убедитесь, что дата в формате дд.мм.гггг.")
        except IndexError:
            print("Не удалось извлечь курс валюты из DataFrame.")
        except Exception as e:
            print(f"Произошла ошибка при расчете цен в разных валютах: {e}")

    print("\nFinal JSON с подтверждённым тикером:")
    print(json.dumps(final_data, indent=2, ensure_ascii=False))

    return final_data