import os
from flask import Flask, request
import telebot
from supabase import create_client, Client

# ---------------- CONFIGURACIÓN ----------------

TOKEN = os.getenv("TOKEN")
URL = os.getenv("URL_APP")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not TOKEN:
    raise ValueError("TOKEN no definido en variables de entorno")

if not URL:
    raise ValueError("URL_APP no definida")

# Inicialización
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- WEBHOOK ----------------

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200


@app.route("/")
def index():
    bot.remove_webhook()
    bot.set_webhook(url=f"{URL}/{TOKEN}")
    return "Bot funcionando correctamente", 200


# ---------------- BOT ----------------

@bot.message_handler(commands=["start"])
def send_welcome(message):
    print("ALGUIEN ESCRIBIÓ /START")
    bot.reply_to(message, "¡Hola! Estoy vivo.")


@bot.message_handler(commands=["buscar"])
def buscar_producto(message):

    parts = message.text.split(" ", 1)

    if len(parts) < 2:
        bot.reply_to(
            message,
            "⚠️ Escribe algo para buscar.\nEjemplo:\n`/buscar laptop`",
            parse_mode="Markdown",
        )
        return

    query_text = parts[1].strip()

    try:
        response = (
            supabase
            .table("productos")
            .select("*")
            .ilike("nombre", f"%{query_text}%")
            .execute()
        )

        data = response.data or []

        if len(data) == 0:
            bot.reply_to(
                message,
                f"❌ No encontré resultados para: *{query_text}*",
                parse_mode="Markdown",
            )
            return

        respuesta = "🔍 *Resultados encontrados:*\n\n"

        for item in data:
            nombre = item.get("nombre", "Sin nombre")
            precio = item.get("precio", "N/A")
            stock = item.get("stock", "N/A")

            respuesta += (
                f"📦 *{nombre}*\n"
                f"💰 Precio: ${precio}\n"
                f"📦 Stock: {stock}\n\n"
            )

        bot.reply_to(message, respuesta, parse_mode="Markdown")

    except Exception as e:
        print("Error Supabase:", e)
        bot.reply_to(message, "⚠️ Error al consultar la base de datos.")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Me dijiste: {message.text}")


# ---------------- SERVER ----------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)