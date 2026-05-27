import streamlit as st

from github.repo_loader import RepoLoader
from agents.story_analyzer import StoryAnalyzer
from agents.orchestrator import Orchestrator
from runtime.prompt_loader import PromptLoader
from runtime.execution_engine import ExecutionEngine
from runtime.project_builder import ProjectBuilder
from runtime.file_writer import FileWriter
from runtime.zip_manager import ZipManager
from runtime.project_analyzer import ProjectAnalyzer
from runtime.impact_analyzer import ImpactAnalyzer
from runtime.edit_engine import EditEngine

# -------------------------
# Page Config
# -------------------------

st.set_page_config(
    page_title="Code Generator Agent",
    layout="wide"
)

# -------------------------
# Services
# -------------------------

repo_loader = RepoLoader()
story_analyzer = StoryAnalyzer()
project_builder = ProjectBuilder()
zip_manager = ZipManager()

# -------------------------
# Session State
# -------------------------

if "prompt_hub" not in st.session_state:
    st.session_state.prompt_hub = None

if "prompt_hub_status" not in st.session_state:
    st.session_state.prompt_hub_status = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "processing" not in st.session_state:
    st.session_state.processing = False

if "zip_path" not in st.session_state:
    st.session_state.zip_path = None

# Session context — agent memory
if "session_context" not in st.session_state:
    st.session_state.session_context = {}

# -------------------------
# Auto Load Prompt Hub
# -------------------------

if st.session_state.prompt_hub is None:

    with st.spinner("Loading Prompt Hub..."):

        success, message = (
            repo_loader.clone_repo_if_needed()
        )

        if success:

            prompt_loader = PromptLoader(
                repo_loader.get_prompt_hub_path()
            )

            st.session_state.prompt_hub = (
                prompt_loader.load_prompt_hub()
            )

            st.session_state.prompt_hub_status = (
                "success"
            )

        else:

            st.session_state.prompt_hub_status = (
                message
            )

# -------------------------
# Sidebar
# -------------------------

with st.sidebar:

    st.title("🚀 Code Generator Agent")

    st.markdown(
        "**Java 21 + Spring Boot 3 + Prompt Hub**"
    )

    st.divider()

    if (
        st.session_state.prompt_hub_status
        == "success"
    ):
        st.success("✅ Prompt Hub Ready")

    else:

        st.error(
            f"❌ Prompt Hub Failed:\n"
            f"{st.session_state.prompt_hub_status}"
        )

        if st.button("🔄 Retry"):
            st.session_state.prompt_hub = None
            st.session_state.prompt_hub_status = None
            st.rerun()

    st.divider()

    repo_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/org/project",
        help="Fill for Edit Mode, leave empty for New Project Mode"
    )

    if repo_url.strip():
        st.info("🔧 Mode: Edit Existing Project")
    else:
        st.info("🆕 Mode: New Project")

    st.divider()

    # Show session context
    if st.session_state.session_context:

        with st.expander("🧠 Agent Memory"):
            st.json(st.session_state.session_context)

    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.session_state.zip_path = None
        st.session_state.session_context = {}
        st.rerun()

# -------------------------
# Chat Header
# -------------------------

st.title("💬 Code Generator Agent")

if repo_url.strip():
    st.caption(f"🔧 Editing: `{repo_url.strip()}`")
else:
    st.caption("🆕 New Project Mode — describe your project")

# -------------------------
# Chat History
# -------------------------

for message in st.session_state.chat_history:

    with st.chat_message(message["role"]):

        if message.get("type") == "json":
            st.json(message["content"])

        elif message.get("type") == "markdown":
            st.markdown(message["content"])

        else:
            st.write(message["content"])

# -------------------------
# Download ZIP
# -------------------------

if (
    st.session_state.zip_path
    and not st.session_state.processing
):

    with open(st.session_state.zip_path, "rb") as f:

        st.download_button(
            label="⬇ Download Generated Project ZIP",
            data=f,
            file_name=(
                st.session_state.zip_path
                .split("/")[-1]
            ),
            mime="application/zip"
        )

# -------------------------
# Chat Input
# -------------------------

prompt_hub = st.session_state.prompt_hub

user_message = st.chat_input(
    "Ask me anything — generate, edit, push, explain...",
    disabled=(
        st.session_state.processing
        or prompt_hub is None
    )
)

