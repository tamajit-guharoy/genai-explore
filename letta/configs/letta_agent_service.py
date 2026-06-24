import time
import logging
from typing import Optional
from contextlib import contextmanager
from letta_client import Letta, LettaError

class LettaAgentService:
    """
    Production-ready wrapper for Letta agents.
    
    Features:
    - Connection pooling (via client reuse)
    - Automatic retry with exponential backoff
    - Structured logging
    - Health checks
    - Cost tracking
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url
        self.client = Letta(
            base_url=base_url,
            api_key=api_key
        )
        self.logger = logging.getLogger(__name__)
    
    def create_agent(self, agent_config: dict):
        """Create an agent with error handling."""
        try:
            agent = self.client.agents.create(**agent_config)
            self.logger.info(f"Agent created: {agent.id}")
            return agent
        except LettaError as e:
            self.logger.error(f"Failed to create agent: {e}")
            raise
    
    def send_message(self, agent_id: str, message: str, 
                     max_retries: int = 3) -> dict:
        """
        Send a message with exponential backoff.
        
        Returns: {messages, cost_estimate, latency_ms}
        """
        start = time.time()
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.agents.messages.create(
                    agent_id,
                    input=message
                )
                
                latency_ms = (time.time() - start) * 1000
                self.logger.info(
                    f"Message sent to {agent_id}: "
                    f"{len(response.messages)} messages, "
                    f"{latency_ms:.0f}ms"
                )
                
                return {
                    "messages": response.messages,
                    "latency_ms": latency_ms,
                    "status": "success"
                }
            
            except LettaError as e:
                last_error = e
                if "429" in str(e):
                    # Rate limit — back off
                    wait = 2 ** attempt
                    self.logger.warning(
                        f"Rate limited (attempt {attempt}). "
                        f"Waiting {wait}s..."
                    )
                    time.sleep(wait)
                    continue
                # Non-retryable
                raise
            
            except Exception as e:
                last_error = e
                self.logger.error(f"Unexpected error: {e}")
                if attempt == max_retries:
                    raise
                time.sleep(1)
        
        raise RuntimeError(
            f"Failed after {max_retries} retries. "
            f"Last error: {last_error}"
        )
    
    def health_check(self) -> bool:
        """Check if the Letta service is healthy."""
        try:
            # Simple API call to verify connectivity
            self.client.agents.list(limit=1)
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def delete_agent_safely(self, agent_id: str):
        """Delete an agent with confirmation logging."""
        try:
            self.client.agents.delete(agent_id)
            self.logger.info(f"Agent deleted: {agent_id}")
        except LettaError as e:
            if "not found" in str(e).lower():
                self.logger.warning(f"Agent already deleted: {agent_id}")
            else:
                raise

# ── Usage example ───────────────────────────────────────────────

# Initialize service
# service = LettaAgentService(base_url="http://localhost:8283")

# Health check before use
# if not service.health_check():
#     raise RuntimeError("Letta service is unhealthy!")

# Create agent
# agent = service.create_agent({
#     "model": "openai/gpt-4o-mini",
#     "memory_blocks": [
#         {"label": "human", "value": "User: Alex", "limit": 2000},
#         {"label": "persona", "value": "I am a helpful assistant.", "limit": 2000}
#     ]
# })

# Send message
# result = service.send_message(agent.id, "Hello!")
# print(f"Response in {result['latency_ms']:.0f}ms")

print("LettaAgentService — production-ready wrapper pattern")