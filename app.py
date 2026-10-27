"""
AI-Powered Document Question Answering System using RAG
---------------------------------------------------------
Pipeline: PDF Upload -> Text Extraction -> Chunking -> Embeddings
          -> FAISS Vector Store -> Semantic Retrieval -> Gemini Answer Generation

Run with:  streamlit run app.py
"""

import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
load_dotenv()  # reads GOOGLE_API_KEY from a .env file if present

st.set_page_config(page_title="RAG Document Q&A", page_icon="📄", layout="wide")
st.title("📄 AI-Powered Document Question Answering (RAG)")
st.caption("Upload PDF documents, ask questions, and get answers grounded in your documents.")

# API key handling: env var first, otherwise ask in the sidebar
api_key = os.getenv("GOOGLE_API_KEY")
with st.sidebar:
    st.header("⚙️ Configuration")
    if not api_key:
        api_key = st.text_input("Enter your Gemini API Key", type="password")
    else:
        st.success("Gemini API key loaded from environment.")

    chunk_size = st.slider("Chunk size (characters)", 300, 2000, 1000, step=100)
    chunk_overlap = st.slider("Chunk overlap (characters)", 0, 400, 150, step=50)
    top_k = st.slider("Top-K chunks to retrieve", 1, 10, 4)

if not api_key:
    st.warning("Please enter your Gemini API key in the sidebar to continue.")
    st.stop()

os.environ["GOOGLE_API_KEY"] = api_key

# Model names -- Google frequently retires specific Gemini model versions, so
# this app uses "gemini-flash-latest", an alias that always points to Google's
# current recommended fast model, instead of a hardcoded version like
# "gemini-2.5-flash" that can get shut down or restricted to existing users.
# The embedding model (gemini-embedding-001) is a stable, generally-available
# release and does not need the same treatment as of mid-2026.
EMBEDDING_MODEL = "models/gemini-embedding-001"
CHAT_MODEL = "gemini-flash-latest"

# ---------------------------------------------------------------------------
# Step 1: Upload PDFs
# ---------------------------------------------------------------------------
uploaded_files = st.file_uploader(
    "Upload one or more PDF documents", type=["pdf"], accept_multiple_files=True
)

# Cache the vector store in session state so we don't rebuild it on every rerun
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

process_clicked = st.button("🔄 Process Documents", disabled=not uploaded_files)

# ---------------------------------------------------------------------------
# Step 2-5: Extract -> Chunk -> Embed -> Store in FAISS
# ---------------------------------------------------------------------------
if process_clicked:
    with st.spinner("Extracting text and building the vector index..."):
        all_docs = []

        for uploaded_file in uploaded_files:
            # Save to a temp file because PyPDFLoader needs a file path
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name

            loader = PyPDFLoader(tmp_path)
            pages = loader.load()  # one Document per page, with metadata["page"]

            # tag each page with the source filename for later display
            for p in pages:
                p.metadata["source"] = uploaded_file.name

            all_docs.extend(pages)
            os.remove(tmp_path)

        # Step 3: Split into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = splitter.split_documents(all_docs)

        # Step 4: Generate embeddings
        embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)

        # Step 5: Store in FAISS
        vectorstore = FAISS.from_documents(chunks, embeddings)

        st.session_state.vectorstore = vectorstore

    st.success(f"Processed {len(uploaded_files)} document(s) into {len(chunks)} chunks. Ready for questions!")

# ---------------------------------------------------------------------------
# Step 6-10: Query -> Retrieve -> Generate Answer -> Display
# ---------------------------------------------------------------------------
if st.session_state.vectorstore is not None:
    st.divider()
    st.subheader("Ask a question about your documents")
    query = st.text_input("Your question:")

    if query:
        with st.spinner("Retrieving relevant chunks and generating answer..."):
            # Step 7: Semantic similarity search directly against FAISS
            retrieved_docs = st.session_state.vectorstore.similarity_search(query, k=top_k)

            # Build the context block from the retrieved chunks
            context_text = "\n\n---\n\n".join(doc.page_content for doc in retrieved_docs)

            prompt = f"""You are a helpful assistant answering questions using ONLY the context below.
If the answer isn't in the context, say you don't have enough information.

Context:
{context_text}

Question: {query}

Answer:"""

            # Step 8: Generate the answer with Gemini
            llm = ChatGoogleGenerativeAI(model=CHAT_MODEL, temperature=0.2)
            response = llm.invoke(prompt)

            # Some newer Gemini models return response.content as a list of
            # structured content blocks (e.g. reasoning + final answer)
            # instead of a single plain string. Handle both cases so the
            # actual answer text always gets displayed correctly.
            if isinstance(response.content, str):
                answer = response.content
            else:
                text_parts = []
                for block in response.content:
                    if isinstance(block, str):
                        text_parts.append(block)
                    elif isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                answer = "\n".join(p for p in text_parts if p).strip()
                if not answer:
                    answer = "(The model didn't return a text answer. Try rephrasing your question.)"

        # Step 9: Display the generated answer
        st.markdown("### ✅ Answer")
        st.write(answer)

        # Step 10: Display the retrieved chunks used to generate the answer
        st.markdown("### 📚 Retrieved Chunks (used as context)")
        for i, doc in enumerate(retrieved_docs, start=1):
            source = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page", "?")
            with st.expander(f"Chunk {i} — {source} (page {page})"):
                st.write(doc.page_content)
else:
    st.info("Upload PDF(s) and click 'Process Documents' to get started.")