# -------------------------
# Process Message
# -------------------------

if user_message and prompt_hub:

    st.session_state.processing = True

    # Add user message to history
    st.session_state.chat_history.append(
        {
            "role": "user",
            "type": "text",
            "content": user_message
        }
    )

    with st.chat_message("user"):
        st.write(user_message)

    with st.chat_message("assistant"):

        try:

            # -------------------------
            # Orchestrator decides action
            # -------------------------

            orchestrator = Orchestrator(prompt_hub)

            decision = orchestrator.decide_action(
                user_message,
                st.session_state.chat_history,
                repo_url,
                st.session_state.session_context
            )

            action = decision.get("action")
            response_message = decision.get(
                "response_message", ""
            )

            st.write(response_message)

            # =====================================
            # ACTION: clarify
            # =====================================

            if action == "clarify":

                clarification = decision.get(
                    "needs_clarification", ""
                )

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "type": "text",
                        "content": clarification
                    }
                )

            # =====================================
            # ACTION: explain
            # =====================================

            elif action == "explain":

                context = st.session_state.session_context

                explain_prompt = f"""
Based on this session context:
{json.dumps(context, indent=2)}

User asks: {user_message}

Provide a clear, concise explanation.
"""
                import json as _json
                import google.generativeai as genai
                from config.settings import settings

                genai.configure(
                    api_key=settings.GEMINI_API_KEY
                )

                model = genai.GenerativeModel(
                    settings.MODEL_NAME
                )

                response = model.generate_content(
                    explain_prompt
                )

                explanation = response.text

                st.markdown(explanation)

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "type": "markdown",
                        "content": explanation
                    }
                )

            # =====================================
            # ACTION: push_code
            # =====================================

            elif action == "push_code":

                context = st.session_state.session_context

                repo_path = context.get("repo_path")
                repo_name = context.get("repo_name")

                if not repo_path or not repo_name:

                    msg = (
                        "❌ No generated code found in this session. "
                        "Please generate or edit a project first."
                    )

                    st.error(msg)

                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
                            "type": "text",
                            "content": msg
                        }
                    )

                else:

                    from github.git_manager import GitManager

                    with st.spinner(
                        "Pushing branch and raising PR..."
                    ):

                        git_manager = GitManager()

                        pr_result = (
                            git_manager.push_and_raise_pr(
                                repo_path,
                                repo_name,
                                user_message
                            )
                        )

                    if pr_result.get("success"):

                        branch = pr_result.get("branch")
                        pr_url = pr_result.get("pr_url")

                        msg = (
                            f"✅ Code pushed to branch `{branch}`"
                        )

                        if pr_url:
                            msg += f"\n\n🔗 [View Pull Request]({pr_url})"

                        st.markdown(msg)

                        st.session_state.chat_history.append(
                            {
                                "role": "assistant",
                                "type": "markdown",
                                "content": msg
                            }
                        )

                    else:

                        msg = f"❌ Push failed: {pr_result.get('error')}"

                        st.error(msg)

                        st.session_state.chat_history.append(
                            {
                                "role": "assistant",
                                "type": "text",
                                "content": msg
                            }
                        )

            # =====================================
            # ACTION: edit_project
            # =====================================

            elif action == "edit_project":

                with st.spinner("Cloning repository..."):

                    clone_result = (
                        repo_loader.clone_user_repo(
                            repo_url
                        )
                    )

                if not clone_result["success"]:

                    msg = f"❌ Clone failed: {clone_result['error']}"

                    st.error(msg)

                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
                            "type": "text",
                            "content": msg
                        }
                    )

                else:

                    st.success(
                        f"✅ Cloned `{clone_result['repo_name']}`"
                    )

                    with st.spinner(
                        "Analyzing project architecture..."
                    ):

                        analyzer = ProjectAnalyzer(
                            clone_result["repo_path"]
                        )

                        project_analysis = (
                            analyzer.analyze_project()
                        )

                    st.success("✅ Project Analysis Complete")

                    with st.expander("📐 Project Architecture"):
                        st.json(project_analysis)

                    with st.spinner("Analyzing impact..."):

                        impact_analyzer = ImpactAnalyzer(
                            project_analysis,
                            user_message
                        )

                        impact_result = (
                            impact_analyzer.analyze_impact()
                        )

                    st.success("✅ Impact Analysis Complete")

                    with st.expander("🎯 Impact Analysis"):
                        st.json(impact_result)

                    with st.spinner(
                        "Generating changes, pushing and raising PR..."
                    ):

                        edit_engine = EditEngine(
                            prompt_hub,
                            clone_result["repo_path"],
                            clone_result["repo_name"],
                            project_analysis,
                            impact_result,
                            user_message
                        )

                        edit_result = (
                            edit_engine.edit_project()
                        )

                    if edit_result["status"] == "success":

                        # Save to session context
                        st.session_state.session_context.update(
                            {
                                "last_action": "edit_project",
                                "repo_name": clone_result["repo_name"],
                                "repo_path": clone_result["repo_path"],
                                "branch": edit_result.get("branch"),
                                "pr_url": edit_result.get("pr_url"),
                                "files_generated": len(
                                    edit_result.get(
                                        "generated_files", []
                                    )
                                )
                            }
                        )

                        branch = edit_result.get("branch")
                        pr_url = edit_result.get("pr_url")
                        pr_success = edit_result.get("pr_success")

                        with st.expander("📄 Generated Files"):
                            st.json(
                                edit_result.get(
                                    "generated_files", []
                                )
                            )

                        if branch:

                            msg = (
                                f"✅ Changes pushed to branch `{branch}`"
                            )

                            if pr_url:
                                msg += f"\n\n🔗 [View Pull Request]({pr_url})"
                            elif not pr_success:
                                msg += "\n\n⚠️ Branch pushed but PR creation failed."

                        else:

                            msg = "❌ Push failed — check terminal for details."

                        st.markdown(msg)

                        st.session_state.chat_history.append(
                            {
                                "role": "assistant",
                                "type": "markdown",
                                "content": msg
                            }
                        )

                    else:

                        msg = edit_result.get(
                            "error", "Edit failed"
                        )

                        st.error(msg)

                        st.session_state.chat_history.append(
                            {
                                "role": "assistant",
                                "type": "text",
                                "content": f"❌ {msg}"
                            }
                        )

            # =====================================
            # ACTION: generate_project
            # =====================================

            elif action == "generate_project":

                with st.spinner("Analyzing story..."):

                    story_analysis = (
                        story_analyzer.analyze_story(
                            user_message
                        )
                    )

                st.success("✅ Story Analyzed")

                with st.expander("📋 Story Analysis"):
                    st.json(story_analysis)

                execution_engine = ExecutionEngine(
                    prompt_hub
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

                progress = st.progress(0)

                for index, step in enumerate(
                    execution_order
                ):

                    with st.spinner(
                        f"Generating: {step}..."
                    ):

                        files = (
                            execution_engine
                            .execute_step(
                                step,
                                story_analysis
                            )
                        )

                        execution_result[step] = files

                    progress.progress(
                        (index + 1) / len(execution_order)
                    )

                project_name = (
                    story_analysis
                    .get("project_name", "GeneratedProject")
                    .replace(" ", "")
                )

                project_path = (
                    project_builder
                    .create_project_structure(project_name)
                )

                file_writer = FileWriter(
                    project_path,
                    project_name
                )

                write_results = (
                    file_writer
                    .write_generated_files(execution_result)
                )

                zip_path = zip_manager.create_zip(
                    project_path
                )

                st.session_state["zip_path"] = zip_path

                # Save to session context
                st.session_state.session_context.update(
                    {
                        "last_action": "generate_project",
                        "project_name": project_name,
                        "project_path": project_path,
                        "zip_path": zip_path,
                        "story_analysis": story_analysis,
                        "files_generated": len(write_results)
                    }
                )

                msg = (
                    f"✅ Project **{project_name}** generated successfully!\n\n"
                    f"📦 {len(write_results)} files created. Download the ZIP below."
                )

                st.markdown(msg)

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "type": "markdown",
                        "content": msg
                    }
                )

        except Exception as e:

            import traceback

            msg = f"❌ Error: {str(e)}"

            st.error(msg)

            print(traceback.format_exc())

            st.session_state.chat_history.append(
                {
                    "role": "assistant",
                    "type": "text",
                    "content": msg
                }
            )

        finally:

            st.session_state.processing = False
