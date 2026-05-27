import json
import re

import google.generativeai as genai

from config.settings import (
    settings, generate_with_retry
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

        response_text = response_text.strip()

        # Remove ```json ... ``` or ``` ... ```
        response_text = re.sub(
            r"^```[a-zA-Z]*\s*",
            "",
            response_text,
            flags=re.IGNORECASE
        )

        response_text = re.sub(
            r"```\s*$",
            "",
            response_text
        )

        return response_text.strip()

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

    def extract_files_manually(
            self,
            response_text
    ):

        files = []

        # Match each file block by file_name
        file_name_pattern = re.findall(
            r'"file_name"\s*:\s*"([^"]+)"',
            response_text
        )

        folder_pattern = re.findall(
            r'"folder"\s*:\s*"([^"]+)"',
            response_text
        )

        # Extract content between "content": " and next "
        content_pattern = re.findall(
            r'"content"\s*:\s*"(.*?)"(?=\s*[,}])',
            response_text,
            re.DOTALL
        )

        for i, file_name in enumerate(
                file_name_pattern
        ):

            folder = (
                folder_pattern[i]
                if i < len(folder_pattern)
                else "misc"
            )

            content = (
                content_pattern[i]
                .replace("\\n", "\n")
                .replace("\\t", "\t")
                .replace("\\\"", "\"")
                if i < len(content_pattern)
                else ""
            )

            files.append(
                {
                    "file_name": file_name,
                    "folder": folder,
                    "content": content
                }
            )

        self.generated_files.extend(files)

        return files

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

        try:

            response = (
                generate_with_retry(
                    self.model,
                    final_prompt
                )
            )

            if not response or not response.text:
                print(
                    f"[ExecutionEngine] "
                    f"Empty response for step: {step_name} "
                    f"- possible quota exhaustion or prompt too large"
                )
                return []

        except Exception as e:

            error_msg = str(e)

            if "429" in error_msg or "quota" in error_msg.lower():
                print(
                    f"[ExecutionEngine] "
                    f"API quota exhausted for step: {step_name}"
                )
            elif "400" in error_msg or "too large" in error_msg.lower():
                print(
                    f"[ExecutionEngine] "
                    f"Prompt too large for step: {step_name}"
                )
            else:
                print(
                    f"[ExecutionEngine] "
                    f"Gemini API error for step {step_name}: {error_msg}"
                )

            return []

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

            # Try strict=False to handle
            # unescaped control characters
            try:

                parsed_response = json.loads(
                    cleaned_response,
                    strict=False
                )

                files = parsed_response.get(
                    "files", []
                )

                self.generated_files.extend(files)

                return files

            except Exception:

                # Last resort — use regex to
                # extract each file block manually
                return self.extract_files_manually(
                    cleaned_response
                )

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