import os
from flask import Flask, request
import telebot
from supabase import create_client, Client

# Configuración de Variables (Se cargan desde la nube)
TOKEN = os.getenv('TOKEN')
URL = os.getenv('URL_APP')
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Inicialización
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- RUTAS DE WEBHOOK ---
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=URL + TOKEN)
    return "Bot funcionando correctamente", 200

# --- LÓGICA DEL BOT ---

# Comando /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "¡Hola! Soy tu bot funcional en Python. ¿En qué puedo ayudarte?")

# Comando /buscar [nombre]
@bot.message_handler(commands=['buscar'])
def buscar_producto(message):
    query_text = message.text.replace('/buscar ', '').strip()

    if not query_text or query_text == '/buscar':
        bot.reply_to(message, "⚠️ Por favor, escribe qué quieres buscar. Ej: `/buscar laptop`", parse_mode="Markdown")
        return

    try:
        # Búsqueda en la tabla "productos" de Supabase
        response = supabase.table("productos").select("*").ilike("nombre", f"%{query_text}%").execute()
        data = response.data

        if len(data) > 0:
            respuesta = "🔍 **Resultados encontrados:**\n\n"
            for item in data:
                respuesta += f"📦 *{item['nombre']}*\n💰 Precio: ${item['precio']}\n🔢 Stock: {item['stock']}\n\n"
            bot.reply_to(message, respuesta, parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ No encontré nada relacionado con '{query_text}'.")
    except Exception as e:
        bot.reply_to(message, "Error al conectar con la base de datos.")
        print(f"Error: {e}")

# Respuesta por defecto (Echo)
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Me dijiste: {message.text}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))