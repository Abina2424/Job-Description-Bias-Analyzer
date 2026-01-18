import os
import httpx
from typing import Dict, Any
from app.models import BiasAnalysis


async def trigger_webhook(analysis: BiasAnalysis) -> bool:
    """Send analysis results to webhook URL"""
    webhook_url = os.getenv("WEBHOOK_URL")
    
    if not webhook_url:
        print("Warning: WEBHOOK_URL not set, skipping webhook")
        return False
    
    payload = {
        "job_description": analysis.job_description,
        "biased_terms": analysis.biased_terms,
        "bias_type": analysis.bias_type,
        "bias_explanation": analysis.bias_explanation,
        "inclusive_alternative": analysis.inclusive_alternative
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload, timeout=10.0)
            response.raise_for_status()
            return True
    except Exception as e:
        print(f"Webhook error: {e}")
        return False
