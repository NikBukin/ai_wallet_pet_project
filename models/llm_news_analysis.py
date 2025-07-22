from langchain_community.llms import YandexGPT
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from pars_info import pars_news, search_active
from database.repository import Repository
from dotenv import load_dotenv
import os

# LLM и переменные окружения
load_dotenv()
folder_id = os.getenv("FOLDER_ID_LLM")
api_key = os.getenv("API_KEY_LLM")
llm = YandexGPT(folder_id=folder_id, api_key=api_key)


# Получение новостей
def get_news_texts(name: str, type_active: str, shortname: str) -> list:
    """
    Получение списка новостей и ссылок по конкретному активу
    :param name: Название актива
    :param type_active: Тип актива
    :param shortname: Второе название актива (тикер)
    :return:
    """
    if type_active == "stock_rus":
        try:
            news = pars_news.get_finam_news([name])
        except:
            news = pars_news.get_finam_news([shortname])
        return [[n["text"], n["link"]] for n in news if n["text"]]
    elif type_active in ["stock_for", "metal"]:
        try:
            news = pars_news.get_yahoo_news([name])
        except:
            news = pars_news.get_yahoo_news([shortname])
        return [[n["text"], n["link"]] for n in news if n["text"]]
    elif type_active == "cripto":
        try:
            news = pars_news.get_crypto_news([name])
        except:
            news = pars_news.get_crypto_news([shortname])
        return [[n["text"], n["link"]] for n in news if n["text"]]
    else:
        return [[]]


def llm_find_active(input_text:str, llm)->dict:
    """
    Вычленение корректного названия актива по неточному наименованиб из запроса пользования с использованием функции find_best_match_func
    """
    prompt = PromptTemplate(
        input_variables=["text"],
        template="""
Извлеки название актива из текста. Выведи ТОЛЬКО название актива. Если актив не найден, выведи пустую строку.

---
Примеры:
Текст: "Какие были новости по акциями сбербанка?"
Актив: Сбербанк

Текст: "Что с биткоином?"
Актив: bitcoin

Текст: "Что слышно про Apple."
Актив: Apple

Текст: "Новости по золоту."
Актив: золото
---

Текст: "{text}"
Актив:
"""
    )
    chain = LLMChain(llm=llm, prompt=prompt, verbose=False)
    response_dict = chain.invoke({"text": input_text}, stop=["\n"])
    if isinstance(response_dict, dict) and 'text' in response_dict:
        active_name = response_dict['text'].strip()
    elif isinstance(response_dict, str):
        active_name = response_dict.strip()
    else:
        active_name = ""

    lines = active_name.split('\n')
    cleaned_active_name = ""
    for line in lines:
        if line.strip() and not line.strip().startswith(("Текст:", "Актив:", "Вопрос", "Ответ")):
            cleaned_active_name = line.strip()
            break
    result = search_active.find_best_match_func(cleaned_active_name)
    return result



# Анализ по одному активу
def llm_news_analysis(name_active: str, shortname_active: str, type_active: str, llm):
    """
    Дает оценку активу с кратким аналитическим выводом на основании новостей
    :param name_active: Название актива
    :param type_active: Тип актива
    :param shortname_active: Второе название актива (тикер)
    :return:
    """
    prompt = PromptTemplate(
        input_variables=["name_active", "shortname_active", "news_text"],
        template="""
    Ты — инвестиционный аналитик. На основе представленных новостей, сформируй краткий аналитический вывод для актива {name_active} - {shortname_active}, которая находится у клиента в кошельке".
    Укажи обязательно на русском языке, в 3-4 предложениях:
    - Общий тон (позитивный/негативный/нейтральный).
    - Краткую информацию
    - Дай рекомендацию для покупки, продажи или удержания на основе полученного текста.
    
    Вот свежие новости:
    {news_text}

    Ответ:
    """
    )
    chain = LLMChain(llm=llm, prompt=prompt, verbose=False)

    try:
        news = get_news_texts(name_active, type_active, shortname_active)
        if not news or not news[0] or not news[0][0]:
            return None, None  # Возвращаем (None, None)

        news_text, link = news[0]  # Получаем текст и ссылку

        # LLM генерирует ответ БЕЗ ссылки
        result = chain.run(
            name_active=name_active,
            shortname_active=shortname_active,
            news_text=news_text
        ).strip()

        return result, link  # Возвращаем (текст_LLM, ссылка)
    except Exception as e:
        print(f"Ошибка при анализе новостей для {name_active}: {e}")
        return f"⚠️ Ошибка анализа: {e}", None


# Итоговый вывод по всем активам
def analyze_assets_with_news(chat_id: int) -> tuple[str, dict]:
    """
    Формирование отчетов по каждой найденной новости и генерация общего отчета на основании последних новостей, которые находятся у пользователя в кошельке
    :param chat_id: chat_id пользователя для получения списка актива из базы данных
    :return:
    """
    assets = Repository.select_by_id_telebot(chat_id)
    assets = assets[['name_of_the_asset', 'second_name_of_the_asset', 'type_active']].drop_duplicates().to_dict(orient='records')

    all_analysis = {}
    news_summary = ""

    for asset in assets:
        name = asset["name_of_the_asset"]
        short = asset["second_name_of_the_asset"]
        type_act = asset["type_active"]

        analysis, link = llm_news_analysis(name, short, type_act, llm)
        if not analysis:
            continue

        news_summary += f"\n\nАналитика по активу *{name}*:\n{analysis}"
        all_analysis[name] = {
            "llm_result": analysis,
            "shortname_active": short,
            "type_active": type_act,
            "link": link
        }

    # 🧠 Финальный обобщённый анализ
    prompt_template_final = PromptTemplate(
        input_variables=["analysis_results"],
        template="""
Ты — инвестиционный аналитик. На основе представленных новостей, сформируй подробный аналитический вывод основываясь на:".
Укажи обязательно на русском языке с использованием эмодзи:
- Общий тон всех новостей в общем (позитивный/негативный/нейтральный). Отдельно выдели активы с крайне негативным тоном при необходимости.
- Краткую важную информацию информацию
- Дай общие рекомендации.

Вот выжимки из новостей:
{analysis_results}

Ответ:
"""
    )
    final_chain = LLMChain(llm=llm, prompt=prompt_template_final, verbose=False)
    final_summary = final_chain.run(analysis_results=news_summary).strip()

    return final_summary, all_analysis