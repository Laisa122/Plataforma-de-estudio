"""Punto de entrada principal para la aplicación FastAPI StudySync."""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.dependencies import limiter
from app.routers.auth import router as auth_router
from app.routers.subjects import router as subjects_router
from app.routers.tasks import router as tasks_router
from app.routers.groups import router as groups_router

settings = get_settings()

# Directorio que contendrá los archivos estáticos del frontend
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación: inicializa tablas de base de datos."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="API backend para StudySync - Plataforma colaborativa de estudio y gestión académica",
    version="1.0.0",
    lifespan=lifespan
)

# Configuración del limitador de tasa de peticiones (slowapi)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Configuración de CORS según el entorno
allowed_origins = (
    ["*"]
    if settings.ENVIRONMENT != "production"
    else ["https://studysync.onrender.com"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de enrutadores con prefijo /api
app.include_router(auth_router, prefix="/api")
app.include_router(subjects_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(groups_router, prefix="/api")

# Montaje de archivos estáticos y rutas web si el frontend existe
if FRONTEND_DIR.exists():
    css_path = FRONTEND_DIR / "css"
    if css_path.exists():
        app.mount("/css", StaticFiles(directory=str(css_path)), name="css")

    js_path = FRONTEND_DIR / "js"
    if js_path.exists():
        app.mount("/js", StaticFiles(directory=str(js_path)), name="js")

    @app.get("/", include_in_schema=False)
    def serve_index():
        """Sirve la página de inicio o login del frontend."""
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/dashboard", include_in_schema=False)
    def serve_dashboard():
        """Sirve la vista de panel principal."""
        return FileResponse(str(FRONTEND_DIR / "dashboard.html"))

    @app.get("/subjects", include_in_schema=False)
    def serve_subjects():
        """Sirve la vista de asignaturas."""
        return FileResponse(str(FRONTEND_DIR / "subjects.html"))

    @app.get("/tasks", include_in_schema=False)
    def serve_tasks():
        """Sirve la vista de tareas."""
        return FileResponse(str(FRONTEND_DIR / "tasks.html"))

    @app.get("/groups", include_in_schema=False)
    def serve_groups():
        """Sirve la vista de grupos de estudio."""
        return FileResponse(str(FRONTEND_DIR / "groups.html"))
else:
    @app.get("/", include_in_schema=False)
    def root_status():
        """Endpoint raíz con estado operativo de la API."""
        return {
            "app": settings.APP_NAME,
            "status": "online",
            "docs": "/docs",
            "environment": settings.ENVIRONMENT
        }
