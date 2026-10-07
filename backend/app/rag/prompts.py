from langchain_core.prompts import PromptTemplate

# Exact prompt specified in the requirements
RAG_SYSTEM_PROMPT = """You are an academic AI assistant. Answer the user's question using ONLY the provided context from the uploaded academic documents.

Context:
{context}

Question:
{question}

Instructions:
- Give a clear and accurate answer in a student-friendly way.
- Use the retrieved context as the only source. Do not invent facts.
- If the context does not contain enough information, say: I couldn't find enough information in the uploaded documents to answer this question.
- Use bullet points or short sections where helpful."""

ACADEMIC_RAG_PROMPT = PromptTemplate(
    template=RAG_SYSTEM_PROMPT,
    input_variables=["context", "question"]
)

# Follow-up query condenser prompt
CONDENSE_PROMPT_TEMPLATE = """Given the following conversation between a student and an academic AI assistant, and a follow-up question, rephrase the follow-up question into a standalone, search-friendly academic question that can be used directly for document retrieval.
Do NOT answer the question. Only return the standalone question. If the follow-up is already a standalone question, return it unchanged.

Chat History:
{chat_history}

Follow-up Question: {question}
Standalone Question:"""

CONDENSE_QUESTION_PROMPT = PromptTemplate(
    template=CONDENSE_PROMPT_TEMPLATE,
    input_variables=["chat_history", "question"]
)
