import os
from git import Repo

from config.settings import (
    settings
)


class RepoLoader:

    def __init__(self):

        self.repo_url = (
            settings.PROMPT_HUB_REPO
        )

        self.local_path = (
            settings.PROMPT_HUB_PATH
        )

    def clone_repo_if_needed(
            self
    ):

        repo_name = (
            self.repo_url
            .split("/")
            [-1]
            .replace(".git", "")
        )

        repo_path = os.path.join(
            self.local_path,
            repo_name
        )

        os.makedirs(
            self.local_path,
            exist_ok=True
        )

        if os.path.exists(repo_path):

            return (
                True,
                f"Prompt Hub already loaded:\n"
                f"{repo_path}"
            )

        try:

            Repo.clone_from(
                self.repo_url,
                repo_path
            )

            return (
                True,
                f"Prompt Hub cloned:\n"
                f"{repo_path}"
            )

        except Exception as e:

            return (
                False,
                f"Clone failed:\n"
                f"{str(e)}"
            )

    def refresh_repo(self):

        try:

            repo_path = (
                self.get_prompt_hub_path()
            )

            repo = Repo(repo_path)

            origin = (
                repo.remotes.origin
            )

            origin.pull()

            return (
                True,
                "Prompt Hub updated"
            )

        except Exception as e:

            return (
                False,
                f"Refresh failed:\n"
                f"{str(e)}"
            )

    def get_prompt_hub_path(
            self
    ):

        repo_name = (
            self.repo_url
            .split("/")
            [-1]
            .replace(".git", "")
        )

        return os.path.join(
            self.local_path,
            repo_name
        )