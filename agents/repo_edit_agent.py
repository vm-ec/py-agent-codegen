import json
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

            # -----------------------------
            # First Attempt
            # -----------------------------

            return json.loads(
                cleaned_response
            )

        except Exception:

            try:

                # -----------------------------
                # Safe Fallback Parse
                # -----------------------------

                safe_response = (
                    cleaned_response
                    .replace(
                        "\r",
                        ""
                    )
                    .replace(
                        "\t",
                        "    "
                    )
                )

                return json.loads(
                    safe_response,
                    strict=False
                )

            except Exception as e:

                return [

                    {
                        "status":
                            "failed",

                        "error":
                            str(e),

                        "raw":
                            raw_text
                    }
                ]

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
            "controllers": project_analysis.get("controllers", []),
            "repositories": project_analysis.get("repositories", [])
        }

        prompt_hub_context = (
            self.extract_prompt_hub_context()
        )

        return f"""
You are a senior Java Spring Boot architect.

You are adding a NEW MODULE to an EXISTING repository.

Your coding standards come from the Prompt Hub below.
You MUST adapt the generated code to match the existing repository style.

=================================================
PROMPT HUB STANDARDS
=================================================

{prompt_hub_context}

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
    # Extract Prompt Hub Context
    # ----------------------------------

    def extract_prompt_hub_context(
            self
    ):

        context = []

        try:

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

            child_prompts = (
                self.prompt_hub
                .get(
                    "child",
                    {}
                )
                .get(
                    "prompts",
                    {}
                )
            )

            enhancement_prompts = (
                self.prompt_hub
                .get(
                    "enhancement",
                    {}
                )
                .get(
                    "prompts",
                    {}
                )
            )

            for (
                    prompt_name,
                    prompt_content
            ) in (
                    parent_prompts.items()
            ):

                context.append(
                    f"\n### "
                    f"{prompt_name}\n"
                    f"{prompt_content}"
                )

            for (
                    prompt_name,
                    prompt_content
            ) in (
                    child_prompts.items()
            ):

                context.append(
                    f"\n### "
                    f"{prompt_name}\n"
                    f"{prompt_content}"
                )

            for (
                    prompt_name,
                    prompt_content
            ) in (
                    enhancement_prompts.items()
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

        return text