import os
import zipfile


class ZipManager:

    def create_zip(
            self,
            project_path
    ):

        project_name = (
            os.path.basename(
                project_path
            )
        )

        zip_path = (
            f"{project_path}.zip"
        )

        with zipfile.ZipFile(
                zip_path,
                "w",
                zipfile.ZIP_DEFLATED
        ) as zip_file:

            for root, _, files in os.walk(
                    project_path
            ):

                for file in files:

                    file_path = (
                        os.path.join(
                            root,
                            file
                        )
                    )

                    arc_name = (
                        os.path.relpath(
                            file_path,
                            os.path.dirname(
                                project_path
                            )
                        )
                    )

                    zip_file.write(
                        file_path,
                        arc_name
                    )

        return zip_path