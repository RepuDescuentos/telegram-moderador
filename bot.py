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

    message = update.effective_message

    if not message:
        return

    # =========================================================
    # INFORMACIÓN DEL MENSAJE
    # =========================================================

    usuario = message.from_user
    sender_chat = message.sender_chat

    print("========================================")
    print("📩 NUEVO MENSAJE")
    print(f"💬 CHAT ID: {update.effective_chat.id}")

    if usuario:
        print(f"👤 USER: {usuario.full_name}")
        print(f"🆔 USER ID: {usuario.id}")
        print(f"👤 USERNAME: @{usuario.username}")

    if sender_chat:
        print(f"📢 SENDER CHAT: {sender_chat.title}")
        print(f"📢 SENDER CHAT ID: {sender_chat.id}")
        print(f"📢 SENDER CHAT TYPE: {sender_chat.type}")

    print(f"👑 OWNER_ID CONFIGURADO: {OWNER_ID}")
    print("========================================")

    # =========================================================
    # EXCEPCIÓN 1: OWNER POR USER ID
    # =========================================================

    if usuario and usuario.id == OWNER_ID:
        print("👑 OWNER DETECTADO POR USER ID → IGNORANDO")
        return

    # =========================================================
    # EXCEPCIÓN 2: MENSAJE ENVIADO COMO CHAT/CANAL
    # =========================================================
    #
    # En grupos de discusión Telegram puede utilizar
    # message.sender_chat en lugar de from_user.
    #
    # Si existe sender_chat, comprobamos si ese chat
    # corresponde al chat donde se está publicando.
    #
    # Esto evita que el bot trate automáticamente como
    # usuario normal ciertos mensajes enviados como identidad
    # del canal/chat.
    # =========================================================

    if sender_chat:

        # Si el mensaje está enviado como el propio chat
        # donde se encuentra el mensaje, no moderarlo.
        if sender_chat.id == update.effective_chat.id:
            print("📢 MENSAJE ENVIADO COMO EL CHAT → IGNORANDO")
            return

    # =========================================================
    # COMPROBAR ADMINISTRADOR / OWNER DEL GRUPO
    # =========================================================

    if usuario:

        try:
            member = await context.bot.get_chat_member(
                update.effective_chat.id,
                usuario.id
            )

            print(f"🔐 STATUS TELEGRAM: {member.status}")

            # OWNER DEL GRUPO
            if member.status == "creator":
                print("👑 CREATOR/OWNER DEL GRUPO → IGNORANDO")
                return

            # ADMINISTRADORES
            if member.status == "administrator":
                print("🛡️ ADMINISTRADOR → IGNORANDO")
                return

        except Exception as e:
            print(f"⚠️ Error comprobando administrador: {e}")

    # =========================================================
    # SI NO HAY ENLACE, NO HACER NADA
    # =========================================================

    if not contiene_enlace(message):
        return

    # =========================================================
    # DATOS DEL USUARIO
    # =========================================================

    if usuario:
        nombre = usuario.full_name
    elif sender_chat:
        nombre = sender_chat.title
    else:
        nombre = "Usuario"

    # =========================================================
    # ELIMINAR MENSAJE
    # =========================================================

    try:

        await message.delete()

        print(
            f"🗑️ MENSAJE ELIMINADO: {nombre}"
        )

    except Exception as e:

        print(
            f"❌ NO SE PUDO ELIMINAR EL MENSAJE: {e}"
        )

    # =========================================================
    # ADVERTENCIA
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
