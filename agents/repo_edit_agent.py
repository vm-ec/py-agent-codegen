import json
import google.generativeai as genai

from config.settings import (
    settings
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
            self.model.generate_content(
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

        repo_context = {

            "base_package":
                base_package,

            "spring_boot":
                project_analysis.get(
                    "spring_boot"
                ),

            "has_lombok":
                project_analysis.get(
                    "has_lombok"
                ),

            "has_swagger":
                project_analysis.get(
                    "has_swagger"
                ),

            "has_mapstruct":
                project_analysis.get(
                    "has_mapstruct"
                ),

            "has_service_impl":
                project_analysis.get(
                    "has_service_impl"
                ),

            "has_generic_response":
                project_analysis.get(
                    "has_generic_response"
                ),

            "controllers":
                project_analysis.get(
                    "controllers",
                    []
                ),

            "repositories":
                project_analysis.get(
                    "repositories",
                    []
                ),

            "configs":
                project_analysis.get(
                    "configs",
                    []
                )
        }

        prompt_hub_context = (
            self.extract_prompt_hub_context()
        )

        return f"""
You are a senior Java Spring Boot architect.

You are modifying an EXISTING repository.

Your PRIMARY coding standards
come from Prompt Hub.

You MUST adapt generated code
to match the existing repository style.

=================================================
PROMPT HUB STANDARDS
=================================================

{prompt_hub_context}

=================================================
REPOSITORY CONTEXT
=================================================

{json.dumps(repo_context, indent=2)}

=================================================
TARGET DOMAIN
=================================================

{target_domain}

=================================================
USER REQUEST
=================================================

{user_prompt}

=================================================
VERY IMPORTANT RULES
=================================================

1. Follow repository style FIRST.

2. Reuse existing architecture.

3. Follow existing controller style.

4. Follow existing repository style.

5. Follow existing package structure.

6. DO NOT create DTOs unless repository uses DTOs.

7. DO NOT create ServiceImpl unless repo uses it.

8. DO NOT generate REST APIs if repo uses MVC.

9. Reuse existing patterns from repo.

10. Generate ONLY required files.

11. Return ONLY JSON.

12. Every file must contain FULL CODE.

=================================================
OUTPUT FORMAT
=================================================

[
  {{
    "file_name":
    "VehicleController.java",

    "package":
    "{base_package}.{target_domain.lower()}",

    "content":
    "full java code"
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