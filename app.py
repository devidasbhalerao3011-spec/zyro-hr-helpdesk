
import streamlit as st
import sqlite3
import json
import uuid
import os
from datetime import datetime
from pathlib import Path

from config import get_settings
from src.rag_chain import build_rag_pipeline, answer_question
from src.document_loader import load_policy_documents
from src.text_splitter import split_documents
from src.vector_store import get_vector_store
from src.retriever import get_retriever


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Zyro Dynamics | HR Assistant",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# DATABASE: PERSISTENT CHAT HISTORY AND FEEDBACK
# =========================================================

DB_PATH = Path(__file__).parent / "chat_history.db"


def get_db():
    return sqlite3.connect(DB_PATH)


def initialize_database():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                sources TEXT,
                feedback TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(chat_id) REFERENCES chats(id)
            )
        """)


def create_chat():
    chat_id = str(uuid.uuid4())

    with get_db() as conn:
        conn.execute(
            "INSERT INTO chats (id, title, created_at) VALUES (?, ?, ?)",
            (
                chat_id,
                "New conversation",
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

    return chat_id


def get_all_chats():
    with get_db() as conn:
        return conn.execute(
            "SELECT id, title FROM chats ORDER BY created_at DESC"
        ).fetchall()


def get_chat_messages(chat_id):
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, role, content, sources, feedback
            FROM messages
            WHERE chat_id = ?
            ORDER BY created_at ASC
            """,
            (chat_id,),
        ).fetchall()

    messages = []

    for row in rows:
        messages.append({
            "id": row[0],
            "role": row[1],
            "content": row[2],
            "sources": json.loads(row[3] or "[]"),
            "feedback": row[4],
        })

    return messages


def save_message(chat_id, role, content, sources=None):
    message_id = str(uuid.uuid4())

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO messages
            (id, chat_id, role, content, sources, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                chat_id,
                role,
                content,
                json.dumps(sources or []),
                datetime.now().isoformat(timespec="microseconds"),
            ),
        )

    return message_id


def update_chat_title(chat_id, question):
    title = question.strip().replace("\n", " ")

    if len(title) > 42:
        title = title[:39] + "..."

    with get_db() as conn:
        conn.execute(
            "UPDATE chats SET title = ? WHERE id = ?",
            (title or "New conversation", chat_id),
        )


def save_feedback(message_id, feedback):
    with get_db() as conn:
        conn.execute(
            "UPDATE messages SET feedback = ? WHERE id = ?",
            (feedback, message_id),
        )


def clear_chat_messages(chat_id):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM messages WHERE chat_id = ?",
            (chat_id,),
        )
        conn.execute(
            "UPDATE chats SET title = ? WHERE id = ?",
            ("New conversation", chat_id),
        )


initialize_database()


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #F5F7FC;
    color: #172B4D;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1100px;
}

/* Sidebar */

section[data-testid="stSidebar"] {
    background: #12213D;
}

section[data-testid="stSidebar"] * {
    color: #FFFFFF;
}

section[data-testid="stSidebar"] .stButton button {
    background: #1D3153;
    border: 1px solid #344B70;
    color: white;
    border-radius: 10px;
    text-align: left;
}

section[data-testid="stSidebar"] .stButton button:hover {
    background: #29456F;
    border-color: #6E9BE5;
}

/* Logo */

.zyro-logo {
    display: flex;
    align-items: center;
    gap: 13px;
    padding: 12px 0 22px 0;
}

