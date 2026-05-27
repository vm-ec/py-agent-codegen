import os


class ImpactAnalyzer:

    def __init__(
            self,
            project_analysis,
            user_prompt
    ):

        self.project_analysis = (
            project_analysis
        )

        self.user_prompt = (
            user_prompt.lower()
        )

    def analyze_impact(
            self
    ):

        impact = {

            "intent":
                "",

            "target_domain":
                "",

            "files_to_create":
                [],

            "files_to_modify":
                [],

            "requires_database":
                False,

            "requires_controller":
                False,

            "requires_service":
                False,

            "requires_repository":
                False,

            "requires_tests":
                True,

            "architecture_style":
                {}
        }

        self.detect_intent(
            impact
        )

        self.detect_target_domain(
            impact
        )

        self.detect_required_layers(
            impact
        )

        self.detect_files(
            impact
        )

        self.detect_architecture_style(
            impact
        )

        return impact

    # ----------------------------------
    # Intent Detection
    # ----------------------------------

    def detect_intent(
            self,
            impact
    ):

        prompt = (
            self.user_prompt
        )

        if (
                "create"
                in prompt
                or
                "add"
                in prompt
                or
                "generate"
                in prompt
        ):

            impact[
                "intent"
            ] = "create"

        elif (
                "update"
                in prompt
                or
                "modify"
                in prompt
                or
                "change"
                in prompt
        ):

            impact[
                "intent"
            ] = "modify"

        elif (
                "delete"
                in prompt
                or
                "remove"
                in prompt
        ):

            impact[
                "intent"
            ] = "delete"

        else:

            impact[
                "intent"
            ] = "unknown"

    # ----------------------------------
    # Domain Detection
    # ----------------------------------

    def detect_target_domain(
            self,
            impact
    ):

        words = (
            self.user_prompt
            .replace(
                "endpoint",
                ""
            )
            .replace(
                "api",
                ""
            )
            .split()
        )

        ignored_words = [

            "create",
            "add",
            "generate",
            "update",
            "modify",
            "delete",
            "remove",
            "new"
        ]

        domain = None

        for word in words:

            if (
                    word
                    not in ignored_words
            ):

                domain = (
                    word.capitalize()
                )

                break

        impact[
            "target_domain"
        ] = domain

    # ----------------------------------
    # Layer Detection
    # ----------------------------------

    def detect_required_layers(
            self,
            impact
    ):

        prompt = (
            self.user_prompt
        )

        if (
                "endpoint"
                in prompt
                or
                "api"
                in prompt
        ):

            impact[
                "requires_controller"
            ] = True

            impact[
                "requires_service"
            ] = True

            impact[
                "requires_repository"
            ] = True

            impact[
                "requires_database"
            ] = True

    # ----------------------------------
    # File Decisions
    # ----------------------------------

    def detect_files(
            self,
            impact
    ):

        domain = impact[
            "target_domain"
        ]

        if not domain:
            return

        files = []

        if impact[
                "requires_controller"
        ]:

            files.append(
                f"{domain}Controller.java"
            )

        if impact[
                "requires_service"
        ]:

            files.append(
                f"{domain}Service.java"
            )

        if impact[
                "requires_repository"
        ]:

            files.append(
                f"{domain}Repository.java"
            )

        if impact[
                "requires_database"
        ]:

            files.append(
                f"{domain}.java"
            )

        if impact[
                "requires_tests"
        ]:

            files.append(
                f"{domain}ControllerTests.java"
            )

        impact[
            "files_to_create"
        ] = files

    # ----------------------------------
    # Architecture Style
    # ----------------------------------

    def detect_architecture_style(
            self,
            impact
    ):

        impact[
            "architecture_style"
        ] = {

            "base_package":
                self.project_analysis.get(
                    "base_package"
                ),

            "has_lombok":
                self.project_analysis.get(
                    "has_lombok"
                ),

            "has_swagger":
                self.project_analysis.get(
                    "has_swagger"
                ),

            "has_mapstruct":
                self.project_analysis.get(
                    "has_mapstruct"
                ),

            "has_service_impl":
                self.project_analysis.get(
                    "has_service_impl"
                ),

            "has_generic_response":
                self.project_analysis.get(
                    "has_generic_response"
                )
        }