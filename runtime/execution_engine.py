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

        self.generated_files = []

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
        # Deprecated - kept for backward compatibility
        return []

    def build_batch_prompt(
            self,
            story_analysis
    ):

        # Get essential parent prompts only
        parent_prompts = self.prompt_hub.get("parent", {}).get("prompts", {})
        essential_parent = [
            "00_system",
            "03_exception",
            "06_logging"
        ]
        
        parent_context = "\n\n".join([
            f"### {k}\n{v}" 
            for k, v in parent_prompts.items() 
            if any(essential in k for essential in essential_parent)
        ])

        child_instructions = (
            self.prompt_hub[
                "child"
            ].get(
                "instructions",
                ""
            )
        )

        return f"""
You are a senior enterprise Java 21 Spring Boot 3 engineer.

You MUST follow the Prompt Hub standards strictly.

You will generate a COMPLETE Spring Boot project in ONE response.

=================================================
PROMPT HUB STANDARDS
=================================================

{parent_context}

=================================================
CHILD INSTRUCTIONS
=================================================

{child_instructions}

=================================================
STORY ANALYSIS
=================================================

{json.dumps(story_analysis, indent=2)}

=================================================
REQUIRED FILES TO GENERATE
=================================================

You MUST generate ALL of the following for EACH entity in the story:

1. Model/Entity - JPA entity with Lombok annotations
2. Repository - Spring Data JPA repository interface
3. Service - Service interface and implementation
4. Controller - REST controller with CRUD endpoints
5. DTO - Request and Response DTOs
6. Mapper - MapStruct mapper interface
7. Exception - Custom exception classes
8. Tests - Integration tests for controller
9. Config - Application configuration classes

=================================================
STRICT REQUIREMENTS
=================================================

- Use Java 21
- Use Spring Boot 3
- Use Lombok for all classes
- Use MapStruct for entity-DTO mapping
- Use JUnit 5 + Mockito for tests
- Follow REST best practices
- Include proper validation
- Include proper error handling
- Generate ONLY what the story requires (no extra features)
- Each file must be COMPLETE and COMPILABLE

=================================================
CRITICAL: FOLDER FIELD RULES
=================================================

You MUST use EXACTLY these folder values based on file type:

- Entity/Model classes (e.g., Claim.java, Product.java) → "folder": "model"
- Repository interfaces (e.g., ClaimRepository.java) → "folder": "repository"
- Service interfaces (e.g., ClaimService.java) → "folder": "service"
- Service implementations (e.g., ClaimServiceImpl.java) → "folder": "service"
- Controller classes (e.g., ClaimController.java) → "folder": "controller"
- Request DTOs (e.g., ClaimRequest.java) → "folder": "dto"
- Response DTOs (e.g., ClaimResponse.java) → "folder": "dto"
- Mapper interfaces (e.g., ClaimMapper.java) → "folder": "mapper"
- Exception classes (e.g., ClaimNotFoundException.java) → "folder": "exception"
- Config classes (e.g., SwaggerConfig.java) → "folder": "config"
- Test classes (e.g., ClaimControllerTest.java) → "folder": "integration-tests"
- Root files (pom.xml, application.yml) → "folder": ""

DO NOT use any other folder values. DO NOT use full package paths.

=================================================
OUTPUT FORMAT - RETURN EXACT JSON STRUCTURE
=================================================

IMPORTANT: The "folder" field must be ONLY the folder type, not full path.

Valid folder values: "model", "repository", "service", "controller", "dto", "mapper", "exception", "config", "integration-tests"

For root files like pom.xml, use empty string: "folder": ""

{{
  "files": [
    {{
      "file_name": "Claim.java",
      "folder": "model",
      "content": "package com.example.project.model;\n\nimport lombok.Data;\n..."
    }},
    {{
      "file_name": "ClaimRepository.java",
      "folder": "repository",
      "content": "package com.example.project.repository;\n..."
    }},
    {{
      "file_name": "ClaimService.java",
      "folder": "service",
      "content": "package com.example.project.service;\n..."
    }},
    {{
      "file_name": "ClaimController.java",
      "folder": "controller",
      "content": "package com.example.project.controller;\n..."
    }},
    {{
      "file_name": "pom.xml",
      "folder": "",
      "content": "<?xml version=\"1.0\"...>"
    }}
  ]
}}

Generate ALL files now. Return ONLY valid JSON. NO markdown. NO explanations.
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

    def execute_batch(
            self,
            story_analysis
    ):

        final_prompt = (
            self.build_batch_prompt(
                story_analysis
            )
        )

        print("[ExecutionEngine] Generating all files in batch mode...")

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
                    f"Empty response - possible quota exhaustion"
                )
                return []

        except Exception as e:

            error_msg = str(e)

            if "429" in error_msg or "quota" in error_msg.lower():
                print(
                    f"[ExecutionEngine] "
                    f"API quota exhausted"
                )
            elif "400" in error_msg or "too large" in error_msg.lower():
                print(
                    f"[ExecutionEngine] "
                    f"Prompt too large"
                )
            else:
                print(
                    f"[ExecutionEngine] "
                    f"Gemini API error: {error_msg}"
                )

            return []

        cleaned_response = (
            self.clean_response(
                response.text
            )
        )

        print("\n========== BATCH AI RESPONSE ==========\n")
        print(cleaned_response[:500])  # Print first 500 chars
        print("\n=======================================\n")

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

            print(f"[ExecutionEngine] Generated {len(files)} files in batch")

            return files

        except Exception as parse_error:

            print(f"[ExecutionEngine] JSON parse failed: {parse_error}")

            # Try strict=False to handle unescaped control characters
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

                # Last resort — use regex
                return self.extract_files_manually(
                    cleaned_response
                )

    def execute(
            self,
            story_analysis
    ):

        # Batch generation - all files in one call
        all_files = self.execute_batch(
            story_analysis
        )

        # Group files by folder for compatibility
        execution_result = {
            "model": [],
            "dto": [],
            "mapper": [],
            "repository": [],
            "service": [],
            "exception": [],
            "controller": [],
            "integration-tests": [],
            "config": []
        }

        for file in all_files:
            folder = file.get("folder", "misc")
            if folder in execution_result:
                execution_result[folder].append(file)
            else:
                # Handle misc files
                if "misc" not in execution_result:
                    execution_result["misc"] = []
                execution_result["misc"].append(file)

        return execution_result