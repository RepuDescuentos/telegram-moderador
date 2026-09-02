import os
import re

from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters


URL_REGEX = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+)",
    re.IGNORECASE
)


# =========================================================
# CONFIGURACIÓN
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
    # 1. PUBLICACIONES DIRECTAS DEL CANAL
    # =========================================================
    #
    # MUY IMPORTANTE:
    # Si Telegram nos está entregando una publicación del
    # canal mediante channel_post, NO LA MODERAMOS NUNCA.
    #
    # Esto evita que el bot pueda borrar publicaciones
    # originales del canal.
    # =========================================================

    if update.channel_post:
        print("📢 PUBLICACIÓN DEL CANAL → IGNORADA")
        return

    usuario = message.from_user
    sender_chat = message.sender_chat
    chat_actual = update.effective_chat

    # =========================================================
    # INFORMACIÓN PARA LOS LOGS
    # =========================================================

    print("========================================")
    print("📩 MENSAJE RECIBIDO")
    print(f"💬 CHAT ID: {chat_actual.id}")

    if usuario:
        print(f"👤 USUARIO: {usuario.full_name}")
        print(f"🆔 USER ID: {usuario.id}")
        print(f"👤 USERNAME: @{usuario.username}")

    if sender_chat:
        print(f"📢 SENDER CHAT: {sender_chat.title}")
        print(f"📢 SENDER CHAT ID: {sender_chat.id}")
        print(f"📢 SENDER CHAT TYPE: {sender_chat.type}")

    print(f"👑 OWNER_ID: {OWNER_ID}")

    # =========================================================
    # 2. OWNER POR USER ID
    # =========================================================

    if usuario and usuario.id == OWNER_ID:

        print("👑 OWNER → MENSAJE IGNORADO")
        print("========================================")
        return

    # =========================================================
    # 3. COMPROBAR SI ES EL CANAL VINCULADO
    # =========================================================

    try:

        chat_info = await context.bot.get_chat(
            chat_actual.id
        )

        linked_chat_id = chat_info.linked_chat_id

        print(
            f"🔗 CANAL VINCULADO: {linked_chat_id}"
        )

        # Si el mensaje viene directamente del canal
        # vinculado al grupo de discusión, se ignora.

        if (
            sender_chat
            and linked_chat_id
            and sender_chat.id == linked_chat_id
        ):

            print(
                "📢 MENSAJE DEL CANAL PRINCIPAL "
                "EN DISCUSIÓN → IGNORADO"
            )
            print("========================================")
            return

    except Exception as e:

        print(
            f"⚠️ Error obteniendo canal vinculado: {e}"
        )

    # =========================================================
    # 4. COMPROBAR ADMINISTRADOR / OWNER DEL GRUPO
    # =========================================================

    if usuario:

        try:

            member = await context.bot.get_chat_member(
                chat_actual.id,
                usuario.id
            )

            print(
                f"🔐 STATUS: {member.status}"
            )

            if member.status == "creator":

                print(
                    "👑 OWNER DEL GRUPO → IGNORADO"
                )
                print("========================================")
                return

            if member.status == "administrator":

                print(
                    "🛡️ ADMINISTRADOR → IGNORADO"
                )
                print("========================================")
                return

        except Exception as e:

            print(
                f"⚠️ Error comprobando administrador: {e}"
            )

    # =========================================================
    # 5. SI NO TIENE ENLACE → NO HACER NADA
    # =========================================================

    if not contiene_enlace(message):
        return

    # =========================================================
    # 6. NOMBRE
    # =========================================================

    if usuario:

        nombre = usuario.full_name

    elif sender_chat:

        nombre = sender_chat.title

    else:

        nombre = "Usuario"

    # =========================================================
    # 7. ELIMINAR MENSAJE
    # =========================================================

    try:

        await message.delete()

        print(
            f"🗑️ MENSAJE ELIMINADO: {nombre}"
        )

    except Exception as e:

        print(
            f"❌ NO SE PUDO ELIMINAR: {e}"
        )

    # =========================================================
    # 8. ADVERTENCIA
    # =========================================================

    advertencia = (
        f"⚠️ <b>{nombre}</b>, "
        f"¡Metete el enlace por el ORTO HIJUEPUTA! 😂\n\n"
        "Esta prohibido publicar cualquier tipo de enlaces."
    )

    try:

        await context.bot.send_message(
            chat_id=chat_actual.id,
            text=advertencia,
            parse_mode="HTML"
        )

        print(
            f"⚠️ ADVERTENCIA ENVIADA A: {nombre}"
        )

    except Exception as e:

        print(
            f"❌ NO SE PUDO ENVIAR ADVERTENCIA: {e}"
        )

    print("========================================")


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
        os.environ.get("PORT", "10000")
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
