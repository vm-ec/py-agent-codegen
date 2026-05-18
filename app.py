import streamlit as st

from github.repo_loader import (
    RepoLoader
)

from agents.story_analyzer import (
    StoryAnalyzer
)

from runtime.prompt_loader import (
    PromptLoader
)

from runtime.execution_engine import (
    ExecutionEngine
)

from runtime.project_builder import (
    ProjectBuilder
)

from runtime.file_writer import (
    FileWriter
)

# -------------------------
# Page Config
# -------------------------

st.set_page_config(
    page_title="Code Generator Agent",
    layout="wide"
)

# -------------------------
# Title
# -------------------------

st.title(
    "🚀 Code Generator Agent"
)

st.markdown(
    """
    **Java 21 + Spring Boot 3 + Prompt Hub**
    """
)

# -------------------------
# Initialize Services
# -------------------------

repo_loader = RepoLoader()

story_analyzer = StoryAnalyzer()

project_builder = (
    ProjectBuilder()
)

# -------------------------
# Session State
# -------------------------

if "repo_loaded" not in st.session_state:
    st.session_state.repo_loaded = False

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "processing" not in st.session_state:
    st.session_state.processing = False

# -------------------------
# Sidebar
# -------------------------

with st.sidebar:

    st.header("⚙️ Workspace")

    if st.button(
            "📥 Load Prompt Hub",
            disabled=
            st.session_state.processing
    ):

        with st.spinner(
                "Loading Prompt Hub..."
        ):

            success, message = (
                repo_loader
                .clone_repo_if_needed()
            )

            if success:

                st.success(message)

                st.session_state[
                    "repo_loaded"
                ] = True

            else:

                st.error(message)

# -------------------------
# Prompt Hub Loading
# -------------------------

prompt_hub = None

if st.session_state[
        "repo_loaded"
]:

    st.success(
        "✅ Prompt Hub Loaded"
    )

    prompt_loader = (
        PromptLoader(
            repo_loader
            .get_prompt_hub_path()
        )
    )

    prompt_hub = (
        prompt_loader
        .load_prompt_hub()
    )

    with st.expander(
            "🧠 Prompt Hub Summary"
    ):

        st.write(
            "### Parent Prompts"
        )

        st.write(
            list(
                prompt_hub[
                    "parent"
                ][
                    "prompts"
                ].keys()
            )
        )

        st.write(
            "### Child Prompts"
        )

        st.write(
            list(
                prompt_hub[
                    "child"
                ][
                    "prompts"
                ].keys()
            )
        )

else:

    st.warning(
        """
        Please load Prompt Hub first.
        """
    )

# -------------------------
# Chat History
# -------------------------

for message in (
        st.session_state
        .chat_history
):

    with st.chat_message(
            message["role"]
    ):
        st.write(
            message["content"]
        )

# -------------------------
# Chat Input
# -------------------------

story = st.chat_input(
    "Enter your story...",
    disabled=(
        st.session_state.processing
        or
        not prompt_hub
    )
)

# -------------------------
# Story Processing
# -------------------------

if story and prompt_hub:

    st.session_state.processing = True

    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": story
        }
    )

    with st.chat_message(
            "user"
    ):
        st.write(story)

    with st.chat_message(
            "assistant"
    ):

        try:

            # ---------------------
            # Analyze Story
            # ---------------------

            with st.spinner(
                    "Analyzing story..."
            ):

                story_analysis = (
                    story_analyzer
                    .analyze_story(
                        story
                    )
                )

            st.write(
                "## Story Analysis"
            )

            st.json(
                story_analysis
            )

            # ---------------------
            # Execute Prompts
            # ---------------------

            execution_engine = (
                ExecutionEngine(
                    prompt_hub
                )
            )

            st.write(
                "## Prompt Execution"
            )

            progress = st.progress(
                0
            )

            execution_result = {}

            execution_order = [
                "model",
                "dto",
                "mapper",
                "repository",
                "service",
                "exception",
                "controller",
                "integration-tests",
                "config"
            ]

            for index, step in enumerate(
                    execution_order
            ):

                st.write(
                    f"Running: {step}"
                )

                files = (
                    execution_engine
                    .execute_step(
                        step,
                        story_analysis
                    )
                )

                execution_result[
                    step
                ] = files

                progress.progress(
                    (
                        index + 1
                    )
                    / len(
                        execution_order
                    )
                )

            st.success(
                "✅ Code Generation Complete"
            )

            # ---------------------
            # Build Project
            # ---------------------

            project_name = (
                story_analysis.get(
                    "project_name",
                    "GeneratedProject"
                )
                .replace(
                    " ",
                    ""
                )
            )

            st.write(
                "## Building Project"
            )

            project_path = (
                project_builder
                .create_project_structure(
                    project_name
                )
            )

            file_writer = (
                FileWriter(
                    project_path,
                    project_name
                )
            )

            write_results = (
                file_writer
                .write_generated_files(
                    execution_result
                )
            )

            st.success(
                "✅ Project Created"
            )

            st.write(
                "### Project Path"
            )

            st.code(
                project_path
            )

            st.write(
                "### Generated Files"
            )

            st.json(
                write_results
            )

            st.session_state[
                "chat_history"
            ].append(
                {
                    "role":
                    "assistant",

                    "content":
                    (
                        "Project generated "
                        "successfully."
                    )
                }
            )

        except Exception as e:

            st.error(
                f"Error: {str(e)}"
            )

        finally:

            st.session_state.processing = False