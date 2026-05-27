import os
import time
from dotenv import load_dotenv
import google.generativeai as genai

# Only load .env in local development, not in production
if os.getenv("RENDER") is None:
    load_dotenv()


class Settings:

    GEMINI_API_KEY = os.getenv(
        "GEMINI_API_KEY"
    )

    PROMPT_HUB_REPO = os.getenv(
        "PROMPT_HUB_REPO"
    )

    MODEL_NAME = os.getenv(
        "MODEL_NAME",
        "gemini-2.0-flash"
    )

    GITHUB1_TOKEN = os.getenv(
        "GITHUB1_TOKEN"
    )

    GITHUB1_USERNAME = os.getenv(
        "GITHUB1_USERNAME"
    )

    PROMPT_HUB_PATH = (
        "workspace/prompt_hub"
    )

    LINKED_PROJECTS_PATH = (
        "workspace/linked_projects"
    )

    GENERATED_PROJECTS_PATH = (
        "generated_projects"
    )

    @staticmethod
    def print_key():

        print("========== ENVIRONMENT DEBUG ==========")
        print(f"GEMINI_API_KEY exists: {bool(os.getenv('GEMINI_API_KEY'))}")
        print(f"MODEL_NAME: {os.getenv('MODEL_NAME', 'NOT SET')}")
        print(f"PROMPT_HUB_REPO: {os.getenv('PROMPT_HUB_REPO', 'NOT SET')}")
        print("=======================================")

        if os.getenv(
                "GEMINI_API_KEY"
        ):

            key = os.getenv(
                "GEMINI_API_KEY"
            )

            print(
                f"Loaded Key: "
                f"{key[:8]}..."
            )

        else:

            print(
                "No Gemini key found"
            )


settings = Settings()

settings.print_key()


def generate_with_retry(model, prompt, max_retries=3):
    """Generate content with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return model.generate_content(prompt)
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 10
                    print(f"Quota exceeded. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Quota exceeded after {max_retries} retries. Switch to gemini-1.5-flash or upgrade to paid tier.") from e
            else:
                raise