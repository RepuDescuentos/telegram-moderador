import os
import re

from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters


URL_REGEX = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+)",
    re.IGNORECASE
)


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

    # Comprobar si quien publicó es administrador
    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        message.from_user.id
    )

    # Los administradores quedan exentos
    if member.status in ("administrator", "creator"):
        return

    # Si no contiene enlace, no hacer nada
    if not contiene_enlace(message):
        return

    usuario = message.from_user

    # Nombre que aparecerá en la advertencia
    nombre = usuario.full_name

    try:
        # Primero eliminamos el mensaje
        await message.delete()

        print(
            f"Mensaje eliminado de "
            f"{usuario.username or usuario.id}"
        )

        # Enviar advertencia
        advertencia = (
            f"⚠️ <b>{nombre}</b>, ¡Metete el enlace por el ORTO! 😂\n\n"
            "Esta prohibido publicar cualquier tipo de enlaces."
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=advertencia,
            parse_mode="HTML"
        )

    except Exception as e:
        print(f"No se pudo procesar el mensaje: {e}")


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
