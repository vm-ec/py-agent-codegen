import os


class PromptLoader:

    def __init__(
            self,
            prompt_hub_path
    ):

        self.prompt_hub_path = (
            prompt_hub_path
        )

    def load_file(
            self,
            file_path
    ):

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as file:

                return file.read()

        except Exception:

            return ""

    def load_prompt_folder(
            self,
            folder_path
    ):

        prompt_data = {
            "readme": "",
            "instructions": "",
            "input": "",
            "prompts": {}
        }

        if not os.path.exists(
                folder_path
        ):
            return prompt_data

        for root, _, files in os.walk(
                folder_path
        ):

            for file in files:

                file_path = (
                    os.path.join(
                        root,
                        file
                    )
                )

                content = (
                    self.load_file(
                        file_path
                    )
                )

                lower_name = (
                    file.lower()
                )

                if (
                        "readme"
                        in lower_name
                ):

                    prompt_data[
                        "readme"
                    ] = content

                elif (
                        "instruction"
                        in lower_name
                ):

                    prompt_data[
                        "instructions"
                    ] = content

                elif (
                        "input"
                        in lower_name
                ):

                    prompt_data[
                        "input"
                    ] = content

                elif (
                        file.endswith(
                            ".md"
                        )
                        or
                        file.endswith(
                            ".prompt.md"
                        )
                ):

                    prompt_name = (
                        file
                        .replace(
                            ".prompt.md",
                            ""
                        )
                        .replace(
                            ".md",
                            ""
                        )
                    )

                    prompt_data[
                        "prompts"
                    ][
                        prompt_name
                    ] = content

        return prompt_data

    def load_prompt_hub(
            self
    ):

        github_path = os.path.join(
            self.prompt_hub_path,
            ".github"
        )

        parent_path = os.path.join(
            github_path,
            "parent"
        )

        child_path = os.path.join(
            github_path,
            "child"
        )

        parent_data = (
            self
            .load_prompt_folder(
                parent_path
            )
        )

        child_data = (
            self
            .load_prompt_folder(
                child_path
            )
        )

        return {
            "parent":
            parent_data,

            "child":
            child_data
        }