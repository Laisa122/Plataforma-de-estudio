"""Servicio para el envío de correos electrónicos transaccionales mediante SMTP."""

import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import functools
import smtplib
from app.config import get_settings


def _build_otp_html(user_name: str, otp_code: str) -> str:
    """Construye una plantilla HTML atractiva con el código OTP destacado."""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Código de verificación - StudySync</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa; margin: 0; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e5e7eb;">
        <div style="background-color: #4f46e5; padding: 24px; text-align: center;">
            <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700;">StudySync</h1>
        </div>
        <div style="padding: 32px 24px;">
            <h2 style="color: #1f2937; margin-top: 0; font-size: 20px;">¡Hola, {user_name}!</h2>
            <p style="color: #4b5563; font-size: 15px; line-height: 1.6;">
                Gracias por registrarte en StudySync. Para completar la verificación de tu cuenta académica, utiliza el siguiente código de seguridad de un solo uso (OTP):
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <span style="display: inline-block; font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #4f46e5; background-color: #eef2ff; padding: 14px 28px; border-radius: 8px; border: 2px dashed #6366f1;">
                    {otp_code}
                </span>
            </div>
            <p style="color: #6b7280; font-size: 13px; line-height: 1.5;">
                Este código expirará en 15 minutos. Si tú no solicitaste este registro, puedes ignorar este mensaje de forma segura.
            </p>
        </div>
        <div style="background-color: #f9fafb; padding: 16px 24px; text-align: center; border-top: 1px solid #e5e7eb;">
            <p style="color: #9ca3af; font-size: 12px; margin: 0;">
                © StudySync - Plataforma Colaborativa de Estudio
            </p>
        </div>
    </div>
</body>
</html>
"""


def _send_email_sync(to_email: str, subject: str, text_body: str, html_body: str) -> None:
    """Envía un correo electrónico sincrónicamente conectándose al servidor SMTP configurado."""
    settings = get_settings()

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"StudySync <{settings.EMAIL_FROM}>"
    message["To"] = to_email

    # Versión texto plano para evitar filtros de spam agresivos
    part_text = MIMEText(text_body, "plain", "utf-8")
    # Versión HTML visual
    part_html = MIMEText(html_body, "html", "utf-8")

    message.attach(part_text)
    message.attach(part_html)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, [to_email], message.as_string())
            print(f"[StudySync] Correo entregado exitosamente a {to_email}", flush=True)
    except Exception as exc:
        print(f"[StudySync] Aviso SMTP para {to_email}: {exc}", flush=True)


async def send_otp_email(to_email: str, otp_code: str, user_name: str) -> None:
    """Envía el correo con el código OTP de forma asíncrona delegando a un executor."""
    print(f"\n========================================================", flush=True)
    print(f"[StudySync] Código de verificación OTP para {to_email}: {otp_code}", flush=True)
    print(f"========================================================\n", flush=True)
    text_content = f"Hola {user_name},\n\nTu código de verificación para StudySync es: {otp_code}\nEste código expirará en 15 minutos.\n\nEquipo StudySync"
    html_content = _build_otp_html(user_name, otp_code)
    subject = f"Tu código de verificación StudySync: {otp_code}"
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            None,
            functools.partial(_send_email_sync, to_email, subject, text_content, html_content)
        )
    except Exception as exc:
        print(f"[StudySync] Aviso al despachar envío de correo: {exc}", flush=True)
