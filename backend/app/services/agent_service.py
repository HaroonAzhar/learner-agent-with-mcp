import httpx
import logging

logger = logging.getLogger(__name__)

AGENT_URL = "http://localhost:10000" # URL of the A2A agent service

async def trigger_resource_analysis(resource_id: int, url: str):
    """
    Triggers the Learner Agent to analyze a resource.
    This sends a message to the agent acting as the 'User'.
    """
    logger.info(f"Triggering analysis for resource {resource_id} at {url}")
    try:
        # A2A agent typically accepts a POST to /v1/conversations/send or similar if it's A2A compliant.
        # However, checking the agent code: `a2a_app = to_a2a(root_agent, port=10000)`
        # This usually exposes stats standard endpoints.
        # We'll assume a standard message structure.
        
        # TODO: Clarify exact payload structure for LlmAgent exposed via to_a2a. 
        # For now, we'll try to send a message that starts the flow defined in the prompt.
        payload = {
            "message": f"Analyze this resource: {url}",
            # "context": {"resource_id": resource_id} # Pass ID if agent supports context
        }
        
        # Using a timeout as agents can be slow, but we might just fire and forget or use background task
        async with httpx.AsyncClient() as client:
             # This endpoint is valid for A2A? Or is it a custom route?
             # If using 'to_a2a', it might wrap it as a Refract/standard agent server.
             # Let's assume a simple /chat endpoint or similar for now, usually it's /
             resp = await client.post(f"{AGENT_URL}/", json=payload, timeout=5.0)
             resp.raise_for_status()
             logger.info(f"Agent triggered: {resp.json()}")
             
    except Exception as e:
        logger.error(f"Failed to trigger agent: {e}")
        # In production, we might want to retry or queue this.
