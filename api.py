from typing import Optional
import sys

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from github.repo_loader import RepoLoader
from agents.story_analyzer import StoryAnalyzer
from runtime.prompt_loader import PromptLoader
from runtime.execution_engine import ExecutionEngine
from runtime.project_builder import ProjectBuilder
from runtime.file_writer import FileWriter
from runtime.zip_manager import ZipManager
from runtime.project_analyzer import ProjectAnalyzer
from runtime.impact_analyzer import ImpactAnalyzer
from runtime.edit_engine import EditEngine

print("========== API STARTING ==========", flush=True)
print(f"Python version: {sys.version}", flush=True)
print("==================================", flush=True)

app = FastAPI(
    title="Code Generator Agent",
    description="""
## 🚀 AI-Powered Code Generator Agent

Generate and edit **Java 21 + Spring Boot 3** projects using **Prompt Hub + Gemini AI**.

### Use Cases

- **New Project** — Generate a full Spring Boot project from a story/specifications
- **Edit Project** — Clone a public GitHub repo, apply changes, push branch and raise PR

### How it works
1. Prompt Hub (your coding standards) is loaded from GitHub
2. Gemini AI generates code following your exact standards
3. For new projects — download as ZIP
4. For existing projects — feature branch is created and PR is raised to your GitHub repo
    """,
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"\n🔵 INCOMING REQUEST: {request.method} {request.url.path}", flush=True)
    response = await call_next(request)
    print(f"🟢 RESPONSE STATUS: {response.status_code}", flush=True)
    return response


repo_loader = RepoLoader()
story_analyzer = StoryAnalyzer()
project_builder = ProjectBuilder()
zip_manager = ZipManager()


# ----------------------------------
# Helper — Load Prompt Hub
# ----------------------------------

def load_prompt_hub():

    success, message = (
        repo_loader.clone_repo_if_needed()
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Prompt Hub load failed: {message}"
        )

    prompt_loader = PromptLoader(
        repo_loader.get_prompt_hub_path()
    )

    return prompt_loader.load_prompt_hub()


# ----------------------------------
# Request Models
# ----------------------------------

class NewProjectRequest(BaseModel):

    story: str = Field(
        ...,
        description="Story or specifications for the new project",
        example=(
            "Create a student management system "
            "with CRUD operations for student "
            "enrollment, grades and attendance"
        )
    )


class EditProjectRequest(BaseModel):

    repo_url: str = Field(
        ...,
        description="Public GitHub repository URL to edit",
        example="https://github.com/spring-projects/spring-petclinic"
    )

    instructions: str = Field(
        ...,
        description="Instructions describing what changes to make",
        example=(
            "Add a vehicle management module "
            "with CRUD APIs following existing patterns"
        )
    )


# ----------------------------------
# Response Models
# ----------------------------------

class HealthResponse(BaseModel):

    status: str = Field(
        example="ok"
    )


class NewProjectResponse(BaseModel):

    status: str = Field(
        example="success"
    )

    project_name: str = Field(
        example="StudentManagement"
    )

    project_path: str = Field(
        example="generated_projects/StudentManagement"
    )

    zip_path: str = Field(
        example="generated_projects/StudentManagement.zip"
    )

    story_analysis: dict = Field(
        example={
            "project_name": "StudentManagement",
            "domain": "Education",
            "entities": ["Student", "Grade"],
            "features": ["CRUD", "Enrollment"]
        }
    )

    write_results: list = Field(
        example=[
            {
                "status": "success",
                "file": "src/main/java/com/example/studentmanagement/model/Student.java"
            }
        ]
    )


