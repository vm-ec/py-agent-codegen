import os
import stat
import shutil

from git import Repo

from config.settings import (
    settings
)


class RepoLoader:

    def __init__(self):

        self.workspace_path = (
            "workspace"
        )

        self.linked_projects_path = (
            os.path.join(
                self.workspace_path,
                "linked_projects"
            )
        )

        self.prompt_hub_repo = (
            settings.PROMPT_HUB_REPO
        )

        os.makedirs(
            self.workspace_path,
            exist_ok=True
        )

        os.makedirs(
            self.linked_projects_path,
            exist_ok=True
        )

    # ----------------------------------
    # Prompt Hub Clone
    # ----------------------------------

    def clone_repo_if_needed(self):

        if not self.prompt_hub_repo:
            return (
                False,
                "PROMPT_HUB_REPO env variable is not set"
            )

        prompt_hub_path = (
            self.get_prompt_hub_path()
        )

        try:

            if os.path.exists(
                    prompt_hub_path
            ):

                return (
                    True,
                    "Prompt Hub already loaded"
                )

            Repo.clone_from(
                self.prompt_hub_repo,
                prompt_hub_path
            )

            return (
                True,
                "Prompt Hub loaded successfully"
            )

        except Exception as e:

            return (
                False,
                str(e)
            )

    # ----------------------------------
    # Prompt Hub Path
    # ----------------------------------

    def get_prompt_hub_path(self):

        return os.path.join(
            self.workspace_path,
            "prompt_hub"
        )

    # ----------------------------------
    # Clone User Repo
    # ----------------------------------

    def clone_user_repo(
            self,
            repo_url
    ):

        try:

            repo_name = (
                repo_url
                .rstrip("/")
                .split("/")[-1]
                .replace(".git", "")
            )

            repo_path = os.path.join(
                self.linked_projects_path,
                repo_name
            )

            if os.path.exists(repo_path):

                def force_remove(
                        func,
                        path,
                        exc
                ):
                    os.chmod(
                        path,
                        stat.S_IWRITE
                    )
                    func(path)

                shutil.rmtree(
                    repo_path,
                    onerror=force_remove
                )

            Repo.clone_from(
                repo_url,
                repo_path
            )

            return {
                "success": True,
                "repo_name": repo_name,
                "repo_path": repo_path
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }
