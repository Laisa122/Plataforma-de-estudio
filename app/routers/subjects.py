"""Enrutador para la gestión de materias o asignaturas académicas."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, Subject
from app.schemas import SubjectCreate, SubjectUpdate, SubjectResponse, MessageResponse

router = APIRouter(prefix="/subjects", tags=["Materias"])


@router.get("/", response_model=List[SubjectResponse])
def list_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene el listado completo de materias pertenecientes al estudiante autenticado."""
    subjects = (
        db.query(Subject)
        .filter(Subject.user_id == current_user.id)
        .order_by(Subject.created_at.desc())
        .all()
    )
    return subjects


@router.post("/", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(
    payload: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea una nueva materia académica asociada al estudiante."""
    subject = Subject(
        user_id=current_user.id,
        name=payload.name,
        professor=payload.professor,
        color=payload.color,
        semester=payload.semester
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.put("/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: int,
    payload: SubjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualiza los datos de una materia existente si pertenece al estudiante."""
    subject = (
        db.query(Subject)
        .filter(Subject.id == subject_id, Subject.user_id == current_user.id)
        .first()
    )
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Materia no encontrada"
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(subject, field, val)

    db.commit()
    db.refresh(subject)
    return subject


@router.delete("/{subject_id}", response_model=MessageResponse)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina una materia y sus tareas dependientes."""
    subject = (
        db.query(Subject)
        .filter(Subject.id == subject_id, Subject.user_id == current_user.id)
        .first()
    )
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Materia no encontrada"
        )

    db.delete(subject)
    db.commit()
    return MessageResponse(message="Materia eliminada exitosamente")
