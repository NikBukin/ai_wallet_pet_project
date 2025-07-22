from langchain_community.llms import YandexGPT
from langchain.agents import initialize_agent
from langchain.agents.agent_types import AgentType
from langchain_core.tools import tool
from langchain_core.callbacks import BaseCallbackHandler
from langchain.callbacks.manager import CallbackManager
from dotenv import load_dotenv
import os
import json
from models.llm_insert_active import llm_insert_active
from models.llm_news_analysis import llm_news_analysis, llm_find_active
from models.llm_sql_database_toolkit import llm_sql_database_toolkit
from models.llm_with_RAG import  llm_with_RAG

load_dotenv()
folder_id = os.getenv("FOLDER_ID_LLM")
api_key = os.getenv("API_KEY_LLM")
llm = YandexGPT(folder_id=folder_id, api_key=api_key)


class ToolUsageCallbackHandler(BaseCallbackHandler):
    """
    Кастомный колбэк хендлер для отслеживания используемых инструментов.
    """

    def __init__(self):
        self.used_tool_name = None

    def on_tool_start(self, serialized: dict, input_str: str, **kwargs) -> None:
        print(f"🛠 on_tool_start: Tool: {serialized.get('name')}, Input: {input_str}")
        pass

    def on_tool_end(self, output: str, **kwargs) -> None:
        print("🛠 on_tool_end captured output (still debugging):", output)
        pass

    def on_agent_action(self, action: dict, **kwargs) -> None:
        """Вызывается, когда агент выбирает действие (инструмент)."""
        print(f"🕵️‍♀️ on_agent_action: Tool selected: {action.tool}, Tool Input: {action.tool_input}")
        self.used_tool_name = action.tool
        pass

    def on_agent_finish(self, finish: dict, **kwargs) -> None:
        print(f"🏁 on_agent_finish: Agent finished. Output: {finish.return_values.get('output', 'N/A')}")
        pass


@tool
def add_asset_tool(text: str) -> str:
    """
    Используется ТОЛЬКО для извлечения информации о покупке нового актива из пользовательского сообщения.
    Ожидает фразы типа: "Я купил криптовалюту 0.00132 биткоина 22 марта 2021 года по цене 18000 долларов за штуку", "добавь 3 акции Apple", "20 мая приобрел доллар по 89 рублей".
    Возвращает JSON с названием, тикером, количеством, ценой и датой.
    """
    print("Добавление актива в БД")
    asset_data = llm_insert_active(text, llm)

    result_summary = "Не удалось обработать информацию о покупке актива."
    if isinstance(asset_data, dict):
        name = asset_data.get('name_active', 'актива')
        count = asset_data.get('count')
        price = asset_data.get('price')
        currency = asset_data.get('currency', '')
        shortname = asset_data.get('shortname_active', 'N/A')

        parts = []
        if count is not None:
            parts.append(f"{count} акций")
        if name:
            parts.append(name)
        if price is not None and currency:
            parts.append(f"по цене {price} {currency}")
        elif price is not None:
            parts.append(f"по цене {price}")

        if parts:
            result_summary = f"Информация о покупке {' '.join(parts)} добавлена. Тикер: {shortname}."
        else:
            result_summary = "Информация о покупке актива получена, но не удалось сформировать полное резюме."

    return json.dumps({
        "tool_name": "add_asset_tool",
        "result_text": result_summary,
        "data": asset_data
    }, ensure_ascii=False)


