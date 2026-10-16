# StudySync - Plataforma Colaborativa de Estudio y Gestión Académica

StudySync es una aplicación web integral para la gestión de la vida académica de estudiantes universitarios. Permite organizar asignaturas, controlar tareas y fechas de entrega, así como crear y unirse a grupos de estudio colaborativos con invitaciones por código.

---

## 🛠️ Tecnologías Utilizadas

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **ORM & DB:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) con soporte para **SQLite** (desarrollo) y **PostgreSQL** (producción)
- **Validación de Datos:** [Pydantic v2](https://docs.pydantic.dev/)
- **Seguridad:** Tokens JWT (Access + Refresh token con rotación), contraseñas con bcrypt, limitador de tasa de peticiones con `slowapi`
- **Frontend:** HTML5 semántico, CSS moderno y JavaScript modular (servido directamente por FastAPI sin compiladores externos)
- **Testing:** Pytest (pruebas unitarias y de integración)

---

## 📁 Estructura del Proyecto

```text
├── app/
│   ├── main.py              # Punto de entrada de FastAPI y rutas estáticas
│   ├── config.py            # Configuración con Pydantic Settings
│   ├── database.py          # Conexión SQLAlchemy y generador de sesiones
│   ├── dependencies.py      # Inyección de dependencias (auth, rate-limit)
│   ├── models.py            # Modelos de base de datos
│   ├── schemas.py           # Esquemas de entrada y salida (Pydantic)
│   ├── routers/             # Endpoints (auth, subjects, tasks, groups)
│   └── services/            # Lógica de negocio (auth_service, email_service)
├── frontend/                # Vistas web, estilos CSS y scripts cliente
├── tests/                   # Suite de pruebas unitarias y de integración
├── render.yaml              # Configuración de despliegue para Render
├── requirements.txt         # Dependencias Python
├── .env.example             # Plantilla de variables de entorno
└── .gitignore               # Exclusiones de control de versiones
```

---

## 🚀 Cómo Ejecutar en Local

### 1. Requisitos Previos
- Python 3.10 o superior (3.11/3.12/3.13 recomendado).
- Git.

### 2. Pasos de Instalación

1. **Clonar el repositorio y entrar al directorio:**
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd Plataforma-de-estudio
   ```

2. **Crear y activar un entorno virtual:**
   * En Linux / macOS / WSL:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   * En Windows (PowerShell):
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Variables de entorno (Opcional en local):**
   Puedes crear tu propio archivo `.env` copiando la plantilla:
   ```bash
   cp .env.example .env
   ```
   > **Nota sobre el registro de usuario:** Si no configuras credenciales SMTP en desarrollo, la aplicación imprimirá el código OTP de verificación directamente en la terminal donde corre el servidor:
   > ```text
   > ========================================================
   > [StudySync] Código de verificación OTP para estudiante@correo.com: 123456
   > ========================================================
   > ```

5. **Iniciar el servidor de desarrollo:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

6. **Acceder a la aplicación:**
   - **Aplicación Web:** [http://localhost:8000/](http://localhost:8000/)
   - **Documentación Interactiva (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Documentación ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Pruebas Automatizadas

Para ejecutar la suite de pruebas unitarias e integrales:

```bash
pytest
```

---

## ☁️ Despliegue en Producción (Render)

El repositorio incluye el archivo `render.yaml` preconfigurado como Blueprint para **Render**.

### Pasos para desplegar:
1. Sube los cambios a tu repositorio de GitHub.
2. En [Render](https://dashboard.render.com/), haz clic en **New +** y selecciona **Blueprint**.
3. Conecta este repositorio. Render detectará automáticamente `render.yaml`.
4. Configura las siguientes variables de entorno en el panel de Render:
   - `DATABASE_URL`: URL de conexión a tu base de datos PostgreSQL (Render Postgres, Supabase o Neon).
   - `SMTP_USER` y `SMTP_PASSWORD`: Credenciales de tu proveedor de correo (ej. SendGrid, Mailtrap, Resend o Gmail) para que los usuarios reciban su código de verificación.
5. Haz clic en **Apply** para iniciar el despliegue automático.