class EditProjectResponse(BaseModel):

    status: str = Field(
        example="success"
    )

    repo_name: str = Field(
        example="spring-petclinic"
    )

    branch: str = Field(
        example="feature/add-vehicle-management-module"
    )

    pr_url: Optional[str] = Field(
        example="https://github.com/your-username/spring-petclinic/pull/1"
    )

    pr_success: bool = Field(
        example=True
    )

    generated_files: list = Field(
        example=[
            {
                "file_name": "VehicleController.java",
                "package": "org.springframework.samples.petclinic.vehicle"
            }
        ]
    )

    write_results: list = Field(
        example=[
            {
                "status": "success",
                "file": "src/main/java/org/springframework/samples/petclinic/vehicle/VehicleController.java"
            }
        ]
    )


# ----------------------------------
# Health Check
# ----------------------------------

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the API is running",
    tags=["General"]
)
def health():
    return {"status": "ok"}


# ----------------------------------
# Use Case 2 — New Project
# ----------------------------------

@app.post(
    "/generate",
    response_model=NewProjectResponse,
    summary="Generate New Project",
    description="""
Generate a full **Java 21 + Spring Boot 3** project from a story or specifications.

### What gets generated
- Model / Entity classes
- DTOs
- MapStruct Mappers
- Repositories
- Services
- Exception handlers
- Controllers
- Integration Tests
- Config classes
- pom.xml, application.yml, Main class

### Output
Returns project path and ZIP path for download.
    """,
    tags=["Code Generation"]
)
def generate_project(
        request: NewProjectRequest
):

    prompt_hub = load_prompt_hub()

    story_analysis = (
        story_analyzer.analyze_story(
            request.story
        )
    )

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

    for step in execution_order:

        files = execution_engine.execute_step(
            step,
            story_analysis
        )

        execution_result[step] = files

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

    zip_path = zip_manager.create_zip(project_path)

    return {
        "status": "success",
        "project_name": project_name,
        "project_path": project_path,
        "zip_path": zip_path,
        "story_analysis": story_analysis,
        "write_results": write_results
    }


# ----------------------------------
# Use Case 1 — Edit Existing Project
# ----------------------------------

@app.post(
    "/edit",
    response_model=EditProjectResponse,
    summary="Edit Existing Project",
    description="""
Clone a **public GitHub repository**, apply AI-generated changes based on your instructions,
push to a feature branch in your GitHub repo and raise a **Pull Request**.

### Flow
1. Clone the public repo fresh
2. Analyze project architecture (controllers, services, patterns)
3. Analyze impact of your instructions
4. Generate changes using Prompt Hub + Gemini
5. Create auto-named feature branch (e.g. `feature/add-vehicle-api`)
6. Commit + push to your GitHub repo
7. Raise Pull Request

### Requirements
- `GITHUB1_TOKEN` and `GITHUB1_USERNAME` must be set in environment variables
    """,
    tags=["Code Generation"]
)
def edit_project(
        request: EditProjectRequest
):

    prompt_hub = load_prompt_hub()

    clone_result = repo_loader.clone_user_repo(
        request.repo_url
    )

    if not clone_result["success"]:
        raise HTTPException(
            status_code=500,
            detail=clone_result["error"]
        )

    analyzer = ProjectAnalyzer(
        clone_result["repo_path"]
    )

    project_analysis = analyzer.analyze_project()

    impact_analyzer = ImpactAnalyzer(
        project_analysis,
        request.instructions
    )

    impact_result = impact_analyzer.analyze_impact()

    edit_engine = EditEngine(
        prompt_hub,
        clone_result["repo_path"],
        clone_result["repo_name"],
        project_analysis,
        impact_result,
        request.instructions
    )

    edit_result = edit_engine.edit_project()

    if edit_result["status"] != "success":
        raise HTTPException(
            status_code=500,
            detail=edit_result.get(
                "error", "Edit failed"
            )
        )

    return {
        "status": "success",
        "repo_name": clone_result["repo_name"],
        "branch": edit_result.get("branch"),
        "pr_url": edit_result.get("pr_url"),
        "pr_success": edit_result.get("pr_success"),
        "generated_files": edit_result.get(
            "generated_files", []
        ),
        "write_results": edit_result.get(
            "write_results", []
        )
    }
