from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import os
from app.models import BiasAnalysis
from app.supabase_client import SupabaseClient
from app.webhook import trigger_webhook


# Bias keyword lists
MASCULINE_KEYWORDS = [
    "aggressive", "dominant", "competitive", "assertive", "rockstar", 
    "ninja", "guru", "warrior", "champion", "leader", "decisive", 
    "confident", "ambitious", "driven", "forceful", "commanding"
]

FEMININE_KEYWORDS = [
    "nurturing", "supportive", "caring", "collaborative", "empathetic",
    "gentle", "patient", "understanding", "helpful", "cooperative",
    "warm", "compassionate", "sensitive", "kind", "thoughtful"
]


class GraphState(TypedDict):
    messages: Annotated[list, lambda x, y: x + y]
    job_description: str
    biased_terms: list
    bias_type: Literal["masculine", "feminine", "neutral", None]
    bias_explanation: str
    inclusive_alternative: str
    requires_clarification: bool
    conversation_id: str
    analysis_complete: bool


def detect_bias_keywords(text: str) -> tuple[list, Literal["masculine", "feminine", "neutral"]]:
    """Detect biased keywords in text and classify bias type"""
    text_lower = text.lower()
    found_masculine = [kw for kw in MASCULINE_KEYWORDS if kw in text_lower]
    found_feminine = [kw for kw in FEMININE_KEYWORDS if kw in text_lower]
    
    if found_masculine and not found_feminine:
        return found_masculine, "masculine"
    elif found_feminine and not found_masculine:
        return found_feminine, "feminine"
    elif found_masculine and found_feminine:
        # Mixed bias - prioritize more frequent
        if len(found_masculine) >= len(found_feminine):
            return found_masculine + found_feminine, "masculine"
        else:
            return found_masculine + found_feminine, "feminine"
    else:
        return [], "neutral"


def start_node(state: GraphState) -> GraphState:
    """Receive user input and initialize state"""
    messages = state.get("messages", [])
    if not messages:
        return state
    
    last_message = messages[-1]
    user_input = last_message.get("content", "") if isinstance(last_message, dict) else str(last_message)
    
    # Initialize state if needed
    if not state.get("job_description"):
        state["job_description"] = user_input
    
    # Detect bias
    biased_terms, bias_type = detect_bias_keywords(user_input)
    state["biased_terms"] = biased_terms
    state["bias_type"] = bias_type
    
    return state


def router_node(state: GraphState) -> GraphState:
    """Route to appropriate bias handling node - passes through state"""
    return state


def generate_bias_explanation(bias_type: str, biased_terms: list, llm: ChatOpenAI) -> tuple[str, str]:
    """Generate bias explanation and inclusive alternative using LLM"""
    if bias_type == "neutral":
        return (
            "The job description appears to use neutral, inclusive language.",
            "No changes needed. The language is already inclusive."
        )
    
    bias_direction = "masculine-coded" if bias_type == "masculine" else "feminine-coded"
    terms_str = ", ".join(biased_terms)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert in inclusive language and gender bias detection in job descriptions."),
        ("user", f"""The following job description contains {bias_direction} language with these terms: {terms_str}

Please provide:
1. A clear explanation (2-3 sentences) of why these terms may create gender bias and discourage certain applicants.
2. A suggested inclusive, gender-neutral alternative phrasing that maintains the same meaning but appeals to all candidates.

Format your response as:
EXPLANATION: [your explanation]
ALTERNATIVE: [your alternative phrasing]""")
    ])
    
    try:
        chain = prompt | llm
        response = chain.invoke({})
        content = response.content
        
        # Parse response
        parts = content.split("ALTERNATIVE:")
        explanation = parts[0].replace("EXPLANATION:", "").strip()
        alternative = parts[1].strip() if len(parts) > 1 else "Consider using more neutral language that focuses on skills and outcomes."
        
        return explanation, alternative
    except Exception as e:
        print(f"LLM error: {e}")
        default_explanation = f"These {bias_direction} terms may unconsciously signal that the role is better suited for one gender, potentially discouraging qualified candidates from applying."
        default_alternative = f"Replace terms like '{terms_str}' with neutral alternatives that focus on skills, behaviors, and outcomes rather than personality traits."
        return default_explanation, default_alternative


def check_completeness(state: GraphState) -> tuple[bool, str]:
    """Check if all required fields are present"""
    if not state.get("job_description") or len(state.get("job_description", "").strip()) < 10:
        return False, "Can you provide the complete job description text? The current input seems incomplete."
    
    if not state.get("bias_explanation"):
        return False, None  # Will be generated
    
    if not state.get("inclusive_alternative"):
        return False, None  # Will be generated
    
    return True, None


