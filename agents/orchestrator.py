import json
import google.generativeai as genai

from config.settings import settings, generate_with_retry


class Orchestrator:

    def __init__(self, prompt_hub):

        self.prompt_hub = prompt_hub

        genai.configure(
            api_key=settings.GEMINI_API_KEY
        )

        self.model = genai.GenerativeModel(
            settings.MODEL_NAME
        )

    # ----------------------------------
    # Decide Action
    # ----------------------------------

    def decide_action(
            self,
            user_message,
            conversation_history,
            repo_url,
            session_context
    ):

        history_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in conversation_history[-6:]
            if msg.get("type") != "json"
        ])

        context_text = json.dumps(
            session_context,
            indent=2
        )

        prompt = f"""
You are an intelligent agent orchestrator for a
Java Spring Boot Code Generator Agent.

Your job is to analyze the user message and
conversation history, then decide what action
to take.

---

AVAILABLE ACTIONS:

1. "generate_project"
   - User wants to create a NEW Spring Boot project
   - No repo URL provided
   - User describes a new system or application

2. "edit_project"
   - User wants to modify an EXISTING GitHub repo
   - Repo URL is provided
   - User describes changes, new features, or modifications

3. "push_code"
   - Code was already generated in this session
   - User wants to push/commit/raise PR
   - Keywords: push, commit, raise PR, create PR

4. "explain"
   - User asks a question about generated code
   - User wants explanation of what was done
   - Keywords: explain, what, why, how, describe

5. "clarify"
   - User message is unclear or missing information
   - Need more details before proceeding

---

CURRENT SESSION CONTEXT:
{context_text}

REPO URL PROVIDED: {repo_url if repo_url else "None"}

CONVERSATION HISTORY:
{history_text}

USER MESSAGE:
{user_message}

---

Respond with STRICT JSON only:

{{
  "action": "generate_project" | "edit_project" | "push_code" | "explain" | "clarify",
  "reason": "brief reason for this decision",
  "response_message": "conversational response to show user before executing action",
  "needs_clarification": "question to ask user if action is clarify, else empty string"
}}
"""

        try:

            response = generate_with_retry(
                self.model,
                prompt
            )

            text = (
                response.text
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

            return json.loads(text)

        except Exception as e:

            # Default fallback based on repo_url
            if repo_url and repo_url.strip():
                action = "edit_project"
            else:
                action = "generate_project"

            return {
                "action": action,
                "reason": "fallback decision",
                "response_message": "Let me work on that for you...",
                "needs_clarification": ""
            }
