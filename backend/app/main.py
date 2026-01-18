from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import uuid
import logging
from app.models import ChatMessage, ChatResponse
from app.graph import create_graph
from app.supabase_client import SupabaseClient
from app.models import BiasAnalysis


load_dotenv()

app = FastAPI(title="Job Description Bias Analyzer")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize graph
graph = create_graph()

# Store conversations (in production, use Redis or database)
conversations = {}

# Setup logger once
logger = logging.getLogger("uvicorn.error")


@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Main chat endpoint for job description analysis"""
    try:
        # 1. Get or create conversation ID
        conversation_id = message.conversation_id or str(uuid.uuid4())

        # 2. Initialize or get conversation state
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
            }

        state = conversations[conversation_id]

        # 3. Add user message
        state["messages"].append({
            "role": "user",
            "content": message.message
        })

        # 4. Run agent graph
        logger.info(f"Invoking graph with state: {state}")
        result = await graph.ainvoke(state)
        logger.info(f"Graph result: {result}")

        # 5. Update conversation state
        conversations[conversation_id] = result

        # 6. Prepare data for Supabase
        analysis_data = {
            "job_description": result.get("job_description", message.message),
            "biased_terms": result.get("biased_terms", []),
            "bias_type": result.get("bias_type") or "neutral",
            "bias_explanation": result.get("bias_explanation", ""),
            "inclusive_alternative": result.get("inclusive_alternative", "")
        }

        # 7. Store in Supabase
        try:
            SupabaseClient.store_analysis(analysis_data)
            logger.info("Analysis stored successfully in Supabase")
        except Exception as e:
            logger.error(f"Supabase insert failed: {e}")

        # 8. Get assistant response
        assistant_messages = [
            m for m in result.get("messages", [])
            if isinstance(m, dict) and m.get("role") == "assistant"
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
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)