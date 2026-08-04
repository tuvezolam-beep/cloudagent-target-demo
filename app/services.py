from datetime import UTC, datetime

from app.models import AuditEvent, Project, ProjectCreate, Task, TaskCreate, TaskStatus
from app.store import InMemoryStore


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


def utc_now() -> datetime:
    return datetime.now(UTC)


def create_project(db: InMemoryStore, payload: ProjectCreate) -> Project:
    name = payload.name.strip()
    if any(project.name.casefold() == name.casefold() for project in db.projects.values()):
        raise ConflictError("A project with this name already exists")

    project = Project(id=db.next_project_id(), name=name, created_at=utc_now())
    db.projects[project.id] = project
    return project


def get_project(db: InMemoryStore, project_id: int) -> Project:
    project = db.projects.get(project_id)
    if project is None:
        raise NotFoundError("Project not found")
    return project


def create_task(db: InMemoryStore, project_id: int, payload: TaskCreate) -> Task:
    get_project(db, project_id)
    title = payload.title.strip()
    if any(
        task.project_id == project_id and task.title.casefold() == title.casefold()
        for task in db.tasks.values()
    ):
        raise ConflictError("A task with this title already exists in the project")

    task = Task(
        id=db.next_task_id(),
        project_id=project_id,
        title=title,
        description=payload.description.strip(),
        priority=payload.priority,
        status=TaskStatus.TODO,
        due_at=payload.due_at,
        created_at=utc_now(),
    )
    db.tasks[task.id] = task
    return task


def list_tasks(
    db: InMemoryStore,
    project_id: int,
    *,
    page: int,
    page_size: int,
    status: TaskStatus | None = None,
    query: str | None = None,
) -> tuple[list[Task], int]:
    get_project(db, project_id)
    tasks = [task for task in db.tasks.values() if task.project_id == project_id]

    if status is not None:
        tasks = [task for task in tasks if task.status == status]
    if query:
        tasks = [task for task in tasks if query in task.title]

    tasks.sort(key=lambda task: task.id)
    start = (page - 1) * page_size
    if page > 1:
        start -= 1
    return tasks[start : start + page_size], len(tasks)


def set_task_status(
    db: InMemoryStore,
    project_id: int,
    task_id: int,
    status: TaskStatus,
) -> Task:
    get_project(db, project_id)
    task = db.tasks.get(task_id)
    if task is None or task.project_id != project_id:
        raise NotFoundError("Task not found")

    task.status = status
    task.completed_at = utc_now() if status == TaskStatus.DONE else None
    db.tasks[task.id] = task

    event = AuditEvent(
        id=db.next_event_id(),
        project_id=project_id,
        task_id=task_id,
        action=f"status_changed:{status}",
        created_at=utc_now(),
    )
    db.audit_events.append(event)
    return task


def list_audit_events(db: InMemoryStore, project_id: int) -> list[AuditEvent]:
    get_project(db, project_id)
    return [event for event in db.audit_events if event.project_id == project_id]

