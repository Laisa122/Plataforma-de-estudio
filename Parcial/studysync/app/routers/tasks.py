"""Enrutador para la gestión de tareas académicas y control de avances."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, Task, Subject, TaskPriority, TaskStatus
from app.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskStatusUpdate,
    TaskResponse,
    MessageResponse
)

router = APIRouter(prefix="/tasks", tags=["Tareas"])


@router.get("/", response_model=List[TaskResponse])
def list_tasks(
    subject_id: Optional[int] = Query(None, description="Filtrar por identificador de materia"),
    status_filter: Optional[TaskStatus] = Query(None, alias="status", description="Filtrar por estado"),
    priority: Optional[TaskPriority] = Query(None, description="Filtrar por prioridad"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista las tareas del estudiante con filtros opcionales ordenadas por fecha límite y creación."""
    query = db.query(Task).filter(Task.user_id == current_user.id)

    if subject_id is not None:
        query = query.filter(Task.subject_id == subject_id)
    if status_filter is not None:
        query = query.filter(Task.status == status_filter)
    if priority is not None:
        query = query.filter(Task.priority == priority)

    tasks = query.order_by(Task.due_date.asc().nulls_last(), Task.created_at.desc()).all()
    return tasks


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea una nueva tarea académica validando la materia asociada si es provista."""
    if payload.subject_id is not None:
        subject = (
            db.query(Subject)
            .filter(Subject.id == payload.subject_id, Subject.user_id == current_user.id)
            .first()
        )
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La materia indicada no existe o no pertenece al usuario"
            )

    task = Task(
        user_id=current_user.id,
        subject_id=payload.subject_id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        priority=payload.priority
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualiza los atributos de una tarea existente perteneciente al usuario."""
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.user_id == current_user.id)
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada"
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "subject_id" in update_data and update_data["subject_id"] is not None:
        subject = (
            db.query(Subject)
            .filter(Subject.id == update_data["subject_id"], Subject.user_id == current_user.id)
            .first()
        )
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La materia indicada no existe o no pertenece al usuario"
            )

    for field, val in update_data.items():
        setattr(task, field, val)

    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: int,
    payload: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualiza exclusivamente el estado de avance de una tarea."""
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.user_id == current_user.id)
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada"
        )

    task.status = payload.status
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", response_model=MessageResponse)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina una tarea del sistema."""
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.user_id == current_user.id)
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada"
        )

    db.delete(task)
    db.commit()
    return MessageResponse(message="Tarea eliminada exitosamente")
