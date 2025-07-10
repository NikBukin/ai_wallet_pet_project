import os
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join([page.extract_text() or "" for page in pdf.pages])

pdf_dir = "content"
texts = []

for filename in os.listdir(pdf_dir):
    if filename.endswith(".pdf"):
        full_path = os.path.join(pdf_dir, filename)
        texts.append(extract_text_from_pdf(full_path))


splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ".", " ", ""]
)

chunks = []
for text in texts:
    chunks += splitter.split_text(text)

print(f"Всего чанков: {len(chunks)}")

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
vectorstore = FAISS.from_texts(texts=chunks, embedding=embedding_model)

# Сохраняем на диск
vectorstore.save_local("content/rag_vector_db")

query = "Какие сигналы даёт индикатор RSI?"
docs = vectorstore.similarity_search(query, k=4)
retrieved_context = "\n\n".join([doc.page_content for doc in docs])