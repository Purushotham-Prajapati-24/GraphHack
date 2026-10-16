"""
title: Approve action (spike)
"""

# Spike Action: proves an Open WebUI Action button can approve a ledgered action by calling the brain over HTTP
# with the clicking user's server-side identity.

import re

import httpx
from pydantic import BaseModel, Field

ACTION_KEY = re.compile(r"action-key:\s*`([A-Za-z0-9:_\-]+)`")


class Action:
    class Valves(BaseModel):
        BRAIN_URL: str = Field(default="http://host.docker.internal:8766")
        SERVICE_SECRET: str = Field(default="")

    def __init__(self):
        self.valves = self.Valves()

    async def action(self, body: dict, __user__: dict = None, __event_emitter__=None):
        messages = body.get("messages", [])
        target = next((m for m in messages if m.get("id") == body.get("id")), messages[-1] if messages else {})
        match = ACTION_KEY.search(target.get("content", ""))
        if not match:
            return {"status": "no_action_key"}

        # __user__ comes from Open WebUI's verified session, never from the request body.
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{self.valves.BRAIN_URL}/actions/{match.group(1)}/approve",
                json={"owui_user_id": __user__["id"], "chat_id": body.get("chat_id"), "message_id": body.get("id")},
                headers={"X-Service-Secret": self.valves.SERVICE_SECRET},
            )
        result = r.json()
        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"Action {result.get('status')}", "done": True}})
        return result
