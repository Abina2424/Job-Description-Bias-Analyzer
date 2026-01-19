from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uuid
import logging
from app.models import ChatMessage, ChatResponse
from app.graph import create_graph

load_dotenv()

app = FastAPI(title="Job Description Bias Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://job-description-bias-analyzer-1.vercel.app",
        "https://job-description-bias-analyzer-1.vercel.app/"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = create_graph()
conversations = {}
logger = logging.getLogger("uvicorn.error")


@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    try:
        conversation_id = message.conversation_id or str(uuid.uuid4())

        if conversation_id not in conversations:
            conversations[conversation_id] = {
                "messages": [],
                "job_description": "",
                "biased_terms": [],
                "bias_type": None,
                "bias_explanation": "",
                "inclusive_alternative": "",
                "requires_clarification": False,
                "conversation_id": conversation_id,
                "analysis_complete": False,
                "current_response": "",
            }

        state = conversations[conversation_id]

        state["messages"].append({
            "role": "user",
            "content": message.message
        })

        result = await graph.ainvoke(state)

        if result.get("current_response"):
            result["messages"].append({
                "role": "assistant",
                "content": result["current_response"]
            })

        conversations[conversation_id] = result

        assistant_messages = [
            m for m in result.get("messages", [])
            if m.get("role") == "assistant"
        ]

        response_text = (
            assistant_messages[-1]["content"]
            if assistant_messages else "Analysis complete."
        )

        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            requires_clarification=result.get("requires_clarification", False),
        )

    except Exception as e:
        logger.error(f"Error in /chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "healthy"}
