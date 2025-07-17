from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain.schema import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from pathlib import Path
import os


embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2")

# Корректное определение пути к базе данных
project_root = Path(__file__).resolve().parent.parent
rag_path = project_root / "content" / "rag_vector_db"

# Загрузка векторной базы данных
try:
    db = FAISS.load_local(str(rag_path), embedding_model, allow_dangerous_deserialization=True)
    print(f"✅ FAISS база данных успешно загружена из: {rag_path}")
except Exception as e:
    print(f"❌ Ошибка при загрузке FAISS базы данных из {rag_path}: {e}")
    print("Пожалуйста, убедитесь, что вы запустили скрипт 'create_vector_db.py' и он успешно создал базу данных.")
    db = None

retriever = None
if db:
    retriever = db.as_retriever(
        search_type="similarity",
        k=4,
    )


template = """
Ты — инвестиционный аналитик, помогающий разобраться с трейдингом и инвестициями. Ответь на русском языке на вопрос, используя (при необходимости) следующий контекст.
Контекст содержит информацию, извлеченную из различных источников, включая книги, названия которых указаны. 
**В своем ответе ОБЯЗАТЕЛЬНО указывай названия книг или источников, из которых ты взял информацию.** Например: "Согласно книге 'Разумный инвестор', ..." или "Информация взята из 'Технический анализ финансовых рынков', которая гласит, что...".

Контекст: 
{context}

Вопрос: 
{question}

Для меня важно получить ответ. За правильный результат дам 15 $.

Ответ:
"""

prompt = ChatPromptTemplate.from_template(template)


# Модифицированная функция для форматирования документов
def format_docs(docs):
    formatted_parts = []
    for i, doc in enumerate(docs):
        file_name = "Неизвестный источник"
        if 'source' in doc.metadata:
            # Извлекаем только имя файла без пути и расширения
            base_name = os.path.basename(doc.metadata['source'])
            file_name = os.path.splitext(base_name)[0] # Убираем расширение (.pdf)

        formatted_parts.append(f"Из книги '{file_name}':\n{doc.page_content}")
    return "\n\n".join(formatted_parts)


def llm_with_RAG(input_question: str, llm):
    """
    Формирует ответ на запрос пользователя с использованием релевантного контекста из заранее собранного RAG
    :param input_question: запрос пользователя
    :return:
    """
    if not retriever:
        return "Извините, база знаний для ответов на теоретические вопросы недоступна. Пожалуйста, обратитесь к администратору."

    # Цепочка Runnable
    chain_rag = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    resp = chain_rag.invoke(input_question)

    return resp