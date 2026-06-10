import json
import html
import re
import google.generativeai as genai

from config.settings import (
    settings, generate_with_retry
)


class RepoEditAgent:

    def __init__(
            self,
            prompt_hub
    ):

        self.prompt_hub = (
            prompt_hub
        )

        genai.configure(
            api_key=
            settings.GEMINI_API_KEY
        )

        self.model = (
            genai.GenerativeModel(
                settings.MODEL_NAME
            )
        )

    # ----------------------------------
    # Generate Repo Changes
    # ----------------------------------

    def generate_repo_changes(
            self,
            user_prompt,
            project_analysis,
            impact_analysis
    ):

        prompt = (
            self.build_prompt(
                user_prompt,
                project_analysis,
                impact_analysis
            )
        )

        response = (
            generate_with_retry(
                self.model,
                prompt
            )
        )

        raw_text = response.text

        print(
            "\n========== RAW AI RESPONSE ==========\n"
        )

        print(raw_text)

        print(
            "\n=====================================\n"
        )

        cleaned_response = (
            self.clean_json_response(
                raw_text
            )
        )

        try:
            return json.loads(cleaned_response)
        except Exception:
            try:
                return json.loads(cleaned_response, strict=False)
            except Exception:
                return self.extract_files_by_regex(cleaned_response)

    # ----------------------------------
    # Regex Fallback Extractor
    # ----------------------------------

    def extract_files_by_regex(self, text):

        files = []

        file_names = re.findall(r'"file_name"\s*:\s*"([^"]+)"', text)
        packages = re.findall(r'"package"\s*:\s*"([^"]+)"', text)
        contents = re.findall(r'"content"\s*:\s*"(.*?)"(?=\s*[,}])', text, re.DOTALL)

        for i, file_name in enumerate(file_names):
            content = (
                contents[i]
                .replace("\\n", "\n")
                .replace("\\t", "\t")
                .replace("\\\"", "\"")
                if i < len(contents) else ""
            )
            files.append({
                "file_name": file_name,
                "package": packages[i] if i < len(packages) else "",
                "content": content
            })

        if not files:
            return [{"status": "failed", "error": "Could not parse AI response", "raw": text}]

        return files

    # ----------------------------------
    # Build Prompt
    # ----------------------------------

    def build_prompt(
            self,
            user_prompt,
            project_analysis,
            impact_analysis
    ):

        base_package = (
            project_analysis.get(
                "base_package",
                ""
            )
        )

        target_domain = (
            impact_analysis.get(
                "target_domain",
                "common"
            )
        )

        domain_lower = target_domain.lower()
        domain_package = f"{base_package}.{domain_lower}"

        has_service_impl = project_analysis.get(
            "has_service_impl", False
        )

        has_dto = project_analysis.get(
            "has_dto", False
        )

        has_mapstruct = project_analysis.get(
            "has_mapstruct", False
        )

        # Build mandatory files list
        mandatory_files = [
            f"{target_domain}.java"
        ]

        if has_dto:
            mandatory_files.append(
                f"{target_domain}Request.java"
            )
            mandatory_files.append(
                f"{target_domain}Response.java"
            )

        if has_mapstruct:
            mandatory_files.append(
                f"{target_domain}Mapper.java"
            )

        mandatory_files.append(
            f"{target_domain}Repository.java"
        )

        mandatory_files.append(
            f"{target_domain}Service.java"
        )

        if has_service_impl:
            mandatory_files.append(
                f"{target_domain}ServiceImpl.java"
            )

        # Exception always generated
        mandatory_files.append(
            f"{target_domain}NotFoundException.java"
        )

        mandatory_files.append(
            f"{target_domain}Controller.java"
        )

        mandatory_files.append(
            f"{target_domain}ControllerTests.java"
        )

        mandatory_files_str = "\n".join(
            [f"  - {f}" for f in mandatory_files]
        )

        repo_context = {
            "base_package": base_package,
            "domain_package": domain_package,
            "spring_boot": project_analysis.get("spring_boot"),
            "has_lombok": project_analysis.get("has_lombok"),
            "has_swagger": project_analysis.get("has_swagger"),
            "has_mapstruct": has_mapstruct,
            "has_dto": has_dto,
            "has_service_impl": has_service_impl,
            "has_generic_response": project_analysis.get("has_generic_response"),
            "controller_count": len(project_analysis.get("controllers", [])),
            "repository_count": len(project_analysis.get("repositories", []))
        }

        prompt_hub_context = (
            self.extract_prompt_hub_context()
        )

        # Extract example files from repo
        example_files_context = (
            self.build_example_files_context(
                project_analysis
            )
        )

        return f"""
You are a senior Java Spring Boot architect.

You are adding a NEW MODULE to an EXISTING repository.

Your coding standards come from the Prompt Hub below.
You MUST adapt the generated code to match the EXAMPLE FILES from the repository.

=================================================
PROMPT HUB STANDARDS (Essential Rules Only)
=================================================

{prompt_hub_context}

=================================================
EXAMPLE FILES FROM REPOSITORY (Follow These Patterns EXACTLY)
=================================================

{example_files_context}

=================================================
REPOSITORY CONTEXT
=================================================

{json.dumps(repo_context, indent=2)}

=================================================
USER REQUEST
=================================================

{user_prompt}

=================================================
TARGET DOMAIN: {target_domain}
TARGET PACKAGE: {domain_package}
=================================================

=================================================
MANDATORY FILES — YOU MUST GENERATE ALL OF THESE
=================================================

{mandatory_files_str}

Do NOT skip any of the above files.
Do NOT generate partial implementations.
Every file MUST contain COMPLETE, COMPILABLE Java code.

=================================================
STRICT RULES
=================================================

1. Generate ALL mandatory files listed above — no exceptions.
2. Follow the existing repository style exactly.
3. Use the same patterns as existing controllers, services, repositories.
4. All files MUST be in package: {domain_package}
5. If has_lombok is true — use Lombok annotations.
6. If has_service_impl is true — generate both Service interface and ServiceImpl.
7. If has_swagger is true — add Swagger annotations to controller.
8. Controller MUST follow existing MVC or REST style of the repo.
9. Repository MUST follow existing repository pattern of the repo.
10. Tests MUST use MockMvc and Mockito following existing test patterns.
11. Return ONLY a valid JSON array.
12. NO markdown, NO explanations outside JSON.

=================================================
OUTPUT FORMAT — RETURN EXACTLY THIS STRUCTURE
=================================================

[
  {{
    "file_name": "{target_domain}.java",
    "package": "{domain_package}",
    "content": "full java code here"
  }},
  {{
    "file_name": "{target_domain}Repository.java",
    "package": "{domain_package}",
    "content": "full java code here"
  }},
  {{
    "file_name": "{target_domain}Service.java",
    "package": "{domain_package}",
    "content": "full java code here"
  }},
  {{
    "file_name": "{target_domain}Controller.java",
    "package": "{domain_package}",
    "content": "full java code here"
  }},
  {{
    "file_name": "{target_domain}ControllerTests.java",
    "package": "{domain_package}",
    "content": "full java code here"
  }}
]
"""

    # ----------------------------------
    # Build Example Files Context
    # ----------------------------------

    def build_example_files_context(
            self,
            project_analysis
    ):

        context = []
        example_files = project_analysis.get("example_files", {})

        if "controller" in example_files:
            context.append(
                f"### EXAMPLE CONTROLLER\n```java\n{example_files['controller']}\n```"
            )

        if "service" in example_files:
            context.append(
                f"### EXAMPLE SERVICE\n```java\n{example_files['service']}\n```"
            )

        if "repository" in example_files:
            context.append(
                f"### EXAMPLE REPOSITORY\n```java\n{example_files['repository']}\n```"
            )

        if not context:
            return "No example files available. Follow Spring Boot best practices."

        return "\n\n".join(context)

    # ----------------------------------
    # Extract Prompt Hub Context
    # ----------------------------------

    def extract_prompt_hub_context(
            self
    ):

        context = []

        try:

            # Only include critical parent prompts to reduce tokens
            parent_prompts = (
                self.prompt_hub
                .get(
                    "parent",
                    {}
                )
                .get(
                    "prompts",
                    {}
                )
            )

            # Filter only essential parent prompts to reduce token usage
            essential_parent = [
                "00_system",
                "03_exception",
                "06_logging"
            ]

            filtered_parent = {
                k: v for k, v in parent_prompts.items()
                if any(essential in k for essential in essential_parent)
            }

            # Skip child prompts to save tokens - rely on repo analysis instead

            # Only include filtered essential prompts
            for (
                    prompt_name,
                    prompt_content
            ) in (
                    filtered_parent.items()
            ):

                context.append(
                    f"\n### "
                    f"{prompt_name}\n"
                    f"{prompt_content}"
                )

        except Exception:

            pass

        return "\n".join(
            context
        )

    # ----------------------------------
    # Clean JSON
    # ----------------------------------

    def clean_json_response(
            self,
            text
    ):

        text = (
            text
            .replace(
                "```json",
                ""
            )
            .replace(
                "```",
                ""
            )
            .strip()
        )

        # Fix HTML entities first
        text = html.unescape(text)

        return text