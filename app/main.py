# IMPORT
import os
# from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain.prompts import ChatPromptTemplate
import streamlit as st


# KEYKEYKEY
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# CONNECT TO Qdrant Cloud
cloud_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)


# MODEL EMBEDDING Hugging Face
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={"device": "cpu"},   # или "cuda", если GPU есть
    encode_kwargs={"normalize_embeddings": True}
)


# QDRANT DATA CONNECT 
qdrant_client = QdrantVectorStore(
    client=cloud_client,
    collection_name="demo_collection",
    embedding=embeddings
)


# CONNECT TO LLM (Groq)
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile"
)

# Проверим, что коллекция доступна
print("📁 Коллекции в облаке:")
print(cloud_client.get_collections())

# ==============================
# 🧠 6. Промпт для подбора сериалов
# ==============================
rag_prompt = ChatPromptTemplate.from_messages([
    ("system", """🎬 Ты профессиональный кинокритик и эксперт по сериалам.
Твоя задача — проанализировать найденные сериалы и подобрать те, которые лучше всего подходят под запрос пользователя.

Формат ответа:
- 💡 Кратко объясни, почему именно эти сериалы подходят.
- 🎯 Укажи жанр, стиль и особенности каждого сериала.
- 😄 Добавь немного иронии или мемов о сериалах, если это уместно.
- 🧠 Структурируй вывод: каждый сериал — отдельным блоком.
- 📍 Отвечай на русском языке живым, но экспертным тоном.
"""),
    ("human", """📺 Найденные сериалы:
{context}

🎯 Запрос пользователя: {question}""")
])

# ==============================
# 🔍 7. Форматирование документов (для промпта)
# ==============================
def format_docs_for_prompt(docs):
    formatted = []
    for d in docs:
        meta = d.metadata
        title = meta.get("title", "Не указано")
        url = meta.get("page_url", "N/A")
        desc = d.page_content[:300].replace("\n", " ")
        formatted.append(f"📺 {title}\n🔗 {url}\n📄 {desc}...")
    return "\n\n".join(formatted)

# ==============================
# 📺 8. Отображение сериалов на странице
# ==============================
def show_results(docs):
    for i, d in enumerate(docs, 1):
        meta = d.metadata
        title = meta.get("title", "")
        url = meta.get("page_url", "#")
        img = meta.get("image_url", "")
        desc = d.page_content[:500] + "..."

        st.subheader(f"🎬 Сериал {i}: {title}")
        if img:
            st.image(img, width=300)
        st.markdown(f"[🔗 Смотреть сериал]({url})")
        st.write(desc)

# ==============================
# 🔎 9. Создание RAG цепочки
# ==============================
retriever = qdrant_client.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5}
)

rag_chain = (
    {
        "context": retriever | format_docs_for_prompt,
        "question": RunnablePassthrough()
    }
    | rag_prompt
    | llm
    | StrOutputParser()
)

# ==============================
# 🎨 10. Streamlit UI
# ==============================
st.set_page_config(page_title="Find My Show 🎥", page_icon="🍿", layout="centered")

st.title("🍿 Find My Show — умный подбор сериалов")
st.write("🔎 Опиши, что ты хочешь посмотреть — и я найду сериалы, которые подойдут именно тебе.")

query = st.text_area("💭 Что ты хочешь посмотреть?", placeholder="Например: Хочу комедийный сериал про расследования и дружбу")

if st.button("🔍 Найти сериалы"):
    if query.strip():
        with st.spinner("🔎 Ищу лучшие варианты..."):
            docs = retriever.invoke(query)  # получаем документы
            show_results(docs)              # показываем карточки
            answer = rag_chain.invoke(query) # анализ от LLM
        st.subheader("📺 Анализ и рекомендации:")
        st.markdown(answer)
    else:
        st.warning("✏️ Сначала введи запрос.")