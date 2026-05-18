import os
import re


class FileWriter:

    def __init__(
            self,
            project_path,
            project_name
    ):

        self.project_path = (
            project_path
        )

        self.project_name = (
            project_name.lower()
        )

    def sanitize_folder(
            self,
            folder
    ):

        if not folder:
            return "misc"

        folder = folder.replace(
            "\\",
            "/"
        )

        folder = folder.lower()

        mappings = {
            "controller":
                "controller",

            "service":
                "service",

            "repository":
                "repository",

            "model":
                "model",

            "entity":
                "model",

            "dto":
                "dto",

            "mapper":
                "mapper",

            "exception":
                "exception",

            "config":
                "config",

            "integration":
                "integration-tests",

            "test":
                "integration-tests"
        }

        for key, value in (
                mappings.items()
        ):

            if key in folder:
                return value

        return "misc"

    def get_folder_path(
            self,
            folder
    ):

        clean_folder = (
            self.sanitize_folder(
                folder
            )
        )

        if (
                clean_folder
                ==
                "integration-tests"
        ):

            return os.path.join(
                self.project_path,
                "src/test/java/com/example",
                self.project_name,
                "integration"
            )

        return os.path.join(
            self.project_path,
            "src/main/java/com/example",
            self.project_name,
            clean_folder
        )

    def sanitize_file_name(
            self,
            file_name
    ):

        if not file_name:
            return "Unknown.java"

        file_name = (
            file_name
            .replace("\\", "/")
            .split("/")[-1]
        )

        return file_name

    def write_file(
            self,
            generated_file
    ):

        try:

            file_name = (
                self.sanitize_file_name(
                    generated_file.get(
                        "file_name"
                    )
                )
            )

            folder = (
                generated_file.get(
                    "folder"
                )
            )

            content = (
                generated_file.get(
                    "content"
                )
            )

            folder_path = (
                self.get_folder_path(
                    folder
                )
            )

            os.makedirs(
                folder_path,
                exist_ok=True
            )

            file_path = (
                os.path.join(
                    folder_path,
                    file_name
                )
            )

            with open(
                    file_path,
                    "w",
                    encoding="utf-8"
            ) as file:

                file.write(
                    content
                )

            return {
                "status":
                    "success",

                "file":
                    file_path
            }

        except Exception as e:

            return {
                "status":
                    "failed",

                "error":
                    str(e)
            }

    def write_generated_files(
            self,
            execution_result
    ):

        write_results = []

        for _, files in (
                execution_result
                .items()
        ):

            if not isinstance(
                    files,
                    list
            ):
                continue

            for generated_file in files:

                if (
                        "file_name"
                        not in generated_file
                ):
                    continue

                result = (
                    self.write_file(
                        generated_file
                    )
                )

                write_results.append(
                    result
                )

        return write_results