async def masculine_bias_node(state: GraphState) -> GraphState:
    """Handle masculine-coded bias"""
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY"))
    
    # Check completeness
    is_complete, clarification = check_completeness(state)
    
    if not is_complete:
        if clarification:
            state["requires_clarification"] = True
            state["messages"].append({
                "role": "assistant",
                "content": clarification
            })
            return state
        else:
            # Generate explanation and alternative
            explanation, alternative = generate_bias_explanation("masculine", state.get("biased_terms", []), llm)
            state["bias_explanation"] = explanation
            state["inclusive_alternative"] = alternative
    
    # Store and trigger webhook
    if not state.get("analysis_complete"):
        analysis = BiasAnalysis(
            job_description=state["job_description"],
            biased_terms=state.get("biased_terms", []),
            bias_type="masculine",
            bias_explanation=state["bias_explanation"],
            inclusive_alternative=state["inclusive_alternative"]
        )
        
        # Store in Supabase
        try:
            SupabaseClient.store_analysis(analysis.dict())
        except Exception as e:
            print(f"Supabase error: {e}")
        
        # Trigger webhook
        await trigger_webhook(analysis)
        state["analysis_complete"] = True
    
    # Generate response message
    response_text = f"""**Masculine-Coded Bias Detected**

**Biased Terms Found:** {', '.join(state.get('biased_terms', []))}

**Explanation:**
{state['bias_explanation']}

**Inclusive Alternative:**
{state['inclusive_alternative']}"""
    
    state["messages"].append({
        "role": "assistant",
        "content": response_text
    })
    
    return state


async def feminine_bias_node(state: GraphState) -> GraphState:
    """Handle feminine-coded bias"""
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY"))
    
    # Check completeness
    is_complete, clarification = check_completeness(state)
    
    if not is_complete:
        if clarification:
            state["requires_clarification"] = True
            state["messages"].append({
                "role": "assistant",
                "content": clarification
            })
            return state
        else:
            # Generate explanation and alternative
            explanation, alternative = generate_bias_explanation("feminine", state.get("biased_terms", []), llm)
            state["bias_explanation"] = explanation
            state["inclusive_alternative"] = alternative
    
    # Store and trigger webhook
    if not state.get("analysis_complete"):
        analysis = BiasAnalysis(
            job_description=state["job_description"],
            biased_terms=state.get("biased_terms", []),
            bias_type="feminine",
            bias_explanation=state["bias_explanation"],
            inclusive_alternative=state["inclusive_alternative"]
        )
        
        # Store in Supabase
        try:
            SupabaseClient.store_analysis(analysis.dict())
        except Exception as e:
            print(f"Supabase error: {e}")
        
        # Trigger webhook
        await trigger_webhook(analysis)
        state["analysis_complete"] = True
    
    # Generate response message
    response_text = f"""**Feminine-Coded Bias Detected**

**Biased Terms Found:** {', '.join(state.get('biased_terms', []))}

**Explanation:**
{state['bias_explanation']}

**Inclusive Alternative:**
{state['inclusive_alternative']}"""
    
    state["messages"].append({
        "role": "assistant",
        "content": response_text
    })
    
    return state


async def neutral_node(state: GraphState) -> GraphState:
    """Handle neutral/inclusive language"""
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY"))
    
    # Check completeness
    is_complete, clarification = check_completeness(state)
    
    if not is_complete:
        if clarification:
            state["requires_clarification"] = True
            state["messages"].append({
                "role": "assistant",
                "content": clarification
            })
            return state
        else:
            # Generate explanation and alternative
            explanation, alternative = generate_bias_explanation("neutral", [], llm)
            state["bias_explanation"] = explanation
            state["inclusive_alternative"] = alternative
    
    # Store and trigger webhook
    if not state.get("analysis_complete"):
        analysis = BiasAnalysis(
            job_description=state["job_description"],
            biased_terms=[],
            bias_type="neutral",
            bias_explanation=state["bias_explanation"],
            inclusive_alternative=state["inclusive_alternative"]
        )
        
        # Store in Supabase
        try:
            SupabaseClient.store_analysis(analysis.dict())
        except Exception as e:
            print(f"Supabase error: {e}")
        
        # Trigger webhook
        await trigger_webhook(analysis)
        state["analysis_complete"] = True
    
    # Generate response message
    response_text = f"""**Neutral/Inclusive Language Detected**

**Analysis:**
{state['bias_explanation']}

**Recommendation:**
{state['inclusive_alternative']}"""
    
    state["messages"].append({
        "role": "assistant",
        "content": response_text
    })
    
    return state


def create_graph():
    """Create and compile LangGraph workflow"""
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("start", start_node)
    workflow.add_node("router", router_node)
    workflow.add_node("masculine_bias_node", masculine_bias_node)
    workflow.add_node("feminine_bias_node", feminine_bias_node)
    workflow.add_node("neutral_node", neutral_node)
    
    # Set entry point
    workflow.set_entry_point("start")
    
    # Add edges
    workflow.add_edge("start", "router")
    workflow.add_conditional_edges(
        "router",
        lambda state: state.get("bias_type", "neutral"),
        {
            "masculine": "masculine_bias_node",
            "feminine": "feminine_bias_node",
            "neutral": "neutral_node"
        }
    )
    
    workflow.add_edge("masculine_bias_node", END)
    workflow.add_edge("feminine_bias_node", END)
    workflow.add_edge("neutral_node", END)
    
    return workflow.compile()
