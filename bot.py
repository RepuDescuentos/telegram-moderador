```python
import os
import re

from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters


URL_REGEX = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+)",
    re.IGNORECASE
)


# =========================================================
# ID DEL OWNER
# =========================================================
# Lo configuraremos como variable de entorno en Render.
# Ejemplo: OWNER_ID=123456789
#
# Si no está configurado, queda en 0.
# =========================================================

OWNER_ID = int(os.environ.get("OWNER_ID", "0"))


def contiene_enlace(message):
    text = message.text or message.caption or ""

    if URL_REGEX.search(text):
        return True

    entities = message.entities or message.caption_entities or []

    for entity in entities:
        if entity.type in ("url", "text_link"):
            return True

    return False


async def moderar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not message or not message.from_user:
        return

    usuario = message.from_user

    # =========================================================
    # EXCEPCIÓN ABSOLUTA DEL OWNER
    # =========================================================
    # Esta comprobación se hace ANTES de revisar administradores.
    # Así el OWNER queda protegido tanto en el canal principal
    # como en el grupo/canal de discusión.
    # =========================================================

    if OWNER_ID != 0 and usuario.id == OWNER_ID:
        print(
            f"👑 OWNER detectado: "
            f"{usuario.full_name} ({usuario.id}). "
            f"Mensaje ignorado por moderación."
        )
        return

    # =========================================================
    # COMPROBAR ADMINISTRADORES
    # =========================================================

    try:
        member = await context.bot.get_chat_member(
            update.effective_chat.id,
            usuario.id
        )
    except Exception as e:
        print(f"Error comprobando administrador: {e}")
        return

    # Los administradores y creador quedan exentos
    if member.status in ("administrator", "creator"):
        return

    # =========================================================
    # SI NO CONTIENE ENLACE, NO HACER NADA
    # =========================================================

    if not contiene_enlace(message):
        return

    nombre = usuario.full_name

    # =========================================================
    # 1. ELIMINAR EL MENSAJE
    # =========================================================

    try:
        await message.delete()

        print(
            f"🗑️ Mensaje eliminado de "
            f"{usuario.username or usuario.id}"
        )

    except Exception as e:
        print(f"❌ No se pudo eliminar el mensaje: {e}")

    # =========================================================
    # 2. ENVIAR ADVERTENCIA
    # =========================================================

    advertencia = (
        f"⚠️ <b>{nombre}</b>, ¡Metete el enlace por el ORTO HIJUEPUTA! 😂\n\n"
        "Esta prohibido publicar cualquier tipo de enlaces."
    )

    try:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=advertencia,
            parse_mode="HTML"
        )

        print(f"⚠️ Advertencia enviada a {nombre}")

    except Exception as e:
        print(f"❌ NO se pudo enviar la advertencia: {e}")


def main():
    token = os.environ["BOT_TOKEN"]
    external_url = os.environ["RENDER_EXTERNAL_URL"]

    application = Application.builder().token(token).build()

    application.add_handler(
        MessageHandler(
            ~filters.COMMAND,
            moderar
        )
    )

    port = int(os.environ.get("PORT", "10000"))

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="telegram",
        webhook_url=f"{external_url}/telegram",
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
```

