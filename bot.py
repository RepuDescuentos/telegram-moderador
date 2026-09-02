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

    # =========================================================
    # SOLO TRABAJAR CON MENSAJES DEL GRUPO DE DISCUSIÓN
    # =========================================================

    message = update.message

    if not message:
        return

    usuario = message.from_user

    if not usuario:
        return

    # =========================================================
    # IGNORAR REENVÍOS AUTOMÁTICOS DEL CANAL
    # =========================================================
    #
    # Telegram envía automáticamente la publicación del canal
    # al grupo de discusión. No queremos que el bot la trate
    # como si fuera un mensaje de un usuario.
    # =========================================================

    if message.is_automatic_forward:
        print("📢 REENVÍO AUTOMÁTICO DEL CANAL → IGNORADO")
        return

    # =========================================================
    # OWNER
    # =========================================================

    if usuario.id == OWNER_ID:

        print(
            f"👑 OWNER → IGNORADO: "
            f"{usuario.full_name} ({usuario.id})"
        )

        return

    # =========================================================
    # COMPROBAR ADMINISTRADOR / OWNER DEL GRUPO
    # =========================================================

    try:

        member = await context.bot.get_chat_member(
            message.chat.id,
            usuario.id
        )

        print(
            f"👤 {usuario.full_name} | "
            f"ID: {usuario.id} | "
            f"STATUS: {member.status}"
        )

        # OWNER DEL GRUPO
        if member.status == "creator":

            print("👑 CREATOR DEL GRUPO → IGNORADO")
            return

        # ADMINISTRADOR
        if member.status == "administrator":

            print("🛡️ ADMINISTRADOR → IGNORADO")
            return

    except Exception as e:

        print(
            f"⚠️ Error comprobando administrador: {e}"
        )

    # =========================================================
    # SI NO HAY ENLACE → NO HACER NADA
    # =========================================================

    if not contiene_enlace(message):
        return

    # =========================================================
    # USUARIO NORMAL CON ENLACE
    # =========================================================

    nombre = usuario.full_name

    # =========================================================
    # ELIMINAR MENSAJE
    # =========================================================

    try:

        await message.delete()

        print(
            f"🗑️ ENLACE ELIMINADO DE: "
            f"{nombre} ({usuario.id})"
        )

    except Exception as e:

        print(
            f"❌ NO SE PUDO ELIMINAR EL MENSAJE: {e}"
        )

        # Si no pudo eliminarlo, no tiene sentido
        # lanzar la advertencia.
        return

    # =========================================================
    # ADVERTENCIA
    # =========================================================

    advertencia = (
        f"⚠️ <b>{nombre}</b>, "
        f"¡Metete el enlace por el ORTO HIJUEPUTA! 😂\n\n"
        "Esta prohibido publicar cualquier tipo de enlaces."
    )

    try:

        await context.bot.send_message(
            chat_id=message.chat.id,
            text=advertencia,
            parse_mode="HTML"
        )

        print(
            f"⚠️ ADVERTENCIA ENVIADA A: {nombre}"
        )

    except Exception as e:

        print(
            f"❌ NO SE PUDO ENVIAR LA ADVERTENCIA: {e}"
        )


def main():

    token = os.environ["BOT_TOKEN"]
    external_url = os.environ["RENDER_EXTERNAL_URL"]

    application = (
        Application.builder()
        .token(token)
        .build()
    )

    # =========================================================
    # SOLO MENSAJES NORMALES
    # =========================================================

    application.add_handler(
        MessageHandler(
            ~filters.COMMAND,
            moderar
        )
    )

    port = int(
        os.environ.get(
            "PORT",
            "10000"
        )
    )

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="telegram",
        webhook_url=f"{external_url}/telegram",
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
