from agents.repo_edit_agent import (
    RepoEditAgent
)

from runtime.repo_editor import (
    RepoEditor
)

from github.git_manager import (
    GitManager
)


class EditEngine:

    def __init__(
            self,
            prompt_hub,
            repo_path,
            repo_name,
            project_analysis,
            impact_analysis,
            user_prompt
    ):

        self.prompt_hub = prompt_hub
        self.repo_path = repo_path
        self.repo_name = repo_name
        self.project_analysis = project_analysis
        self.impact_analysis = impact_analysis
        self.user_prompt = user_prompt

        self.repo_edit_agent = (
            RepoEditAgent(prompt_hub)
        )

        self.repo_editor = (
            RepoEditor(
                repo_path,
                project_analysis
            )
        )

        self.git_manager = GitManager()

    # ----------------------------------
    # Main Edit Flow
    # ----------------------------------

    def edit_project(self):

        try:

            # -----------------------------
            # Generate Changes
            # -----------------------------

            generated_files = (
                self.generate_repo_changes()
            )

            # -----------------------------
            # Write Files Into Repo
            # -----------------------------

            write_results = (
                self.write_changes_to_repo(
                    generated_files
                )
            )

            # -----------------------------
            # Push + Raise PR
            # -----------------------------

            pr_result = (
                self.git_manager
                .push_and_raise_pr(
                    self.repo_path,
                    self.repo_name,
                    self.user_prompt
                )
            )

            return {
                "status": "success",
                "generated_files": generated_files,
                "write_results": write_results,
                "branch": pr_result.get("branch"),
                "pr_url": pr_result.get("pr_url"),
                "pr_success": pr_result.get("success")
            }

        except Exception as e:

            return {
                "status": "failed",
                "error": str(e)
            }

    # ----------------------------------
    # Generate Repo Changes
    # ----------------------------------

    def generate_repo_changes(self):

        return (
            self.repo_edit_agent
            .generate_repo_changes(
                self.user_prompt,
                self.project_analysis,
                self.impact_analysis
            )
        )

    # ----------------------------------
    # Write Changes Into Repo
    # ----------------------------------

    def write_changes_to_repo(
            self,
            generated_files
    ):

        target_domain = (
            self.impact_analysis.get(
                "target_domain",
                "common"
            )
        )

        self.repo_editor.target_domain = (
            target_domain
        )

        return (
            self.repo_editor
            .place_generated_files(
                generated_files
            )
        )
