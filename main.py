from llama_index.llms.openai_like import OpenAILike
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import Document
from dotenv import load_dotenv
import asyncio
import chromadb
import os
import warnings
from scripts.read_data import load_docs_from_folder

warnings.filterwarnings("ignore")
load_dotenv()

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

async def main():
    # takes a list of documents
    result = await pipeline.arun(documents=documents)
    return result
asyncio.run(main())

llm = OpenAILike(
    model="meta-llama/llama-3-8b-instruct",
    api_base=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
    is_chat_model=True,
    context_window=8192,
    temperature=1,
)

# OR as_retriever OR as_chat_engine
query_engine = index.as_query_engine(
    # streaming=True,
    llm=llm,
    response_mode="tree_summarize", # OR refine OR compact
)

print("Welcome, coder! \n")
while True:
    try:
        prompt = input("You > ")
        answer = query_engine.query(prompt)
        print("\nChatbot > ", answer)
        print("\n")
    except KeyboardInterrupt:
        print("\nGoodbye!")
        break