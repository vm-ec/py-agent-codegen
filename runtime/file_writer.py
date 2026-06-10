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

    def detect_folder_from_filename(
            self,
            file_name
    ):
        """
        Auto-detect correct folder based on file name patterns.
        This overrides incorrect AI folder assignments.
        """
        if not file_name:
            return None

        lower_name = file_name.lower()

        # Controller files
        if "controller" in lower_name and "test" not in lower_name:
            return "controller"

        # Repository files
        if "repository" in lower_name:
            return "repository"

        # Service files (not ServiceImpl)
        if "service" in lower_name:
            return "service"

        # Mapper files
        if "mapper" in lower_name:
            return "mapper"

        # DTO files (Request/Response)
        if "request" in lower_name or "response" in lower_name or "dto" in lower_name:
            return "dto"

        # Exception files
        if "exception" in lower_name or lower_name.endswith("notfoundexception.java"):
            return "exception"

        # Config files
        if "config" in lower_name or "configuration" in lower_name:
            return "config"

        # Test files
        if "test" in lower_name:
            return "integration-tests"

        # Application main class
        if "application.java" in lower_name:
            return None  # Root level

        # Entity/Model files - if ends with .java and no other keywords
        # This catches files like Claim.java, Product.java, Employee.java
        if (
            lower_name.endswith(".java") 
            and "controller" not in lower_name
            and "service" not in lower_name
            and "repository" not in lower_name
            and "mapper" not in lower_name
            and "exception" not in lower_name
            and "config" not in lower_name
            and "request" not in lower_name
            and "response" not in lower_name
            and "test" not in lower_name
            and "application" not in lower_name
        ):
            return "model"

        return None

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

            # Auto-detect folder from file name if AI gave wrong folder
            detected_folder = self.detect_folder_from_filename(file_name)
            if detected_folder:
                folder = detected_folder
                print(f"[FileWriter] Auto-corrected folder for {file_name}: '{generated_file.get('folder')}' → '{folder}'")

            # Handle root files (pom.xml, application.yml, etc.)
            if not folder or folder == "" or file_name in [
                "pom.xml", "application.yml", "application.properties"
            ]:
                folder_path = self.project_path
            else:
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

        print(f"[FileWriter] Starting to write files...")
        print(f"[FileWriter] Execution result keys: {list(execution_result.keys())}")

        for folder_key, files in (
                execution_result
                .items()
        ):

            print(f"[FileWriter] Processing folder: {folder_key}, files count: {len(files) if isinstance(files, list) else 0}")

            if not isinstance(
                    files,
                    list
            ):
                print(f"[FileWriter] Skipping {folder_key} - not a list")
                continue

            for generated_file in files:

                if (
                        "file_name"
                        not in generated_file
                ):
                    print(f"[FileWriter] Skipping file - no file_name field")
                    continue

                print(f"[FileWriter] Writing: {generated_file.get('file_name')} in folder: {generated_file.get('folder')}")

                result = (
                    self.write_file(
                        generated_file
                    )
                )

                print(f"[FileWriter] Result: {result.get('status')} - {result.get('file', result.get('error'))}")

                write_results.append(
                    result
                )

        print(f"[FileWriter] Total files written: {len(write_results)}")
        return write_results