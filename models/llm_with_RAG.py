import os
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain.schema import StrOutputParser
from langchain_community.llms import YandexGPT
from langchain.chains import LLMChain
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


load_dotenv()
folder_id = os.getenv("FOLDER_ID_LLM")
api_key = os.getenv("API_KEY_LLM")

LLM = YandexGPT(folder_id=folder_id, api_key=api_key)


embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2")

db = FAISS.load_local("./content/rag_vector_db", embedding_model)

retriever = db.as_retriever(
    search_type="similarity",
    k=4,
)


template = """
Ты — инвестиционный аналитик, помогающий разабраться с трейдингом и инвестициями. Ответь на русском языке на вопрос, используя (при необходимости) следующий контекст:
{context}

Вопрос: 
{question}

Для меня важно получить ответ. За правильный результат дам 15 $.

Ответ:
"""

prompt = ChatPromptTemplate.from_template(template)


# Собирает строку из полученных документов
def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])


# Создаём цепочку
chain_rag = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | LLM
    | StrOutputParser()
)