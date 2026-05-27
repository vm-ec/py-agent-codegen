import json
import re

import google.generativeai as genai

from config.settings import (
    settings, generate_with_retry
)


class StoryAnalyzer:

    def __init__(self):

        genai.configure(
            api_key=settings
            .GEMINI_API_KEY
        )

        self.model = (
            genai.GenerativeModel(
                settings.MODEL_NAME
            )
        )

    def clean_json_response(
            self,
            response_text
    ):

        response_text = (
            response_text.strip()
        )

        # Remove ```json
        response_text = re.sub(
            r"^```json",
            "",
            response_text,
            flags=re.IGNORECASE
        )

        # Remove ```
        response_text = re.sub(
            r"```$",
            "",
            response_text
        )

        response_text = (
            response_text.strip()
        )

        return response_text

    def analyze_story(
            self,
            story
    ):

        prompt = f"""
You are a senior Java Spring Boot architect.

Analyze the user story.

Extract the following:

1. project_name
2. domain
3. entities
4. APIs needed
5. features
6. modules
7. whether CRUD is needed

Return STRICT JSON only.

Do NOT return markdown.

Do NOT wrap in ```json.

Story:
{story}
"""

        response = (
            generate_with_retry(
                self.model,
                prompt
            )
        )

        cleaned_response = (
            self.clean_json_response(
                response.text
            )
        )

        try:

            parsed_json = json.loads(
                cleaned_response
            )

            return parsed_json

        except Exception:

            return {
                "raw_response":
                cleaned_response
            }