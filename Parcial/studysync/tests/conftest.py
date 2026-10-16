"""Configuración global de fixtures de prueba para pytest."""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, patch

# Configuración de variables de entorno antes de importar la aplicación
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("SECRET_KEY", "clave-secreta-de-prueba-no-usar-en-produccion")
os.environ.setdefault("SMTP_USER", "test")
os.environ.setdefault("SMTP_PASSWORD", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_studysync.db")

from app.main import app
from app.database import Base, get_db

TEST_DB_URL = "sqlite:///./test_studysync.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Generador que reemplaza la dependencia get_db para usar la base de datos de pruebas."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_database():
    """Reinicia el esquema de base de datos antes y después de cada prueba."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Cliente de pruebas HTTP sincronizado para invocar endpoints de FastAPI."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture
def db():
    """Proporciona una sesión de base de datos directa para verificar o crear datos en pruebas."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def mock_email():
    """Simula el servicio de correo electrónico para evitar envíos reales durante pruebas."""
    with patch("app.routers.auth.send_otp_email", new_callable=AsyncMock) as mocked_send:
        yield mocked_send
