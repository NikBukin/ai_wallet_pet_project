import os
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


def extract_text_from_pdf(pdf_path):
    """
    Извлекает текст из PDF-файла.
    """
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join([page.extract_text() or "" for page in pdf.pages])


pdf_dir = "content"  # Папка с вашими PDF-файлами
rag_vector_db_path = "content/rag_vector_db"  # Папка для сохранения FAISS DB

documents = []  # Будем хранить объекты Document

print(f"Поиск PDF-файлов в: {pdf_dir}")
# Проходим по всем PDF-файлам и извлекаем текст, создавая объекты Document
for filename in os.listdir(pdf_dir):
    if filename.endswith(".pdf"):
        full_path = pdf_dir + "/" + filename  # Используем Path для правильного объединения путей
        text = extract_text_from_pdf(full_path)

        # Создаем объект Document для каждого файла
        # Метаданные будут содержать путь к исходному файлу
        doc = Document(page_content=text, metadata={"source": str(full_path)})
        documents.append(doc)
        print(f"Извлечен текст из: {filename}")

if not documents:
    print(f"⚠️ PDF-файлы не найдены в директории: {pdf_dir}. Убедитесь, что файлы присутствуют.")
    exit()  # Прерываем выполнение, если нет документов для обработки

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ".", " ", ""]
)

chunks = splitter.split_documents(documents)

print(f"Всего чанков создано: {len(chunks)}")

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
vectorstore = FAISS.from_documents(documents=chunks, embedding=embedding_model)

# Сохраняем на диск
vectorstore.save_local(str(rag_vector_db_path))

print(f"✅ Векторная база данных успешно создана и сохранена с метаданными в: {rag_vector_db_path}")