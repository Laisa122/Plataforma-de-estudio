"""Pruebas de integración para las operaciones CRUD sobre materias (subjects)."""

from tests.integration.test_auth_flow import register_user, verify_user, login_user


def test_create_and_list_subjects(client, db):
    """Valida la creación de asignaturas y su posterior recuperación en listado."""
    email = "materias.user@universidad.edu.co"
    password = "Password123"

    register_user(client, email, password)
    verify_user(client, db, email)
    token = login_user(client, email, password)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Crear primera materia
    sub1_payload = {
        "name": "Bases de Datos Avanzadas",
        "professor": "Dr. Fernando Morales",
        "color": "#10b981",
        "semester": "2026-1"
    }
    r1 = client.post("/api/subjects/", json=sub1_payload, headers=headers)
    assert r1.status_code == 201
    data1 = r1.json()
    assert data1["name"] == sub1_payload["name"]
    assert data1["color"] == "#10b981"

    # 2. Crear segunda materia
    sub2_payload = {
        "name": "Arquitectura de Software",
        "professor": "Ing. Patricia Ruiz",
        "color": "#3b82f6",
        "semester": "2026-1"
    }
    r2 = client.post("/api/subjects/", json=sub2_payload, headers=headers)
    assert r2.status_code == 201

    # 3. Listar materias del usuario
    list_resp = client.get("/api/subjects/", headers=headers)
    assert list_resp.status_code == 200
    subjects = list_resp.json()
    assert len(subjects) == 2
    subject_names = [s["name"] for s in subjects]
    assert "Bases de Datos Avanzadas" in subject_names
    assert "Arquitectura de Software" in subject_names


def test_update_and_delete_subject(client, db):
    """Valida la modificación parcial y posterior eliminación de una materia."""
    email = "editor.materia@universidad.edu.co"
    password = "Password123"

    register_user(client, email, password)
    verify_user(client, db, email)
    token = login_user(client, email, password)
    headers = {"Authorization": f"Bearer {token}"}

    # Crear materia
    create_resp = client.post(
        "/api/subjects/",
        json={"name": "Inteligencia Artificial", "color": "#8b5cf6"},
        headers=headers
    )
    assert create_resp.status_code == 201
    subject_id = create_resp.json()["id"]

    # Actualizar materia (nombre y profesor)
    update_resp = client.put(
        f"/api/subjects/{subject_id}",
        json={"name": "Inteligencia Artificial y Aprendizaje Automático", "professor": "Dra. Mendez"},
        headers=headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Inteligencia Artificial y Aprendizaje Automático"
    assert update_resp.json()["professor"] == "Dra. Mendez"
    assert update_resp.json()["color"] == "#8b5cf6"  # Color original intacto

    # Eliminar materia
    delete_resp = client.delete(f"/api/subjects/{subject_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert "exitosa" in delete_resp.json()["message"].lower()

    # Confirmar que ya no existe (404 al intentar actualizar)
    retry_update = client.put(
        f"/api/subjects/{subject_id}",
        json={"name": "Nuevo Intento"},
        headers=headers
    )
    assert retry_update.status_code == 404


def test_user_isolation_for_subjects(client, db):
    """Verifica que un estudiante no pueda visualizar ni modificar asignaturas de otro estudiante."""
    # Usuario A
    email_a = "estudiante.a@test.com"
    register_user(client, email_a, "Password123")
    verify_user(client, db, email_a)
    token_a = login_user(client, email_a, "Password123")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Usuario B
    email_b = "estudiante.b@test.com"
    register_user(client, email_b, "Password123")
    verify_user(client, db, email_b)
    token_b = login_user(client, email_b, "Password123")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Usuario A crea una materia
    r_a = client.post(
        "/api/subjects/",
        json={"name": "Física Mecánica", "color": "#ef4444"},
        headers=headers_a
    )
    assert r_a.status_code == 201
    subject_a_id = r_a.json()["id"]

    # Usuario B no ve la materia en su listado
    list_b = client.get("/api/subjects/", headers=headers_b)
    assert list_b.status_code == 200
    assert len(list_b.json()) == 0

    # Usuario B no puede modificar la materia de Usuario A
    edit_b = client.put(
        f"/api/subjects/{subject_a_id}",
        json={"name": "Hackeado"},
        headers=headers_b
    )
    assert edit_b.status_code == 404

    # Usuario B no puede eliminar la materia de Usuario A
    del_b = client.delete(f"/api/subjects/{subject_a_id}", headers=headers_b)
    assert del_b.status_code == 404
