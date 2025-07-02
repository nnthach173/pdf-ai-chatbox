import os
import streamlit as st
import streamlit.components.v1 as components
import json

from db.db_manager import ( 
    init_database,
    save_chat_message
)
from assistant import Assistant
from utils.pdf_utils import extract_text_from_pdf
from utils.token_utils import num_tokens_from_string
from rag.rag_engine import (
    build_vectorstore_from_pdf,
    get_context_from_pdf_query,
    get_file_hash
)
from db.chat_logger import (
    init_conversation_db,
    save_pdf_session,
    load_all_pdf_sessions,
    delete_all_sessions,
)

def render_message(message, is_user):
    bg = "#1a1a1a" if is_user else "#2e2e2e"
    align = "right" if is_user else "left"
    style = f"""
        padding:12px;border-radius:10px;margin:5px 0;
        max-width:90%;word-wrap:break-word;
        background-color:{bg};color:white;
    """
    st.markdown(
        f"<div style='text-align:{align};'><div style='{style}'>{message}</div></div>",
        unsafe_allow_html=True
    )

def main():
    st.set_page_config("PDF Chat (GPT-4o)", layout="wide")
    st.title("📄 PDF Chat with GPT-4o")
    
    # ✅ Initialize MySQL-based DB
    init_database()
    init_conversation_db()

    # Session state
    if "assistant" not in st.session_state:
        st.session_state.assistant = Assistant()
    if "pdf_sessions" not in st.session_state:
        st.session_state.pdf_sessions = load_all_pdf_sessions()
    if "current_pdf" not in st.session_state:
        st.session_state.current_pdf = None

    # ==== Sidebar ====
    with st.sidebar:
        st.markdown("## 📁 Your PDFs")
        if st.session_state.pdf_sessions:
            for pdf_name in st.session_state.pdf_sessions:
                if st.button(f"📄 {pdf_name}", key=f"load_{pdf_name}"):
                    st.session_state.current_pdf = pdf_name
        else:
            st.info("No PDFs uploaded yet.")

        if st.button("🗑 Clear All Sessions"):
            delete_all_sessions()
            st.session_state.pdf_sessions.clear()
            st.session_state.current_pdf = None
            st.success("🧹 All PDF sessions cleared.")

    # ==== Upload PDF ====
    uploaded = st.file_uploader("📤 Upload PDF", type="pdf")
    if uploaded:
        pdf_name = uploaded.name
        if pdf_name not in st.session_state.pdf_sessions:
            text = extract_text_from_pdf(uploaded)
            token_count = num_tokens_from_string(text)
            use_rag = token_count > 15000

            print("📏 Token count:", token_count)

            base_prompt = ""
            vector_folder = None

            if use_rag:
                st.sidebar.warning("📚 Large PDF: Using RAG.")

                os.makedirs("storage/pdf", exist_ok=True)
                pdf_save_path = os.path.join("storage/pdf", pdf_name)

                with open(pdf_save_path, "wb") as f:
                    f.write(uploaded.getvalue())

                pdf_hash = get_file_hash(pdf_save_path)
                vector_folder = os.path.join("storage/vectors", pdf_hash)

                build_vectorstore_from_pdf(pdf_save_path, vector_folder)

                context = get_context_from_pdf_query("summary", vector_folder)

                with st.expander("🔍 RAG Retrieved Context"):
                    st.markdown(context)

                base_prompt = (
                    "You are a helpful assistant. When answering questions, always prioritize the provided context first. If the answer is not in the context, use your general knowledge to respond.\n\n"
                    "Context:\n"
                    f"{context}\n\n"
                )

                st.session_state.pdf_sessions[pdf_name] = {
                    "base_prompt": base_prompt,
                    "history": [],
                    "resp_id": None,
                    "tokens": token_count,
                    "vector_folder": vector_folder
                }
            else:
                st.sidebar.success("📚 PDF is short enough for full context.")
                base_prompt = (
                    "You are a helpful assistant. When answering questions, always prioritize the text below first. If the answer is not in the text, use your general knowledge to respond.\n\n"
                    f"{text}\n\n"
                )
                st.session_state.pdf_sessions[pdf_name] = {
                    "base_prompt": base_prompt,
                    "history": [],
                    "resp_id": None,
                    "tokens": token_count
                }

            save_pdf_session(
                pdf_name,
                base_prompt,
                None,
                [],
                token_count
            )

        st.session_state.current_pdf = pdf_name

    # ==== Chat UI ====
    current_pdf = st.session_state.current_pdf
    if current_pdf:
        session = st.session_state.pdf_sessions[current_pdf]

        for msg in session["history"]:
            render_message(msg["content"], is_user=(msg["role"] == "user"))

        user_input = st.chat_input("Ask something about this PDF…")
        if user_input:
            # === Prompt Construction ===
            if "vector_folder" in session:
                context = get_context_from_pdf_query(user_input, session["vector_folder"])
                full_prompt = (
                    "You are a helpful assistant. When answering questions, always prioritize the provided context first. If the answer is not in the context, use your general knowledge to respond.\n\n"
                    "Context:\n"
                    f"{context}\n\nUser: {user_input}"
                )
            else:
                full_prompt = session["base_prompt"] + f"User: {user_input}"

            print("🧾 Prompt token length:", num_tokens_from_string(full_prompt))

            # === Send Prompt ===
            with st.spinner("🤖 Thinking..."):
                response = st.session_state.assistant.send(full_prompt, session["resp_id"])
                session["resp_id"] = response["id"]
                ai_reply = response["text"]

                # log raw JSON to browser console
                try:
                    raw_json = json.dumps(response).replace("\\", "\\\\").replace('"', '\\"')
                    components.html(f"""
                        <script>
                            const rawResponse = JSON.parse("{raw_json}");
                            console.log("📦 [Raw OpenAI Response]:", rawResponse);
                        </script>
                    """, height=0)
                except Exception as e:
                    st.warning(f"Failed to log raw response: {e}")

            # === Update history ===
            session["history"].append({"role": "user", "content": user_input})
            session["history"].append({"role": "assistant", "content": ai_reply})
            render_message(user_input, True)
            render_message(ai_reply, False)
            save_chat_message(session_id=current_pdf, question=user_input, answer=ai_reply)

            save_pdf_session(
                pdf_name=current_pdf,
                base_prompt=session["base_prompt"],
                resp_id=session["resp_id"],
                history=session["history"],
                token_count=session["tokens"]
            )
    else:
        st.info("📎 Please upload a PDF to start chatting.")

if __name__ == "__main__":
    main()
