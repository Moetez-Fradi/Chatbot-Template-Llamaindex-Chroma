from llama_index.llms.openai_like import OpenAILike
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import Document
from llama_index.core import PromptTemplate
from llama_index.core.query_engine import CustomQueryEngine
from llama_index.core.retrievers import BaseRetriever
from typing import Any
from dotenv import load_dotenv
import asyncio
import chromadb
import os
import warnings
from scripts.read_data import load_docs_from_folder

warnings.filterwarnings("ignore")
load_dotenv()

qa_prompt = PromptTemplate(
    "Below is the content of the conversation so far.\n"
    "---------------------\n"
    "{conversation}\n"
    "---------------------\n"
    "Below is context information about SpongePy.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "You are a friendly, helpful, and slightly humorous AI assistant whose job is to explain and assist users with SpongePy.\n"
    "Only use the context provided; if the answer is not clear from it, respond with “I don’t know.”\n"
    "You may only rely on prior knowledge when it is directly relevant to Data Science.\n"
    "Don't mention the context or the source of the information in your response.\n"
    "Question: {query_str}\n"
    "Answer: "
)

docs_text = load_docs_from_folder("data")
documents = [Document(text=chunk) for chunk in docs_text]

db = chromadb.PersistentClient(path="./db_chroma")
chroma_collection = db.get_or_create_collection("docs")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

embedder = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")
index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embedder)

pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_overlap=0),
        HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2"),
    ],
    vector_store=vector_store,
)

async def index_docs():
    # takes a list of documents
    result = await pipeline.arun(documents=documents)
    return result
asyncio.run(index_docs())

llm = OpenAILike(
    model="meta-llama/llama-3-8b-instruct",
    api_base=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
    is_chat_model=True,
    context_window=8192,
    temperature=1,
)

retriever = index.as_retriever(similarity_top_k=5, similarity_threshold=0.4)

class RAGStringQueryEngine(CustomQueryEngine):
    """RAG String Query Engine."""

    retriever: BaseRetriever
    llm: Any
    qa_prompt: PromptTemplate

    def custom_query(self, query_str: str, conversation: list) -> str:
        nodes = self.retriever.retrieve(query_str)

        context_str = "\n\n".join([n.node.get_content() for n in nodes])
        
        prompt = self.qa_prompt.format(context_str=context_str, query_str=query_str, conversation="\n".join(conversation))


        resp = self.llm.complete(prompt)
        text = getattr(resp, "text", None) or str(resp)

        return text

query_engine = RAGStringQueryEngine(
    retriever=retriever,
    llm=llm,
    qa_prompt=qa_prompt,
)

conversation = []

print("Welcome, coder! \n")
while True:
    # reduce context length to avoid exceeding the model's context window
    if (len(conversation) > 10):
        conversation = conversation[-10:]
    try:
        prompt = input("You > ")
        answer = query_engine.custom_query(prompt, conversation)
        print("\nChatbot > ", answer)
        interaction = f"You: {prompt}\nChatbot: {answer}"
        conversation.append(interaction)
        print("\n")
    except KeyboardInterrupt:
        print("\nGoodbye! It was nice chatting with you")
        break