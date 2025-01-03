# Bot de Encriptación Telegram

Bot de Telegram para encriptar y desencriptar mensajes con claves personalizadas por usuario.

## Características
- Encriptación y desencriptación de mensajes
- Claves personalizadas por usuario
- Sistema de estadísticas
- Panel de administración

## Configuración

### Variables de Entorno
Crea un archivo `.env` con las siguientes variables:
```
TOKEN=tu_token_de_telegram
ADMIN_ID=tu_id_de_administrador
```

### Instalación
1. Clona el repositorio
2. Instala las dependencias:
```bash
pip install -r requirements.txt
```
3. Configura las variables de entorno
4. Ejecuta el bot:
```bash
python bot.py
```

## Comandos
- `/start` - Inicia el bot
- `/encrypt <mensaje>` - Encripta un mensaje
- `/decrypt <mensaje>` - Desencripta un mensaje
- `/newkey` - Genera una nueva clave
- `/mykey` - Muestra tu clave actual
- `/stats` - Muestra estadísticas de uso
- `/admin` - Panel de administración (solo admins)

## Licencia
MIT
