from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.models import (
    AuditEvent,
    BulkTaskCreate,
    Project,
    ProjectCreate,
    ProjectMetrics,
    Task,
    TaskCreate,
    TaskPage,
    TaskStatus,
    TaskStatusUpdate,
)
from app.services import (
    ConflictError,
    NotFoundError,
    create_project,
    create_task,
    list_audit_events,
    list_tasks,
    set_task_status,
)
from app.store import store

app = FastAPI(
    title="SprintPilot",
    description="A small project-tracking API used as a coding-agent evaluation target.",
    version="0.1.0",
)


@app.exception_handler(NotFoundError)
async def not_found_handler(_request, exc: NotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(ConflictError)
async def conflict_handler(_request, exc: ConflictError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/projects", response_model=Project, status_code=status.HTTP_201_CREATED)
def post_project(payload: ProjectCreate) -> Project:
    return create_project(store, payload)


@app.post(
    "/projects/{project_id}/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
)
def post_task(project_id: int, payload: TaskCreate) -> Task:
    return create_task(store, project_id, payload)


@app.get("/projects/{project_id}/tasks", response_model=TaskPage)
def get_tasks(
    project_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    task_status: TaskStatus | None = Query(default=None, alias="status"),
    query: str | None = Query(default=None, min_length=1),
) -> TaskPage:
    items, total = list_tasks(
        store,
        project_id,
        page=page,
        page_size=page_size,
        status=task_status,
        query=query,
    )
    return TaskPage(items=items, page=page, page_size=page_size, total=total)


@app.patch("/projects/{project_id}/tasks/{task_id}/status", response_model=Task)
def patch_task_status(project_id: int, task_id: int, payload: TaskStatusUpdate) -> Task:
    return set_task_status(store, project_id, task_id, payload.status)


@app.get("/projects/{project_id}/audit-events", response_model=list[AuditEvent])
def get_audit_events(project_id: int) -> list[AuditEvent]:
    return list_audit_events(store, project_id)


@app.post(
    "/projects/{project_id}/tasks/bulk",
    response_model=list[Task],
    status_code=status.HTTP_201_CREATED,
)
def post_tasks_bulk(project_id: int, payload: BulkTaskCreate) -> list[Task]:
    del project_id, payload
    raise HTTPException(status_code=501, detail="Bulk task creation is not implemented")


@app.get("/projects/{project_id}/metrics", response_model=ProjectMetrics)
def get_project_metrics(project_id: int) -> ProjectMetrics:
    del project_id
    raise HTTPException(status_code=501, detail="Project metrics are not implemented")