.zyro-mark {
    width: 48px;
    height: 48px;
    border-radius: 15px;
    background: linear-gradient(135deg, #4F8DF7, #2455C7);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-family: 'Manrope', sans-serif;
    font-size: 26px;
    font-weight: 800;
    box-shadow: 0 5px 15px rgba(35, 90, 190, 0.25);
}

.zyro-name {
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    font-size: 17px;
    letter-spacing: 1px;
    color: #172B4D;
}

.zyro-subtitle {
    color: #7890B2;
    font-size: 10px;
    letter-spacing: 2px;
    font-weight: 600;
}

/* Welcome banner */

.hero {
    background: linear-gradient(115deg, #172F57, #2757A5);
    padding: 34px;
    border-radius: 22px;
    color: white;
    margin-bottom: 25px;
    box-shadow: 0 12px 30px rgba(30, 70, 130, 0.12);
}

.hero h1 {
    color: white;
    font-family: 'Manrope', sans-serif;
    font-size: 30px;
    font-weight: 800;
    margin-bottom: 8px;
}

.hero p {
    color: #D9E7FF;
    font-size: 14px;
}

/* Quick action cards */

div[data-testid="stButton"] button {
    border-radius: 12px;
    font-weight: 600;
    min-height: 43px;
}

/* Chat messages */

div[data-testid="stChatMessage"] {
    background: white;
    border: 1px solid #E7ECF5;
    border-radius: 15px;
    padding: 15px;
    margin-bottom: 12px;
    box-shadow: 0 3px 12px rgba(25, 45, 80, 0.035);
}

/* Disclaimer */

.hr-disclaimer {
    background: #FFF8E8;
    border: 1px solid #F1D89C;
    border-left: 4px solid #D69B24;
    padding: 13px 16px;
    border-radius: 10px;
    margin: 12px 0 16px 0;
    color: #745719;
    font-size: 12px;
}

/* Feedback */

.feedback-label {
    font-size: 12px;
    color: #71809A;
    margin-top: 8px;
}

/* Sources */

div[data-testid="stExpander"] {
    border: 1px solid #E1E8F3;
    border-radius: 10px;
    background: white;
}

/* Input */

div[data-testid="stChatInput"] {
    border-radius: 14px;
}

/* Footer */

.footer {
    text-align: center;
    color: #91A0B8;
    font-size: 11px;
    padding: 25px 0 10px 0;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# LOGO AND BRANDING
# =========================================================

def show_logo():
    st.markdown("""
    <div class="zyro-logo">
        <div class="zyro-mark">Z</div>
        <div>
            <div class="zyro-name">ZYRO DYNAMICS</div>
            <div class="zyro-subtitle">PEOPLE & HR ASSISTANT</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# LOAD RAG PIPELINE
# =========================================================

@st.cache_resource(show_spinner="Loading HR policy knowledge base...")
def load_pipeline():
    settings = get_settings()

    docs = load_policy_documents(
        settings.pdf_dir,
        expected_count=settings.expected_pdf_count
    )

    chunks = split_documents(
        docs,
        settings.chunk_size,
        settings.chunk_overlap
    )

    store = get_vector_store(chunks, settings)
    retriever = get_retriever(store, settings)
    chain = build_rag_pipeline(settings)

    return retriever, chain


try:
    retriever, chain = load_pipeline()

except Exception:
    st.error(
        "Could not initialize the HR knowledge base. "
        "Please check the policy PDFs, configuration and model credentials."
    )

    if os.getenv("DEBUG", "").lower() == "true":
        st.exception(Exception("Knowledge base initialization failed."))

    st.stop()


# =========================================================
# SESSION STATE
# =========================================================

if "active_chat" not in st.session_state:
    chats = get_all_chats()

    if chats:
        st.session_state.active_chat = chats[0][0]
    else:
        st.session_state.active_chat = create_chat()


if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    show_logo()

    st.markdown("---")

    if st.button("＋  New conversation", use_container_width=True):
        st.session_state.active_chat = create_chat()
        st.session_state.pending_question = None
        st.rerun()

    st.markdown("### Your conversations")

    chats = get_all_chats()

    if not chats:
        st.caption("Your conversations will appear here.")

    for chat_id, title in chats:

        label = ("● " if chat_id == st.session_state.active_chat else "○ ") + title

        if st.button(
            label,
            key=f"chat_{chat_id}",
            use_container_width=True,
        ):
            st.session_state.active_chat = chat_id
            st.session_state.pending_question = None
            st.rerun()

    st.markdown("---")

    st.markdown("### Conversation tools")

    current_messages = get_chat_messages(
        st.session_state.active_chat
    )

    if current_messages:

        export_lines = [
            "ZYRO DYNAMICS - HR POLICY ASSISTANT",
            "=" * 45,
            "",
        ]

        for msg in current_messages:
            role = "You" if msg["role"] == "user" else "HR Assistant"

            export_lines.append(f"{role}:")
            export_lines.append(msg["content"])
            export_lines.append("")

            if msg["sources"]:
                export_lines.append("Sources:")

                for source in msg["sources"]:
                    export_lines.append(
                        f"- {source.get('source', 'Unknown')} "
                        f"(Page {source.get('page', '?')})"
                    )

                export_lines.append("")

            if msg["feedback"]:
                export_lines.append(
                    f"Feedback: {msg['feedback']}"
                )
                export_lines.append("")

            export_lines.append("-" * 35)
            export_lines.append("")

        export_text = "\n".join(export_lines)

        st.download_button(
            "⬇  Download this chat",
            data=export_text,
            file_name="zyro_hr_conversation.txt",
            mime="text/plain",
            use_container_width=True,
        )

    else:
        st.caption("Ask a question to enable chat export.")

    if st.button("Clear current conversation", use_container_width=True):
        clear_chat_messages(st.session_state.active_chat)
        st.rerun()

    st.markdown("---")

    st.caption("Zyro Dynamics HR Help Desk")
    st.caption("Powered by Retrieval-Augmented Generation")


# =========================================================
# MAIN HEADER
# =========================================================

show_logo()

st.markdown("""
<div class="hero">
    <h1>Your HR knowledge, one conversation away.</h1>
    <p>
        Get answers from Zyro Dynamics HR policies.
        Ask about leave, benefits, workplace policies,
        performance and employee support.
    </p>
</div>
""", unsafe_allow_html=True)


# =========================================================
# GENERAL DISCLAIMER
# =========================================================

st.markdown("""
<div class="hr-disclaimer">
    <b>Important HR notice</b><br>
    Answers are generated from the available HR policy documents
    and are intended for general guidance. They are not official
    HR approvals or decisions. Confirm individual eligibility,
    exceptions, interpretations and important employment decisions
    with the HR team.
</div>
""", unsafe_allow_html=True)


# =========================================================
# QUICK QUESTIONS
# =========================================================

st.markdown("### What would you like to know?")

quick_questions = [
    "How does Earned Leave accrue?",
    "What is the work-from-home policy?",
    "What medical benefits are provided?",
    "What is the notice period?",
    "How do I raise a POSH complaint?",
    "What are the performance review timelines?",
]

cols = st.columns(3)

for i, question in enumerate(quick_questions):

    with cols[i % 3]:

        if st.button(
            question,
            key=f"quick_{i}",
            use_container_width=True,
        ):
            st.session_state.pending_question = question
            st.rerun()


st.markdown("---")


# =========================================================
# DISPLAY CHAT HISTORY
# =========================================================

messages = get_chat_messages(
    st.session_state.active_chat
)

for message in messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        if message["role"] == "assistant":

            if message["sources"]:

                with st.expander("📚 View policy sources"):

                    for source in message["sources"]:
                        st.markdown(
                            f"**{source.get('source', 'Unknown')}** "
                            f"— Page {source.get('page', '?')}"
                        )

            st.markdown("""
            <div class="hr-disclaimer">
                <b>HR confirmation:</b>
                This answer is policy-based guidance. Confirm
                individual circumstances, exceptions and approvals
                with the HR team.
            </div>
            """, unsafe_allow_html=True)

            st.markdown(
                '<div class="feedback-label">Was this answer helpful?</div>',
                unsafe_allow_html=True,
            )

            col1, col2, col3 = st.columns([1, 1, 5])

            with col1:
                if st.button(
                    "👍 Helpful",
                    key=f"helpful_{message['id']}",
                ):
                    save_feedback(message["id"], "Helpful")
                    st.rerun()

            with col2:
                if st.button(
                    "👎 Not Helpful",
                    key=f"not_helpful_{message['id']}",
                ):
                    save_feedback(message["id"], "Not Helpful")
                    st.rerun()

            if message["feedback"]:
                st.caption(
                    f"Your feedback: {message['feedback']}"
                )


# =========================================================
# PROCESS QUESTION
# =========================================================

question = st.chat_input(
    "Ask anything about Zyro Dynamics HR policies..."
)

if st.session_state.pending_question:

    question = st.session_state.pending_question
    st.session_state.pending_question = None


if question:

    chat_id = st.session_state.active_chat

    # Save user question
    save_message(
        chat_id,
        "user",
        question,
    )

    # Update conversation title for its first question
    existing_messages = get_chat_messages(chat_id)

    if len(existing_messages) == 1:
        update_chat_title(chat_id, question)

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):

        with st.spinner(
            "Searching HR policy documents..."
        ):

            try:

                result = answer_question(
                    question,
                    retriever,
                    chain,
                )

                answer = result["answer"]
                sources = result.get("sources", [])

                st.markdown(answer)

                if sources:

                    with st.expander("📚 View policy sources"):

                        for source in sources:
                            st.markdown(
                                f"**{source.get('source', 'Unknown')}** "
                                f"— Page {source.get('page', '?')}"
                            )

                st.markdown("""
                <div class="hr-disclaimer">
                    <b>HR confirmation:</b>
                    This answer is based on available policy documents.
                    Confirm individual eligibility, exceptions,
                    approvals and important decisions with HR.
                </div>
                """, unsafe_allow_html=True)

                message_id = save_message(
                    chat_id,
                    "assistant",
                    answer,
                    sources,
                )

                st.markdown(
                    '<div class="feedback-label">Was this answer helpful?</div>',
                    unsafe_allow_html=True,
                )

                col1, col2 = st.columns([1, 1])

                with col1:
                    if st.button(
                        "👍 Helpful",
                        key=f"new_helpful_{message_id}",
                    ):
                        save_feedback(message_id, "Helpful")
                        st.rerun()

                with col2:
                    if st.button(
                        "👎 Not Helpful",
                        key=f"new_not_helpful_{message_id}",
                    ):
                        save_feedback(message_id, "Not Helpful")
                        st.rerun()

            except Exception:

                error_message = (
                    "I couldn't complete your request right now. "
                    "Please check the model service and credentials, "
                    "then try again."
                )

                st.error(error_message)

                save_message(
                    chat_id,
                    "assistant",
                    error_message,
                )

                if os.getenv("DEBUG", "").lower() == "true":
                    st.exception(Exception("Question processing failed."))

    st.rerun()


# =========================================================
# FOOTER
# =========================================================

st.markdown("""
<div class="footer">
    ZYRO DYNAMICS · HR POLICY ASSISTANT<br>
    AI-powered policy assistance | Always verify important decisions with HR
</div>
""", unsafe_allow_html=True)
