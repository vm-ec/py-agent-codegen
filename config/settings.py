import os
from dotenv import load_dotenv

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