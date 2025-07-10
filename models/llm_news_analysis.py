from langchain_community.llms import YandexGPT
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from pars_info import pars_news
import os
from database.repository import Repository
from dotenv import load_dotenv


load_dotenv()
folder_id = os.getenv("FOLDER_ID_LLM")
api_key = os.getenv("API_KEY_LLM")

llm = YandexGPT(folder_id=folder_id, api_key=api_key)

# Универсальный шаблон
prompt_template = PromptTemplate(
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

chain_one_active = LLMChain(llm=llm, prompt=prompt_template, verbose=False)
chain_all_active = LLMChain(llm=llm, prompt=prompt_template_final, verbose=False)

def get_news_texts(name: str, type_active: str, shortname: str) -> list:
    if type_active == "stock_rus":
        return [[n["text"], n["link"]] for n in pars_news.get_finam_news([shortname]) if n["text"]]
    elif type_active in ["stock_for", "metal"]:
        return [[n["text"], n["link"]] for n in pars_news.get_yahoo_news(name) if n["text"]]
    elif type_active == "cripto":
        return [[n["text"], n["link"]] for n in pars_news.get_crypto_news(name) if n["text"]]
    else:
        return [[]]


def analyze_assets_with_news(chat_id: int, bot) -> dict:
    assets = Repository.select_by_id_telebot(chat_id)
    assets = assets[['name_active', 'shortname_active', 'type_active']].drop_duplicates().to_dict(orient='records')
    print(assets)
    processed_news = {}  # Ключ: news_text, Значение: (results, link)
    print(2)
    for asset in assets:
        name = asset["name_active"]
        short = asset["shortname_active"]
        type_act = asset["type_active"]
        try:
            news_tuple = get_news_texts(name, type_act, short)[0]
        except:
            news_tuple = None
        print(news_tuple)

        if not news_tuple:
            continue

        news_texts, link = news_tuple
        if news_texts in processed_news:
            print("⏩ Повторная новость, пропускаем LLM")
            processed_news[news_texts]["name_active"].append(name)
            processed_news[news_texts]["shorntame_active"].append(short)
            processed_news[news_texts]["link"].append(link)

        else:
            try:
                print(news_texts)
                analysis = chain_one_active.run(name_active=name, shortname_active=short, news_text=news_texts)
                results = analysis.strip()
                processed_news[news_texts] = {"llm_result": results,
                                              "name_active": [name, ],
                                              "shorntame_active": [short, ],
                                              "type_act": type_act,
                                              "link": [link, ]}
            except Exception as e:
                results = f"⚠️ Ошибка анализа: {e}"

        # bot.send_message(chat_id, results, parse_mode="Markdown", reply_markup=url_news_button(link))
    # with open("llm_news_analysis.json", "w", encoding="utf-8") as file:
    #     json.dump(processed_news, file, indent=5)
    print(processed_news)

    text_to_prompt = ""
    for an_news in processed_news.keys():
        news = processed_news[an_news]
        name_active = ' '.join(news["name_active"])
        results = ' '.join(news["llm_result"])

        text_to_prompt = text_to_prompt + f"\n\n" \
                                          f"Аналитика по активам: {name_active}:\n" \
                                          f"{results}"

    return chain_all_active.run(analysis_results = text_to_prompt).strip(), processed_news