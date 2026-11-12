import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv(override=True)

POLICY_DIR = Path("data/hr_policies")
INDEX_DIR = Path("faiss_index")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

SYSTEM_PROMPT = """You are Zyro Dynamics' internal HR Help Desk assistant.
Answer the employee's question using ONLY the supplied HR policy context.
Do not use outside knowledge or invent policy details, numbers, deadlines, eligibility rules, or contacts.
If the context does not contain enough information to answer, say:
"I'm sorry, but I couldn't find that information in the available Zyro Dynamics HR policies. Please contact the HR team for clarification."
Be concise, clear, and helpful. If the policy has conditions or exceptions, include them.
"""

class HRRAG:
    def __init__(self, vectorstore, llm):
        self.vectorstore = vectorstore
        self.llm = llm
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT + "\n\nRelevant policy excerpts:\n{context}"),
            ("human", "{question}")
        ])
        self.chain = prompt | llm | StrOutputParser()

    def ask(self, question: str):
        # Use raw FAISS L2 distances. Lower distance means a closer match.
        scored = self.vectorstore.similarity_search_with_score(question, k=4)

        if not scored or float(scored[0][1]) > 1.20:
            return (
                "I'm sorry, but I couldn't find that information in the available Zyro Dynamics HR policies. "
                "Please contact the HR team for clarification.",
                []
            )

        # MMR provides diverse policy excerpts for the final grounded answer.
        docs = self.vectorstore.max_marginal_relevance_search(
            question, k=5, fetch_k=12, lambda_mult=0.65
        )

        context_parts, sources = [], []
        seen = set()

        for doc in docs:
            source = Path(doc.metadata.get("source", "Unknown document")).name
            page = int(doc.metadata.get("page", 0)) + 1
            context_parts.append(f"[Source: {source}, page {page}]\n{doc.page_content}")

            label = f"{source} — page {page}"
            if label not in seen:
                sources.append(label)
                seen.add(label)

        answer = self.chain.invoke({
            "question": question,
            "context": "\n\n".join(context_parts)
        })

        return answer.strip(), sources

def build_rag():
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is missing. Add it to a .env file or environment variable.")
    pdf_files = sorted(POLICY_DIR.glob("*.pdf"))
    if not pdf_files:
        raise RuntimeError(f"No PDF files found in {POLICY_DIR.resolve()}")
    documents = []
    for pdf in pdf_files:
        documents.extend(PyPDFLoader(str(pdf)).load())
    if not documents:
        raise RuntimeError("The PDF files were found, but no readable text was extracted.")
    splitter = RecursiveCharacterTextSplitter(chunk_size=850, chunk_overlap=150)
    chunks = splitter.split_documents(documents)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    return HRRAG(vectorstore, llm)
