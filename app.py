
import streamlit as st
import uuid
from rag_pipeline import build_rag


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Zyro HR Assistant",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --------------------------------------------------
# PREMIUM LIGHT THEME CSS
# --------------------------------------------------

st.markdown("""
<style>

.stApp {
    background-color: #F5F7FB;
    color: #172033;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1150px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

section[data-testid="stSidebar"] {
    background-color: #111827;
    border-right: 1px solid #253247;
}

section[data-testid="stSidebar"] * {
    color: #E5E7EB;
}

section[data-testid="stSidebar"] button {
    background-color: #1F2937;
    border: 1px solid #374151;
    border-radius: 10px;
    color: white;
    width: 100%;
    text-align: left;
}

section[data-testid="stSidebar"] button:hover {
    background-color: #26364D;
    border-color: #60A5FA;
}

h1, h2, h3 {
    color: #172033 !important;
    font-weight: 700 !important;
}

.hero {
    background: linear-gradient(120deg, #172554, #1D4ED8);
    padding: 32px;
    border-radius: 20px;
    color: white;
    margin-bottom: 25px;
    box-shadow: 0 8px 24px rgba(30, 64, 175, 0.12);
}

.hero h1 {
    color: white !important;
    font-size: 30px;
    margin-bottom: 8px;
}

.hero p {
    color: #DBEAFE;
    font-size: 15px;
}

div.stButton > button {
    border-radius: 12px;
    border: 1px solid #E1E7F0;
    background: white;
    color: #172033;
    padding: 12px 16px;
    min-height: 55px;
    transition: all 0.2s ease;
    font-weight: 600;
}

div.stButton > button:hover {
    border-color: #2563EB;
    color: #2563EB;
    background: #EFF6FF;
}

div[data-testid="stChatMessage"] {
    background: white;
    border: 1px solid #E6EAF0;
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 12px;
    box-shadow: 0 3px 12px rgba(15, 23, 42, 0.03);
}

div[data-testid="stChatInput"] {
    background: white;
    border-radius: 15px;
}

.citation {
    background: #EFF6FF;
    border-left: 4px solid #2563EB;
    padding: 12px 15px;
    border-radius: 8px;
    color: #1E3A8A;
    font-size: 13px;
    margin-top: 10px;
}

.status {
    display: inline-block;
    background: #DCFCE7;
    color: #166534;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}

.footer {
    text-align: center;
    color: #94A3B8;
    font-size: 12px;
    padding: 25px 0;
}

hr {
    border-color: #E5EAF2;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "chats" not in st.session_state:
    st.session_state.chats = [
        {
            "id": str(uuid.uuid4()),
            "title": "New conversation",
            "messages": []
        }
    ]

if "active_chat" not in st.session_state:
    st.session_state.active_chat = 0

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# --------------------------------------------------
# RAG BACKEND
# --------------------------------------------------

@st.cache_resource
def load_rag():
    return build_rag()


try:
    rag = load_rag()
except Exception as e:
    st.error("Unable to initialize the HR Assistant.")
    st.exception(e)
    st.stop()


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def get_current_chat():
    return st.session_state.chats[st.session_state.active_chat]


def create_new_chat():
    st.session_state.chats.append({
        "id": str(uuid.uuid4()),
        "title": "New conversation",
        "messages": []
    })

    st.session_state.active_chat = len(st.session_state.chats) - 1
    st.session_state.pending_question = None


def select_chat(index):
    st.session_state.active_chat = index
    st.session_state.pending_question = None


def set_question(question):
    st.session_state.pending_question = question


def build_chat_export(chat):
    lines = [
        "ZYRO DYNAMICS - HR ASSISTANT CHAT",
        "=" * 40,
        f"Conversation: {chat['title']}",
        ""
    ]

    for message in chat["messages"]:
        role = message["role"].upper()

        lines.append(f"{role}:")
        lines.append(message["content"])

        if message["role"] == "assistant":
            sources = message.get("sources", [])

            if sources:
                lines.append("Sources:")
                lines.extend(f"- {source}" for source in sources)

        lines.append("")

    lines.append(
        "Disclaimer: AI-generated responses should be verified "
        "with the HR team before making official decisions."
    )

    return "\n".join(lines)


def process_question(question):
    question = question.strip()

    if not question:
        return

    chat = get_current_chat()

    chat["messages"].append({
        "role": "user",
        "content": question
    })

    if chat["title"] == "New conversation":
        chat["title"] = question[:35] + (
            "..." if len(question) > 35 else ""
        )

    try:
        with st.spinner("Zyro Assistant is thinking..."):
            answer, sources = rag.ask(question)

        chat["messages"].append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })

    except Exception as e:
        chat["messages"].append({
            "role": "assistant",
            "content": (
                "I'm sorry, something went wrong while processing "
                "your question. Please try again."
            ),
            "sources": []
        })

        st.error(f"Technical error: {e}")


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.markdown("""
    <div style="padding:10px 0 20px 0;">
        <div style="font-size:28px;font-weight:800;color:white;">
            💼 ZYRO
        </div>
        <div style="font-size:12px;color:#9CA3AF;letter-spacing:2px;">
            DYNAMICS HR PORTAL
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    if st.button("＋ New Chat", use_container_width=True):
        create_new_chat()
        st.rerun()

    st.markdown("### Your Conversations")

    for i, chat in enumerate(st.session_state.chats):
        label = "💬 " + chat["title"]

        if st.button(
            label,
            key=f"chat_{chat['id']}",
            use_container_width=True
        ):
            select_chat(i)
            st.rerun()

    # Download current conversation
    current_chat = get_current_chat()

    st.download_button(
        label="⬇ Download Current Chat",
        data=build_chat_export(current_chat),
        file_name="zyro_hr_chat.txt",
        mime="text/plain",
        use_container_width=True,
        disabled=len(current_chat["messages"]) == 0
    )

    st.markdown("---")

    st.markdown("### HR Help Desk")

    page = st.radio(
        "Navigation",
        ["Assistant", "About Zyro"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.markdown("""
    <div style="background:#1F2937;padding:15px;border-radius:12px;">
        <div style="color:#86EFAC;font-weight:600;font-size:13px;">
            ● AI SYSTEM ACTIVE
        </div>
        <p style="color:#9CA3AF;font-size:12px;margin-top:6px;">
            Powered by RAG technology
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:11px;color:#9CA3AF;margin-top:30px;">
        Zyro Dynamics Pvt. Ltd.<br>
        Internal HR Knowledge Assistant
    </div>
    """, unsafe_allow_html=True)


# --------------------------------------------------
# ABOUT PAGE
# --------------------------------------------------

if page == "About Zyro":

    st.markdown("# About Zyro Dynamics")

    st.markdown("""
    <div class="hero">
        <h1>Welcome to Zyro Dynamics</h1>
        <p>
            Your intelligent workplace assistant for HR policies,
            employee information and organizational guidelines.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### About this project")

    st.write("""
    The Zyro Dynamics Intelligent HR Help Desk is an AI-powered
    knowledge assistant designed to help employees find answers
    from official company HR policy documents.
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Policy Documents", "11")

    with col2:
        st.metric("AI Architecture", "RAG")

    with col3:
        st.metric("Vector Database", "FAISS")

    st.markdown("### Technology Stack")

    st.markdown("""
    - **Frontend:** Streamlit
    - **LLM:** Groq
    - **Embeddings:** Sentence Transformers
    - **Vector Database:** FAISS
    - **Framework:** LangChain
    - **Knowledge Base:** Zyro Dynamics HR policy PDFs
    """)

    st.info(
        "This assistant provides information from available policy documents. "
        "For official decisions or clarification, contact the HR team."
    )

    st.stop()


# --------------------------------------------------
# MAIN ASSISTANT PAGE
# --------------------------------------------------

st.markdown("""
<div class="hero">
    <div style="font-size:13px;letter-spacing:2px;font-weight:600;">
        ZYRO DYNAMICS • PEOPLE & CULTURE
    </div>
    <h1>Your Intelligent HR Assistant</h1>
    <p>
        Ask questions about company policies, leave, compensation,
        benefits and workplace guidelines.
    </p>
    <span class="status">● Online and ready to help</span>
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------
# QUICK ACTION CARDS
# --------------------------------------------------

chat = get_current_chat()

if not chat["messages"]:

    st.markdown("### How can I help you today?")
    st.caption("Choose a topic or type your own question below.")

    quick_questions = [
        ("🏖️ Leave Policy", "How does my Earned Leave accrue every month?"),
        ("🏠 Work From Home", "Am I eligible to work from home at my grade?"),
        ("💰 Salary & Benefits", "What medical insurance coverage does the company provide?"),
        ("📈 Performance", "When am I put on a Performance Improvement Plan?"),
        ("🛡️ Code of Conduct", "Can I accept a gift from a client or vendor?"),
        ("✈️ Travel Policy", "What are my hotel and daily allowances for international travel?")
    ]

    columns = st.columns(3)

    for i, (label, question) in enumerate(quick_questions):
        with columns[i % 3]:
            if st.button(
                label,
                key=f"quick_{i}",
                use_container_width=True
            ):
                st.session_state.pending_question = question
                st.rerun()

    st.markdown("---")
    st.markdown("### Suggested questions")

    suggestions = [
        "How much Earned Leave can I carry forward?",
        "What is the salary credit date?",
        "How do I raise a POSH complaint?",
        "What notice period do I need to serve?"
    ]

    cols = st.columns(2)

    for i, question in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(
                "↗ " + question,
                key=f"suggest_{i}",
                use_container_width=True
            ):
                st.session_state.pending_question = question
                st.rerun()


# --------------------------------------------------
# DISPLAY CHAT HISTORY
# --------------------------------------------------

chat = get_current_chat()

for message in chat["messages"]:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        if message["role"] == "assistant":

            sources = message.get("sources", [])

            if sources:
                with st.expander("📚 View policy sources"):
                    for source in sources:
                        st.markdown(
                            f'<div class="citation">📄 {source}</div>',
                            unsafe_allow_html=True
                        )


# --------------------------------------------------
# PROCESS QUICK QUESTION
# --------------------------------------------------

if st.session_state.pending_question:

    question = st.session_state.pending_question
    st.session_state.pending_question = None

    process_question(question)
    st.rerun()


# --------------------------------------------------
# CHAT INPUT
# --------------------------------------------------

user_question = st.chat_input(
    "Ask anything about Zyro Dynamics HR policies..."
)

if user_question:
    process_question(user_question)
    st.rerun()


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("""
<div class="footer">
    Powered by AI • Zyro Dynamics Pvt. Ltd.<br>
    Your intelligent HR policy assistant
</div>
""", unsafe_allow_html=True)
