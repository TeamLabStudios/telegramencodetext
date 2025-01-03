import os
import json
import base64
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from cryptography.fernet import Fernet

class UserManager:
    def __init__(self, storage_file="users.json"):
        self.storage_file = storage_file
        self.users = self._load_users()

    def _load_users(self):
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_users(self):
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)

    def register_user(self, user_id, username, first_name, last_name=None):
        user_id = str(user_id)
        if user_id not in self.users:
            self.users[user_id] = {
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "joined_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "messages_encrypted": 0,
                "messages_decrypted": 0,
                "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        self._save_users()

    def update_stats(self, user_id, action):
        user_id = str(user_id)
        if user_id in self.users:
            if action == "encrypt":
                self.users[user_id]["messages_encrypted"] += 1
            elif action == "decrypt":
                self.users[user_id]["messages_decrypted"] += 1
            self.users[user_id]["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._save_users()

    def get_user_stats(self, user_id):
        return self.users.get(str(user_id))

    def get_all_users(self):
        return self.users

class UserKeyManager:
    def __init__(self, storage_file="user_keys.json"):
        self.storage_file = storage_file
        self.keys = self._load_keys()

    def _load_keys(self):
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_keys(self):
        with open(self.storage_file, 'w') as f:
            json.dump(self.keys, f)

    def get_user_key(self, user_id):
        user_id = str(user_id)
        if user_id not in self.keys:
            self.generate_new_key(user_id)
        return self.keys[user_id]

    def generate_new_key(self, user_id):
        user_id = str(user_id)
        key = Fernet.generate_key().decode()
        self.keys[user_id] = key
        self._save_keys()
        return key

# Inicializa los gestores
key_manager = UserKeyManager()
user_manager = UserManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Registra al usuario y envía el mensaje de bienvenida."""
    user = update.effective_user
    user_manager.register_user(
        user.id,
        user.username,
        user.first_name,
        user.last_name
    )

    await update.message.reply_text(
        f'¡Hola {user.first_name}! Soy un bot de encriptación con claves personalizadas.\n\n'
        'Comandos disponibles:\n'
        '/encrypt <mensaje> - Encripta un mensaje\n'
        '/decrypt <mensaje> - Desencripta un mensaje\n'
        '/newkey - Genera una nueva clave personal\n'
        '/mykey - Muestra tu clave actual\n'
        '/stats - Muestra tus estadísticas de uso'
    )

async def encrypt_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Encripta el mensaje y actualiza estadísticas."""
    try:
        message = ' '.join(context.args)
        if not message:
            await update.message.reply_text('Por favor proporciona un mensaje para encriptar.')
            return

        user_key = key_manager.get_user_key(update.effective_user.id)
        fernet = Fernet(user_key.encode())

        encrypted_message = fernet.encrypt(message.encode())
        safe_message = base64.urlsafe_b64encode(encrypted_message).decode()
        
        user_manager.update_stats(update.effective_user.id, "encrypt")
        
        await update.message.reply_text(
            'Mensaje encriptado:\n'
            f'`{safe_message}`',
            parse_mode='Markdown'
        )
        
        await update.message.reply_text(
            'Copia y pega esto para desencriptar:\n'
            f'`/decrypt {safe_message}`',
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f'Error al encriptar: {str(e)}')

async def decrypt_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Desencripta el mensaje y actualiza estadísticas."""
    try:
        message = ' '.join(context.args)
        if not message:
            await update.message.reply_text('Por favor proporciona un mensaje para desencriptar.')
            return

        user_key = key_manager.get_user_key(update.effective_user.id)
        fernet = Fernet(user_key.encode())

        try:
            decoded_message = base64.urlsafe_b64decode(message.encode())
            decrypted_message = fernet.decrypt(decoded_message)
            
            user_manager.update_stats(update.effective_user.id, "decrypt")
            
            await update.message.reply_text(
                'Mensaje desencriptado:\n'
                f'`{decrypted_message.decode()}`',
                parse_mode='Markdown'
            )
        except Exception:
            await update.message.reply_text(
                'No se pudo desencriptar el mensaje.\n'
                'Esto puede deberse a:\n'
                '1. El mensaje fue encriptado con una clave diferente\n'
                '2. El formato del mensaje es incorrecto\n'
                '3. Has generado una nueva clave desde que se encriptó el mensaje'
            )
    except Exception as e:
        await update.message.reply_text(
            'Error al desencriptar. Por favor verifica:\n'
            '1. Que hayas copiado todo el mensaje encriptado\n'
            '2. Que no haya espacios extras\n'
            '3. Que uses el comando correctamente'
        )

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra las estadísticas del usuario."""
    user_id = update.effective_user.id
    stats = user_manager.get_user_stats(user_id)
    
    if stats:
        await update.message.reply_text(
            '📊 Tus estadísticas:\n\n'
            f'Fecha de registro: {stats["joined_date"]}\n'
            f'Mensajes encriptados: {stats["messages_encrypted"]}\n'
            f'Mensajes desencriptados: {stats["messages_decrypted"]}\n'
            f'Última actividad: {stats["last_active"]}'
        )
    else:
        await update.message.reply_text('No se encontraron estadísticas. Usa /start para registrarte.')

async def generate_new_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera una nueva clave para el usuario."""
    user_id = update.effective_user.id
    key_manager.generate_new_key(user_id)
    await update.message.reply_text(
        '✨ ¡Nueva clave generada con éxito! ✨\n\n'
        'Nota: Los mensajes encriptados con tu clave anterior ya no podrán ser desencriptados.'
    )

async def show_current_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la clave actual del usuario."""
    user_id = update.effective_user.id
    key = key_manager.get_user_key(user_id)
    await update.message.reply_text(
        'Tu clave actual es:\n'
        f'`{key}`\n\n'
        '⚠️ No compartas esta clave con nadie ⚠️\n'
        'Solo podrás desencriptar mensajes si mantienes la misma clave con la que fueron encriptados.',
        parse_mode='Markdown'
    )

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra estadísticas globales (solo para administradores)."""
    ADMIN_IDS = os.environ.get('ADMIN_ID', '').split(',')  # Lee los IDs de administradores desde variable de entorno
    user_id = str(update.effective_user.id)
    
    if user_id in ADMIN_IDS:
        users = user_manager.get_all_users()
        total_users = len(users)
        total_encrypted = sum(user["messages_encrypted"] for user in users.values())
        total_decrypted = sum(user["messages_decrypted"] for user in users.values())
        
        active_users = sum(1 for user in users.values() 
                         if datetime.strptime(user["last_active"], "%Y-%m-%d %H:%M:%S") > 
                         datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))
        
        await update.message.reply_text(
            '📊 Estadísticas globales:\n\n'
            f'Total de usuarios: {total_users}\n'
            f'Usuarios activos hoy: {active_users}\n'
            f'Total mensajes encriptados: {total_encrypted}\n'
            f'Total mensajes desencriptados: {total_decrypted}'
        )
    else:
        await update.message.reply_text('No tienes permiso para ver las estadísticas globales.')

def main():
    """Función principal para iniciar el bot."""
    # Obtiene el token desde la variable de entorno
    TOKEN = os.environ.get('TOKEN')
    if not TOKEN:
        raise ValueError("No se encontró el token del bot. Configura la variable de entorno TOKEN.")
    
    application = Application.builder().token(TOKEN).build()

    # Agrega manejadores de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("encrypt", encrypt_message))
    application.add_handler(CommandHandler("decrypt", decrypt_message))
    application.add_handler(CommandHandler("newkey", generate_new_key))
    application.add_handler(CommandHandler("mykey", show_current_key))
    application.add_handler(CommandHandler("stats", show_stats))
    application.add_handler(CommandHandler("admin", admin_stats))

    print("Bot iniciado...")
    application.run_polling()

if __name__ == '__main__':
    main()