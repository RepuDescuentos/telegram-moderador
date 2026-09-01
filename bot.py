import os
import re
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# Detecta enlaces visibles
URL_REGEX = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+)",
    re.IGNORECASE
)

async def moderar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not message or not message.text:
        return

    # Obtener información del usuario
    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        message.from_user.id
    )

    # No tocar mensajes de administradores o propietario
    if member.status in ("administrator", "creator"):
        return

    # Si contiene un enlace, eliminar
    if URL_REGEX.search(message.text):
        try:
            await message.delete()
        except Exception as e:
            print(f"No se pudo eliminar el mensaje: {e}")


def main():
    token = os.environ["BOT_TOKEN"]

    app = Application.builder().token(token).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            moderar
        )
    )

    print("Bot de moderación iniciado.")
    app.run_polling()


if __name__ == "__main__":
    main()
