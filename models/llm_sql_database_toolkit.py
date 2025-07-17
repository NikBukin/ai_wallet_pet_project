from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit

# подключимся к базе
db = SQLDatabase.from_uri("sqlite:///database/db_active.db")


# Создаём кастомный prompt
prompt = """
Ты — финансовый помощник. У тебя есть база активов пользователей с таблицей `assets`, где 
id - уникальный ключ записи в таблице
user_id - id пользователя, который загрузил информацию
information_upload_date - дата загрузки информации
user_name - имя пользователя
type_active - тип актива (stock_rus - российские ценные бумаги, stock_for - иностранные ценные бумаги, currency - валюта, cripto - криптовалюта, metal - драгоценные металлы)
name_of_the_asset - название актива
second_name_of_the_asset - другое название актива
amount_of_asset - количество актива
asset_purchase_date - дата покупки актива
purchase_price_of_one_asset_in_dollars - цена покупки одной единицы актива в долларах
purchase_price_of_one_asset_in_rubles - цена покупки одной единицы актива в рублях

Даты записаны  в формате YYYY-MM-DD.\n\n
    
Ты должен использовать SQL-инструменты и таблицу `assets` для ответа.

Вопрос:

"""


def llm_sql_database_toolkit(input_text: str, user_id: int, LLM)->str:
    """
    Формирует необходимый sql запрос с фильтрацией по user_id и обращается к базе данных в соответствии с запросом пользователя
    :param input_text: Входной запрос пользователя
    :param user_id: user_id пользователя
    :return:
    """
    toolkit = SQLDatabaseToolkit(db=db, llm=LLM)
    agent_executor = create_sql_agent(LLM,
                             toolkit=toolkit,
                             verbose=True)

    resp = agent_executor.invoke({"input": f"{prompt} {input_text}\n"
                                           f"Информацию необходимо предоставлять строго по пользователю с user_id {user_id}?"})

    return resp