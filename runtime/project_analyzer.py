import os


class ProjectAnalyzer:

    def __init__(
            self,
            project_path
    ):

        self.project_path = (
            project_path
        )

    def analyze_project(
            self
    ):

        analysis = {

            "project_name":
                "",

            "base_package":
                "",

            "spring_boot":
                False,

            "controllers":
                [],

            "services":
                [],

            "repositories":
                [],

            "models":
                [],

            "dtos":
                [],

            "exceptions":
                [],

            "configs":
                [],

            "has_service_impl":
                False,

            "has_mapstruct":
                False,

            "has_swagger":
                False,

            "has_lombok":
                False,

            "has_generic_response":
                False,

            "has_dto":
                False,

            "java_files":
                []
        }

        self.detect_project_name(
            analysis
        )

        self.scan_files(
            analysis
        )

        self.detect_patterns(
            analysis
        )

        return analysis

    # ----------------------------------
    # Project Name
    # ----------------------------------

    def detect_project_name(
            self,
            analysis
    ):

        analysis[
            "project_name"
        ] = os.path.basename(
            self.project_path
        )

    # ----------------------------------
    # Scan Files
    # ----------------------------------

    def scan_files(
            self,
            analysis
    ):

        for root, dirs, files in os.walk(
                self.project_path
        ):

            # -------------------------
            # Ignore unwanted folders
            # -------------------------

            dirs[:] = [

                directory

                for directory in dirs

                if directory not in [
                    ".git",
                    "target",
                    "build",
                    ".idea",
                    ".gradle",
                    "node_modules",

                    # Ignore bad generated code
                    "unknown",
                    "generated"
                ]
            ]

            normalized_root = (
                root.replace(
                    "\\",
                    "/"
                )
            )

            # -------------------------
            # Detect Spring Boot
            # -------------------------

            if "pom.xml" in files:

                analysis[
                    "spring_boot"
                ] = True

            # -------------------------
            # Only scan src/main/java
            # -------------------------

            if (
                    "src/main/java"
                    not in normalized_root
            ):
                continue

            for file in files:

                file_path = (
                    os.path.join(
                        root,
                        file
                    )
                )

                # -------------------------
                # Java Files
                # -------------------------

                if not file.endswith(
                        ".java"
                ):
                    continue

                analysis[
                    "java_files"
                ].append(
                    file_path
                )

                lower_path = (
                    file_path.lower()
                )

                # -------------------------
                # Controllers
                # -------------------------

                if (
                        "controller"
                        in lower_path
                ):

                    analysis[
                        "controllers"
                    ].append(
                        file_path
                    )

                # -------------------------
                # Services
                # -------------------------

                elif (
                        "service"
                        in lower_path
                ):

                    analysis[
                        "services"
                    ].append(
                        file_path
                    )

                    if (
                            "impl"
                            in lower_path
                    ):

                        analysis[
                            "has_service_impl"
                        ] = True

                # -------------------------
                # Repository
                # -------------------------

                elif (
                        "repository"
                        in lower_path
                ):

                    analysis[
                        "repositories"
                    ].append(
                        file_path
                    )

                # -------------------------
                # DTO
                # -------------------------

                elif (
                        "dto"
                        in lower_path
                ):

                    analysis[
                        "dtos"
                    ].append(
                        file_path
                    )

                    analysis[
                        "has_dto"
                    ] = True

                # -------------------------
                # Exception
                # -------------------------

                elif (
                        "exception"
                        in lower_path
                ):

                    analysis[
                        "exceptions"
                    ].append(
                        file_path
                    )

                # -------------------------
                # Config
                # -------------------------

                elif (
                        "config"
                        in lower_path
                        or
                        "configuration"
                        in lower_path
                ):

                    analysis[
                        "configs"
                    ].append(
                        file_path
                    )

                # -------------------------
                # Model / Entity
                # -------------------------

                elif (
                        "/model/"
                        in normalized_root
                        or
                        "/entity/"
                        in normalized_root
                ):

                    analysis[
                        "models"
                    ].append(
                        file_path
                    )

    # ----------------------------------
    # Pattern Detection
    # ----------------------------------

    def detect_patterns(
            self,
            analysis
    ):

        # Limit to first 3 files of each type to reduce token usage
        sample_files = (
            analysis["controllers"][:3] +
            analysis["services"][:3] +
            analysis["repositories"][:3] +
            analysis["models"][:3]
        )

        # Store example files for hybrid prompt approach
        analysis["example_files"] = {}

        for java_file in sample_files:

            try:

                with open(
                        java_file,
                        "r",
                        encoding="utf-8"
                ) as file:

                    content = (
                        file.read()
                    )

                # -------------------------
                # Package Detection
                # -------------------------

                if (
                        not analysis[
                            "base_package"
                        ]
                        and
                        "package "
                        in content
                ):

                    package_line = [

                        line

                        for line in
                        content.splitlines()

                        if line.strip()
                        .startswith(
                            "package "
                        )
                    ]

                    if package_line:

                        package_name = (
                            package_line[0]
                            .replace(
                                "package",
                                ""
                            )
                            .replace(
                                ";",
                                ""
                            )
                            .strip()
                        )

                        package_parts = (
                            package_name
                            .split(".")
                        )

                        # avoid detecting deep package
                        # like owner, vehicle, system
                        if (
                                len(
                                    package_parts
                                ) >= 4
                        ):

                            analysis[
                                "base_package"
                            ] = ".".join(
                                package_parts[:4]
                            )

                        else:

                            analysis[
                                "base_package"
                            ] = (
                                package_name
                            )

                # -------------------------
                # Store example file content
                # -------------------------

                lower_path = java_file.lower()

                if "controller" in lower_path and "controller" not in analysis["example_files"]:
                    analysis["example_files"]["controller"] = content

                elif "service" in lower_path and "impl" not in lower_path and "service" not in analysis["example_files"]:
                    analysis["example_files"]["service"] = content

                elif "repository" in lower_path and "repository" not in analysis["example_files"]:
                    analysis["example_files"]["repository"] = content

                # -------------------------
                # MapStruct
                # -------------------------

                if (
                        "@Mapper"
                        in content
                ):

                    analysis[
                        "has_mapstruct"
                    ] = True

                # -------------------------
                # Swagger
                # -------------------------

                if (
                        "OpenAPI"
                        in content
                        or
                        "@Operation"
                        in content
                        or
                        "Swagger"
                        in content
                ):

                    analysis[
                        "has_swagger"
                    ] = True

                # -------------------------
                # Lombok
                # -------------------------

                if (
                        "lombok."
                        in content
                        or
                        "@Data"
                        in content
                        or
                        "@Getter"
                        in content
                        or
                        "@Setter"
                        in content
                        or
                        "@Builder"
                        in content
                ):

                    analysis[
                        "has_lombok"
                    ] = True

                # -------------------------
                # Generic Response
                # -------------------------

                if (
                        "class GenericResponse"
                        in content
                        or
                        "record GenericResponse"
                        in content
                ):

                    analysis[
                        "has_generic_response"
                    ] = True

            except Exception:
                pass