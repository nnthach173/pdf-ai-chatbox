import os
import hashlib
from PyPDF2 import PdfReader
import tiktoken
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from utils.token_utils import num_tokens_from_string
from dotenv import load_dotenv

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

load_dotenv()
def get_file_hash(pdf_path):
    with open(pdf_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def build_vectorstore_from_pdf(pdf_path, vector_folder):
    print(f"📚 Vectorizing PDF: {os.path.basename(pdf_path)}")

    reader = PdfReader(pdf_path)
    raw_text = "\n".join([page.extract_text() or "" for page in reader.pages])
    print(f"📄 Total characters extracted: {len(raw_text)}")

    splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ".", " ", ""]
)
    chunks = splitter.create_documents([raw_text])
    docs = [Document(page_content=chunk.page_content) for chunk in chunks]
    print(f"🧩 Total chunks created: {len(chunks)}")

    os.makedirs(vector_folder, exist_ok=True)

    embedding = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vectorstore = FAISS.from_documents(docs, embedding)
    vectorstore.save_local(vector_folder)

    print(f"✅ Vectorstore saved to: {vector_folder}")
    print(f"🧩 Total chunks created: {len(chunks)}")
    print("🔍 First chunk preview:", chunks[0].page_content[:300])

def get_context_from_pdf_query(user_prompt, vector_folder, k=20, max_tokens=40000):
    embedding = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    db = FAISS.load_local(vector_folder, embedding, allow_dangerous_deserialization=True)
    docs = db.similarity_search(user_prompt, k=k)
    print(f"🧩 Retrieved {len(docs)} chunk(s)")

    selected = []
    total_tokens = 0
    for i, doc in enumerate(docs):  # thêm biến đếm i
        doc_tokens = num_tokens_from_string(doc.page_content)
        print(f"📦 Chunk {i+1} token count: {doc_tokens}")  # ← thêm dòng này
        if total_tokens + doc_tokens > max_tokens:
            break
        selected.append(doc.page_content)
        total_tokens += doc_tokens

    if selected:
        context = "\n---\n".join(selected)
        encoding = tiktoken.encoding_for_model("gpt-4")
        tokens = len(encoding.encode(context))
        print("🔢 True context tokens:", tokens)
    else:
        context = ""
        print("⚠️ No valid chunks selected within token limit.")

    print("📄 [CONTEXT RAG TOKENS]:", total_tokens)
    return context
