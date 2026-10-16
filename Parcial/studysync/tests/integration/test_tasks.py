"""Pruebas de integración para las operaciones y filtros sobre tareas académicas (tasks)."""

from tests.integration.test_auth_flow import register_user, verify_user, login_user
from app.models import TaskPriority, TaskStatus


def test_create_and_list_tasks_with_subject(client, db):
    """Valida la creación de tareas asociadas a una materia y su listado."""
    email = "tareas.test@universidad.edu.co"
    password = "Password123"

    register_user(client, email, password)
    verify_user(client, db, email)
    token = login_user(client, email, password)
    headers = {"Authorization": f"Bearer {token}"}

    # Crear materia para vincular
    sub_resp = client.post(
        "/api/subjects/",
        json={"name": "Compiladores", "color": "#6366f1"},
        headers=headers
    )
    subject_id = sub_resp.json()["id"]

    # Crear tarea con materia y prioridad alta
    task_payload = {
        "title": "Entrega Fase 1 Analizador Léxico",
        "description": "Implementar autómata con soporte para tokens numéricos e identificadores",
        "priority": TaskPriority.high.value,
        "subject_id": subject_id
    }
    create_task_resp = client.post("/api/tasks/", json=task_payload, headers=headers)
    assert create_task_resp.status_code == 201
    task_data = create_task_resp.json()
    assert task_data["title"] == task_payload["title"]
    assert task_data["status"] == TaskStatus.pending.value
    assert task_data["priority"] == TaskPriority.high.value
    assert task_data["subject_id"] == subject_id

    # Listar tareas
    list_resp = client.get("/api/tasks/", headers=headers)
    assert list_resp.status_code == 200
    tasks = list_resp.json()
    assert len(tasks) == 1
    assert tasks[0]["id"] == task_data["id"]


def test_filter_tasks_by_status_and_priority(client, db):
    """Valida el filtrado de tareas según su estado y prioridad."""
    email = "filtro.tareas@universidad.edu.co"
    password = "Password123"

    register_user(client, email, password)
    verify_user(client, db, email)
    token = login_user(client, email, password)
    headers = {"Authorization": f"Bearer {token}"}

    # Tarea 1: pendiente, media
    client.post(
        "/api/tasks/",
        json={"title": "Tarea 1", "priority": "medium"},
        headers=headers
    )

    # Tarea 2: alta
    t2 = client.post(
        "/api/tasks/",
        json={"title": "Tarea 2 Urgente", "priority": "high"},
        headers=headers
    ).json()

    # Tarea 3: baja
    client.post(
        "/api/tasks/",
        json={"title": "Tarea 3 Menor", "priority": "low"},
        headers=headers
    )

    # Cambiar estado de Tarea 2 a 'in_progress'
    client.patch(
        f"/api/tasks/{t2['id']}/status",
        json={"status": TaskStatus.in_progress.value},
        headers=headers
    )

    # Filtrar por status=in_progress
    resp_filter_status = client.get("/api/tasks/?status=in_progress", headers=headers)
    assert resp_filter_status.status_code == 200
    in_progress_tasks = resp_filter_status.json()
    assert len(in_progress_tasks) == 1
    assert in_progress_tasks[0]["title"] == "Tarea 2 Urgente"

    # Filtrar por status=pending
    resp_filter_pending = client.get("/api/tasks/?status=pending", headers=headers)
    assert resp_filter_pending.status_code == 200
    assert len(resp_filter_pending.json()) == 2

    # Filtrar por priority=high
    resp_filter_priority = client.get("/api/tasks/?priority=high", headers=headers)
    assert resp_filter_priority.status_code == 200
    assert len(resp_filter_priority.json()) == 1
    assert resp_filter_priority.json()[0]["id"] == t2["id"]


def test_update_task_status_and_delete(client, db):
    """Valida la transición de estado de una tarea y su eliminación."""
    email = "lifecycle.task@universidad.edu.co"
    password = "Password123"

    register_user(client, email, password)
    verify_user(client, db, email)
    token = login_user(client, email, password)
    headers = {"Authorization": f"Bearer {token}"}

    # Crear tarea
    task = client.post(
        "/api/tasks/",
        json={"title": "Estudiar para el Quiz"},
        headers=headers
    ).json()
    task_id = task["id"]

    # Marcar como 'done'
    patch_resp = client.patch(
        f"/api/tasks/{task_id}/status",
        json={"status": TaskStatus.done.value},
        headers=headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == TaskStatus.done.value

    # Eliminar tarea
    del_resp = client.delete(f"/api/tasks/{task_id}", headers=headers)
    assert del_resp.status_code == 200

    # Verificar que ya no existe
    list_after = client.get("/api/tasks/", headers=headers).json()
    assert len(list_after) == 0
