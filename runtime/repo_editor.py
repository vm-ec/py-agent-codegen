import os


class RepoEditor:

    def __init__(
            self,
            repo_path,
            project_analysis
    ):

        self.repo_path = (
            repo_path
        )

        self.project_analysis = (
            project_analysis
        )

    # ----------------------------------
    # Main Entry
    # ----------------------------------

    def place_generated_files(
            self,
            generated_files
    ):

        results = []

        if not isinstance(
                generated_files,
                list
        ):

            return [

                {
                    "status":
                        "failed",

                    "error":
                        "Generated files must be a list"
                }
            ]

        for file_data in (
                generated_files
        ):

            try:

                result = (
                    self.write_file(
                        file_data
                    )
                )

                results.append(
                    result
                )

            except Exception as e:

                results.append(

                    {
                        "status":
                            "failed",

                        "error":
                            str(e)
                    }
                )

        return results

    # ----------------------------------
    # Write File
    # ----------------------------------

    def write_file(
            self,
            file_data
    ):

        if (
                not isinstance(
                    file_data,
                    dict
                )
        ):

            return {

                "status":
                    "invalid",

                "reason":
                    "File data is not dictionary"
            }

        file_name = (
            file_data.get(
                "file_name"
            )
        )

        package_name = (
            file_data.get(
                "package"
            )
        )

        content = (
            file_data.get(
                "content"
            )
        )

        if (
                not file_name
                or
                not package_name
                or
                not content
        ):

            return {

                "status":
                    "invalid",

                "reason":
                    "Missing required fields"
            }

        target_path = (
            self.resolve_package_path(
                package_name
            )
        )

        os.makedirs(
            target_path,
            exist_ok=True
        )

        file_path = os.path.join(
            target_path,
            file_name
        )

        # ----------------------------------
        # Safe Overwrite Protection
        # ----------------------------------

        if os.path.exists(
                file_path
        ):

            return {

                "status":
                    "already_exists",

                "file":
                    file_path
            }

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

    # ----------------------------------
    # Resolve Package Path
    # ----------------------------------

    def resolve_package_path(
            self,
            package_name
    ):

        package_path = (
            package_name.replace(
                ".",
                os.sep
            )
        )

        src_main_java = os.path.join(

            self.repo_path,

            "src",

            "main",

            "java"
        )

        final_path = os.path.join(

            src_main_java,

            package_path
        )

        return (
            final_path
        )

    # ----------------------------------
    # Helper
    # ----------------------------------

    def file_exists(
            self,
            package_name,
            file_name
    ):

        package_path = (
            self.resolve_package_path(
                package_name
            )
        )

        file_path = os.path.join(
            package_path,
            file_name
        )

        return os.path.exists(
            file_path
        )