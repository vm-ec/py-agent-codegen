import json
import re

import google.generativeai as genai

from config.settings import (
    settings
)


class ExecutionEngine:

    def __init__(
            self,
            prompt_hub
    ):

        self.prompt_hub = (
            prompt_hub
        )

        genai.configure(
            api_key=settings
            .GEMINI_API_KEY
        )

        self.model = (
            genai.GenerativeModel(
                settings.MODEL_NAME
            )
        )

        self.execution_order = [
            "model",
            "dto",
            "mapper",
            "repository",
            "service",
            "exception",
            "controller",
            "integration-tests",
            "config"
        ]

        self.generated_files = []

        self.step_dependencies = {
            "model": [],

            "dto": [
                "model"
            ],

            "mapper": [
                "model",
                "dto"
            ],

            "repository": [
                "model"
            ],

            "service": [
                "model",
                "dto",
                "mapper",
                "repository",
                "exception"
            ],

            "exception": [
                "model"
            ],

            "controller": [
                "dto",
                "service",
                "exception"
            ],

            "integration-tests": [
                "controller",
                "service",
                "repository"
            ],

            "config": [
                "controller",
                "service"
            ]
        }

    def clean_response(
            self,
            response_text
    ):

        response_text = (
            response_text.strip()
        )

        response_text = re.sub(
            r"^```json",
            "",
            response_text,
            flags=re.IGNORECASE
        )

        response_text = re.sub(
            r"```$",
            "",
            response_text
        )

        return (
            response_text
            .strip()
        )

    def get_dependency_files(
            self,
            step_name
    ):

        required_steps = (
            self.step_dependencies
            .get(
                step_name,
                []
            )
        )

        dependency_files = []

        for generated_file in (
                self.generated_files
        ):

            folder = (
                generated_file
                .get(
                    "folder",
                    ""
                )
            )

            if (
                    folder
                    in required_steps
            ):
                dependency_files.append(
                    generated_file
                )

        return dependency_files

    def build_prompt(
            self,
            prompt_name,
            prompt_content,
            story_analysis
    ):

        parent_context = "\n".join(
            self.prompt_hub[
                "parent"
            ][
                "prompts"
            ].values()
        )

        child_instructions = (
            self.prompt_hub[
                "child"
            ].get(
                "instructions",
                ""
            )
        )

        dependency_files = (
            self.get_dependency_files(
                prompt_name
            )
        )

        dependency_context = (
            json.dumps(
                dependency_files,
                indent=2
            )
        )

        return f"""
You are a senior enterprise
Java 21 Spring Boot engineer.

You MUST follow the
Prompt Hub strictly.

You MUST generate
ONLY what is required
for the current step.

Do NOT assume extra APIs.
Do NOT add extra methods.
Do NOT hallucinate.

PARENT PROMPT HUB:
{parent_context}

CHILD INSTRUCTIONS:
{child_instructions}

CURRENT STEP:
{prompt_name}

STEP PROMPT:
{prompt_content}

STORY ANALYSIS:
{json.dumps(
    story_analysis,
    indent=2
)}

DEPENDENCY FILES:
{dependency_context}

STRICT RULES:

1. Generate ONLY
the current step.

2. Follow Java 21.

3. Follow Spring Boot 3.

4. Use Lombok.

5. Use MapStruct.

6. Use Mockito.

7. Use JUnit 5.

8. Return COMPLETE FILES.

9. NO markdown.

10. NO ```json

11. Generate ONLY
what story requires.

Return STRICT JSON:

{{
  "files": [
    {{
      "file_name":
      "StudentService.java",

      "folder":
      "service",

      "content":
      "full java code"
    }}
  ]
}}
"""

    def execute_step(
            self,
            step_name,
            story_analysis
    ):

        child_prompts = (
            self.prompt_hub[
                "child"
            ][
                "prompts"
            ]
        )

        if (
                step_name
                not in child_prompts
        ):
            return []

        prompt_content = (
            child_prompts[
                step_name
            ]
        )

        final_prompt = (
            self.build_prompt(
                step_name,
                prompt_content,
                story_analysis
            )
        )

        response = (
            self.model
            .generate_content(
                final_prompt
            )
        )

        cleaned_response = (
            self.clean_response(
                response.text
            )
        )

        try:

            parsed_response = (
                json.loads(
                    cleaned_response
                )
            )

            files = (
                parsed_response
                .get(
                    "files",
                    []
                )
            )

            self.generated_files.extend(
                files
            )

            return files

        except Exception:

            return [
                {
                    "error":
                    "JSON Parse Failed",

                    "raw_response":
                    cleaned_response
                }
            ]

    def execute(
            self,
            story_analysis
    ):

        execution_result = {}

        for step in (
                self.execution_order
        ):

            step_result = (
                self.execute_step(
                    step,
                    story_analysis
                )
            )

            execution_result[
                step
            ] = step_result

        return execution_result