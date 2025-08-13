from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import BackgroundTasks
from query_engine import query_engine, index_docs
from fastapi.concurrency import run_in_threadpool

app = FastAPI(title="SpongePy Chatbot")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_index():
    return FileResponse("static/index.html")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conversation = []

class ChatRequest(BaseModel):
    message: str

@app.on_event("startup")
async def startup_event(background_tasks: BackgroundTasks = None):
    await index_docs()

@app.post("/chat")
async def chat(req: ChatRequest):
    global conversation
    if len(conversation) > 10:
        conversation = conversation[-10:]
    answer = await run_in_threadpool(query_engine.custom_query, req.message, conversation)
    conversation.append(f"You: {req.message}\nChatbot: {answer}")
    return {"reply": answer}