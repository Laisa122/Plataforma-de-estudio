"""Enrutador para la gestión de grupos de estudio colaborativo y membresías."""

import secrets
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, StudyGroup, GroupMember, Subject, GroupRole
from app.schemas import (
    GroupCreate,
    GroupJoin,
    GroupResponse,
    GroupMemberResponse,
    MessageResponse
)

router = APIRouter(prefix="/groups", tags=["Grupos de Estudio"])


def generate_invite_code() -> str:
    """Genera un código de invitación aleatorio alfanumérico en mayúsculas."""
    return secrets.token_urlsafe(6)[:8].upper()


@router.get("/", response_model=List[GroupResponse])
def list_my_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista todos los grupos de estudio en los que participa el estudiante autenticado."""
    memberships = (
        db.query(GroupMember)
        .filter(GroupMember.user_id == current_user.id)
        .all()
    )

    response_list = []
    for m in memberships:
        grp = m.group
        response_list.append(
            GroupResponse(
                id=grp.id,
                name=grp.name,
                description=grp.description,
                subject_id=grp.subject_id,
                creator_id=grp.creator_id,
                invite_code=grp.invite_code,
                created_at=grp.created_at,
                member_count=len(grp.members)
            )
        )
    return response_list


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    payload: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea un grupo de estudio nuevo asignando al creador como administrador del mismo."""
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

    while True:
        code = generate_invite_code()
        existing = db.query(StudyGroup).filter(StudyGroup.invite_code == code).first()
        if not existing:
            break

    group = StudyGroup(
        name=payload.name,
        description=payload.description,
        subject_id=payload.subject_id,
        creator_id=current_user.id,
        invite_code=code
    )
    db.add(group)
    db.flush()

    admin_member = GroupMember(
        group_id=group.id,
        user_id=current_user.id,
        role=GroupRole.admin
    )
    db.add(admin_member)
    db.commit()
    db.refresh(group)

    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        subject_id=group.subject_id,
        creator_id=group.creator_id,
        invite_code=group.invite_code,
        created_at=group.created_at,
        member_count=1
    )


@router.post("/join", response_model=GroupResponse)
def join_group(
    payload: GroupJoin,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Permite unirse a un grupo existente mediante un código de invitación válido."""
    code = payload.invite_code.strip().upper()
    group = db.query(StudyGroup).filter(StudyGroup.invite_code == code).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo no encontrado con el código de invitación proporcionado"
        )

    already_member = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group.id, GroupMember.user_id == current_user.id)
        .first()
    )
    if already_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya eres miembro de este grupo"
        )

    new_member = GroupMember(
        group_id=group.id,
        user_id=current_user.id,
        role=GroupRole.member
    )
    db.add(new_member)
    db.commit()
    db.refresh(group)

    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        subject_id=group.subject_id,
        creator_id=group.creator_id,
        invite_code=group.invite_code,
        created_at=group.created_at,
        member_count=len(group.members)
    )


@router.get("/{group_id}/members", response_model=List[GroupMemberResponse])
def get_group_members(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene la lista de estudiantes integrantes del grupo si el solicitante pertenece a él."""
    membership = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No eres miembro de este grupo"
        )

    members = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id)
        .order_by(GroupMember.joined_at.asc())
        .all()
    )

    return [
        GroupMemberResponse(
            user_id=m.user_id,
            user_name=m.user.name,
            user_email=m.user.email,
            role=m.role,
            joined_at=m.joined_at
        )
        for m in members
    ]


@router.delete("/{group_id}/leave", response_model=MessageResponse)
def leave_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Permite al estudiante abandonar el grupo de estudio con validación de administradores."""
    membership = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No eres miembro de este grupo"
        )

    if membership.role == GroupRole.admin:
        other_admins = (
            db.query(GroupMember)
            .filter(
                GroupMember.group_id == group_id,
                GroupMember.role == GroupRole.admin,
                GroupMember.user_id != current_user.id
            )
            .count()
        )
        total_members = (
            db.query(GroupMember)
            .filter(GroupMember.group_id == group_id)
            .count()
        )

        if other_admins == 0 and total_members > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debes asignar a otro administrador antes de salir del grupo"
            )

        if total_members == 1:
            group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
            if group:
                db.delete(group)
                db.commit()
                return MessageResponse(
                    message="Has salido del grupo y el grupo fue eliminado por ser el último integrante"
                )

    db.delete(membership)
    db.commit()
    return MessageResponse(message="Has salido del grupo exitosamente")