@tool
def analyze_news_tool(text: str) -> str:
    """
    Используется ТОЛЬКО для поиска новостей по активам.
    Ожидает фразы типа: "Что происходит с биткоином?", "Какие новости по AMD?", "Что по новостям у сбербанка?".
    Возвращает JSON-строгую с аналитическим выводом и ссылкой на источник. Может выдавать отсутствие аналитики с случае отсутствия новостей за последние.
    """
    asset = llm_find_active(text, llm)
    if not asset or not asset.get("name_active"):
        return json.dumps({
            "tool_name": "analyze_news_tool",
            "result_text": "Не удалось найти актив по вашему запросу для анализа новостей.",
            "link": None
        }, ensure_ascii=False)

    name_active = asset["name_active"]
    shortname_active = asset["shortname_active"]
    type_active = asset["type_active"]
    print(f"Анализ новостей для: {name_active}")

    result_text, link = llm_news_analysis(name_active, shortname_active, type_active, llm)

    if not result_text:
        return json.dumps({
            "tool_name": "analyze_news_tool",
            "result_text": "Не удалось получить аналитику по новостям.",
            "link": None
        }, ensure_ascii=False)

    return json.dumps({
        "tool_name": "analyze_news_tool",
        "result_text": result_text,
        "link": link
    }, ensure_ascii=False)


def create_sql_query_tool(user_id: int):
    @tool
    def sql_query_tool(text: str) -> str:
        """
        Используется ТОЛЬКО для поиска информации по активам пользователя из его кошелька (формирование запроса в базу данных).
        Ожидает фразы типа: "Какие активы я купил в мае 2025?", "Сколько всего я инвестировал в рублях?", "Когда последний раз я покупал криптовалюту?"
        Возвращает JSON-строку с результатами запроса.
        """
        print(f"Получение информации из БД для пользователя {user_id}")
        response_data = llm_sql_database_toolkit(text, user_id, llm)
        return json.dumps({
            "tool_name": "sql_query_tool",
            "result_text": str(response_data)
        }, ensure_ascii=False)

    return sql_query_tool


@tool
def rag_tool(text: str) -> str:
    """
    Отвечает на ТЕОРЕТИЧЕСКИЕ или ОБЩИЕ ВОПРОСЫ о финансах, терминах и стратегиях.
    Использует метод RAG для генерации ответа на основе базы знаний.
    Не подходит для вопросов про конкретные покупки/продажи или новости по активам пользователя.
    Ожидает фразы типа: "Как оценить риски при долгосрочных инвестициях?", "Что такое хэджирование на свопах?", "Почему долгосрочные инвестиции безопаснее краткосрочных?"
    Возвращает JSON-строку с ответом и списком источников.
    """
    print("Информация из RAG")
    result_text = llm_with_RAG(text, llm)

    if not result_text:
        return json.dumps({
            "tool_name": "rag_tool",
            "result_text": "Не удалось получить информацию из базы знаний."
        }, ensure_ascii=False)

    return json.dumps({
        "tool_name": "rag_tool",
        "result_text": result_text
    }, ensure_ascii=False)


def llm_router(text: str, user_id: int)->dict:
    current_sql_query_tool = create_sql_query_tool(user_id)

    # Для получения used_tool_name из on_agent_action
    callback_handler = ToolUsageCallbackHandler()
    cb_manager = CallbackManager([callback_handler])

    agent = initialize_agent(
        tools=[add_asset_tool, analyze_news_tool, current_sql_query_tool, rag_tool],
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        callbacks=cb_manager,
        return_intermediate_steps=True
    )

    result_agent = agent.invoke({"input": text})

    used_tool = callback_handler.used_tool_name

    final_output_text = result_agent.get('output', "Не удалось получить ответ.")
    tool_data = {}

    # Извлекаем последний Observation из intermediate_steps
    intermediate_steps = result_agent.get('intermediate_steps', [])
    last_observation_str = None
    if intermediate_steps:
        _, last_observation_str = intermediate_steps[-1]

    if last_observation_str:
        try:
            tool_data = json.loads(last_observation_str)
        except json.JSONDecodeError:
            print(f"Ошибка при парсинге JSON из последнего Observation: {last_observation_str}")
            tool_data = {"error": "Failed to parse tool output as JSON from intermediate steps"}
        except Exception as e:
            print(f"Неизвестная ошибка при обработке данных из intermediate steps: {e}")
            tool_data = {"error": f"An unexpected error occurred: {e}"}

    print(f"\n✅ Ответ получен с помощью инструмента: {used_tool}")
    return {
        "output": final_output_text,
        "used_tool": used_tool,
        "tool_data": tool_data
    }