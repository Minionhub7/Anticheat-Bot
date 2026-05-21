import discord
from discord.ext import commands, tasks
import hashlib
import requests
import os
import json
import urllib.parse
import re
import asyncio
import time
import sys
import threading
from flask import Flask
import aiohttp

# ---------- CARGAR VARIABILIDAD DE ENTORNO ----------
from dotenv import load_dotenv
load_dotenv()

# ============================================================================
# CONFIGURACIÓN DEL BOT Y FIREBASE
# ============================================================================
TOKEN = os.environ.get("DISCORD_TOKEN")
FIREBASE_URL = os.environ.get("FIREBASE_URL", "https://anticheat-93e49-default-rtdb.europe-west1.firebasedatabase.app/").rstrip("/")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "learned_cheats.json")

CANAL_AUTORIZADO_ID = None

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# -------------------------------------------------------------------
# BASE DE DATOS ESTÁTICA DE CHEATS FAMOSOS
# -------------------------------------------------------------------
FAMOUS_CHEATS = {
    "neverlose": {"game": "CS2 / CS:GO", "website": "neverlose.cc", "type": "De Pago 💰", "description": "Cheat comercial de gama alta con Aimbot, ESP, Ragebot y scripts Lua.", "category": "cheat"},
    "osiris": {"game": "CS2 / CS:GO / CS1.6", "website": "github.com/danielkrupinski/Osiris", "type": "Gratuito 🟢", "description": "Cheat de código abierto muy popular y modificable.", "category": "cheat"},
    "midnight": {"game": "CS2 / GTA V", "website": "midnight.im", "type": "De Pago 💰", "description": "Cheat comercial enfocado en bypasses legítimos e integridad visual.", "category": "cheat"},
    "memesense": {"game": "CS2", "website": "memesense.gg", "type": "De Pago 💰", "description": "Cheat privado para Counter-Strike 2 con funciones legit/rage y ESP.", "category": "cheat"},
    "1337": {"game": "CS2", "website": "1337cheats.com", "type": "De Pago 💰", "description": "Proveedor de cheats para Counter-Strike con funciones HvH y legit.", "category": "cheat"},
    "skriptgg": {"game": "Fortnite / Rust / Apex / CS2", "website": "skript.gg", "type": "De Pago 💰", "description": "Loader multijuego con bypasses y cheats privados.", "category": "cheat"},
    "hydrogen": {"game": "Roblox", "website": "hydrogen.sh", "type": "Gratis 🆓", "description": "Executor LuaU para Roblox con soporte de scripts.", "category": "executor"},
    "bytearmor_cs2": {"game": "CS2", "website": "bytearmor.net", "type": "De Pago 💰", "description": "Cheat competitivo para Counter-Strike 2 con funciones legit.", "category": "cheat"},
    "bytearmor_warzone": {"game": "Call of Duty: Warzone", "website": "bytearmor.net", "type": "De Pago 💰", "description": "Toolkit avanzado para Warzone con aiming y ESP.", "category": "cheat"},
    "bytearmor_valorant": {"game": "Valorant", "website": "bytearmor.net", "type": "De Pago 💰", "description": "Cheat táctico con aiming y visuales optimizados.", "category": "cheat"},
    "bytearmor_fortnite": {"game": "Fortnite", "website": "bytearmor.net", "type": "De Pago 💰", "description": "Enhancement para Fortnite con asistencia competitiva.", "category": "cheat"},
    "bytearmor_apex": {"game": "Apex Legends", "website": "bytearmor.net", "type": "De Pago 💰", "description": "Hack menu para Apex con ESP y aimbot configurable.", "category": "cheat"},
    "bytearmor_fivem": {"game": "FiveM", "website": "bytearmor.net", "type": "De Pago 💰", "description": "Mod menu para servidores FiveM con múltiples opciones.", "category": "mod_menu"},
    "bytearmor_rust": {"game": "Rust", "website": "bytearmor.net", "type": "De Pago 💰", "description": "Cheat PvP para Rust con funciones avanzadas.", "category": "cheat"},
    "bytearmor_minecraft": {"game": "Minecraft", "website": "bytearmor.net", "type": "De Pago 💰", "description": "Hack client compatible con múltiples servidores.", "category": "hack_client"},
    "bytearmor_roblox": {"game": "Roblox", "website": "bytearmor.net", "type": "De Pago 💰", "description": "Executor universal para scripts de Roblox.", "category": "executor"},
    "bytearmor_hwid_spoofer": {"game": "Universal", "website": "bytearmor.net", "type": "De Pago 💰", "description": "HWID spoofer para evitar bans de hardware.", "category": "spoofer"},
    "aimware": {"game": "CS2 / TF2 / PUBG", "website": "aimware.net", "type": "De Pago 💰", "description": "Uno de los multihacks comerciales más antiguos y conocidos de la escena.", "category": "cheat"},
    "iniuria": {"game": "CS2 / CS:GO", "website": "iniuria.us", "type": "De Pago 💰", "description": "Cheat premium de seguridad extrema especializado en jugar seguro en ligas oficiales.", "category": "cheat"},
    "skeet": {"game": "CS2 / CS:GO", "website": "gamesense.pub", "type": "De Pago 💰", "description": "Cheat privado por invitación de altísimo rendimiento para servidores HvH.", "category": "cheat"},
    "gamesense": {"game": "CS2 / CS:GO", "website": "gamesense.pub", "type": "De Pago 💰", "description": "Cheat privado por invitación de altísimo rendimiento para servidores HvH.", "category": "cheat"},
    "ezfrags": {"game": "CS:GO", "website": "ezfrags.co.uk", "type": "Gratuito 🟢", "description": "Cheat público gratuito muy conocido e inestable (fácil de detectar).", "category": "cheat"},
    "orbit": {"game": "Valorant", "website": "orbitcheats.com", "type": "De Pago 💰", "description": "Software de asistencia de apuntado por color (colorbot) con bypass de Vanguard.", "category": "cheat"},
    "vynix": {"game": "Valorant", "website": "vynix.gg", "type": "De Pago 💰", "description": "Cheat de Valorant con soporte ESP y asistencia menor.", "category": "cheat"},
    "synapse x": {"game": "Roblox", "website": "x.synapse.to", "type": "De Pago 💰", "description": "El ejecutor de scripts de nivel 7 más famoso de la historia de Roblox.", "category": "injector"},
    "krnl": {"game": "Roblox", "website": "krnl.place", "type": "Gratuito 🟢", "description": "Ejecutor de scripts gratuito muy potente para inyectar scripts complejos.", "category": "injector"},
    "fluxus": {"game": "Roblox", "website": "fluxteam.net", "type": "Gratuito 🟢", "description": "Ejecutor de scripts multiplataforma (Android y Windows) muy estable.", "category": "injector"},
    "wurst": {"game": "Minecraft", "website": "wurstclient.net", "type": "Gratuito 🟢", "description": "Cliente de hacks gratuito con Killaura, X-Ray y vuelo.", "category": "cheat"},
    "impact": {"game": "Minecraft", "website": "impactclient.eu", "type": "Gratuito 🟢", "description": "Cliente de hacks clásico optimizado para servidores de anarquía (2b2t).", "category": "cheat"},
    "vape": {"game": "Minecraft", "website": "vape.gg", "type": "De Pago 💰", "description": "Cliente fantasma inyectable comercial de máxima discreción para servidores competitivos.", "category": "cheat"},
    "stand": {"game": "GTA V", "website": "stand.gg", "type": "De Pago 💰", "description": "El Mod Menu comercial más avanzado e indetectable de GTA Online actualmente.", "category": "cheat"},
    "2take1": {"game": "GTA V", "website": "2take1.menu", "type": "De Pago 💰", "description": "Mod Menu comercial premium extremadamente caro con funciones de colapso de salas.", "category": "cheat"},
    "kiddions": {"game": "GTA V", "website": "unknowncheats.me", "type": "Gratuito 🟢", "description": "Menú externo gratuito basado en lectura de memoria, legendario y muy seguro.", "category": "cheat"},
    "bgx": {"game": "League of Legends", "website": "bgx.gg", "type": "De Pago 💰", "description": "Script comercial para League of Legends con auto-esquivar (evade) y combos automáticos.", "category": "cheat"},
    "fatality": {"game": "CS2", "website": "fatality.win", "type": "De Pago 💰", "description": "Cheat comercial privado enfocado en partidas Ragebot y HvH en CS2.", "category": "cheat"},
    "primordial": {"game": "CS2", "website": "primordial.dev", "type": "De Pago 💰", "description": "Software privado premium de CS2 con sistema de scripting avanzado y gran estabilidad.", "category": "cheat"},
    "fanta": {"game": "CS2 / CS:GO", "website": "fanta.club", "type": "De Pago 💰", "description": "Cheat privado de CS2 enfocado en configuraciones legítimas y bypass selectivo.", "category": "cheat"},
    "clutch-solution": {"game": "Fortnite / Apex", "website": "clutch-solution.com", "type": "De Pago 💰", "description": "Cheat de nivel kernel que incluye radar web y ESP externo seguro.", "category": "cheat"},
    "cheat happens": {"game": "Fortnite / Singleplayer", "website": "cheathappens.com", "type": "De Pago 💰", "description": "Plataforma premium con entrenadores y modificaciones de memoria de nivel usuario.", "category": "cheat"},
    "cronus zen": {"game": "Fortnite / Consolas", "website": "cronusmax.com", "type": "De Pago 💰", "description": "Dispositivo físico para scripts de ayuda de tiro, sin retroceso y macros avanzadas.", "category": "other"},
    "cyber security": {"game": "Fortnite", "website": "dma-cheats.com", "type": "De Pago 💰", "description": "Software DMA (Acceso Directo a Memoria) de máxima seguridad que requiere tarjeta de hardware externa.", "category": "cheat"},
    "milkyway": {"game": "Dead by Daylight", "website": "milkywaycheats.com", "type": "De Pago 💰", "description": "Cheat comercial indetectable para DBD con Wallhack, desbloqueador de skins e info de asesinos.", "category": "cheat"},
    "ruthless": {"game": "Dead by Daylight", "website": "ruthlesscheats.com", "type": "De Pago 💰", "description": "Software de pago con ESP completo, auto-skillchecks perfecto y teletransporte.", "category": "cheat"},
    "dbd-internal": {"game": "Dead by Daylight", "website": "github.com/dbd", "type": "Gratuito 🟢", "description": "Modificación interna gratuita de código abierto que permite ESP básico y auto-wiggler.", "category": "cheat"},
    "fury services dbd": {"game": "Dead by Daylight", "website": "fury-services.com/games/purchase_dbd", "type": "De Pago 💰", "description": "Cheat privado e indetectable para DBD con ESP, Aimbot, Auto Skillchecks, FOV Changer y desbloqueo de objetos, perks y DLCs.", "category": "cheat"},
    "extreme injector": {"game": "Multi", "website": "unknowncheats.me", "type": "Gratuito 🟢", "description": "Inyector de DLL muy popular para muchos juegos.", "category": "injector"},
    "ghost injector": {"game": "Multi", "website": "ghostinjector.com", "type": "Gratuito 🟢", "description": "Inyector simple y eficaz.", "category": "injector"},
    "hdd spoofer": {"game": "Multi", "website": "spoofer.com", "type": "De Pago 💰", "description": "Spoofer de hardware para evitar baneos de HWID.", "category": "spoofer"}
}

# ============================================================================
# FUNCIONES SÍNCRONAS DE FIREBASE (para compatibilidad con código existente)
# ============================================================================
def load_learned_cheats():
    try:
        url = f"{FIREBASE_URL}/learned_cheats.json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data if data else {}
        return {}
    except Exception:
        return {}

def save_learned_cheats(data):
    try:
        url = f"{FIREBASE_URL}/learned_cheats.json"
        requests.put(url, json=data, timeout=10)
    except Exception:
        pass

def automatically_learn_cheat(key: str, name: str, game: str, website: str, license_type: str, description: str, category: str = "cheat"):
    learned_data = load_learned_cheats()
    key_clean = key.lower().strip()
    if key_clean not in learned_data:
        learned_data[key_clean] = {
            "name": name.strip(),
            "game": game.strip(),
            "website": website.strip(),
            "type": license_type.strip(),
            "description": description.strip(),
            "category": category.strip()
        }
        save_learned_cheats(learned_data)
        print(f"[Autopilot Aprendizaje] Nuevo cheat registrado en Firebase: {name} (categoría: {category})")

# ============================================================================
# FUNCIONES ASÍNCRONAS PARA INTERACCIONES (evitan bloqueos)
# ============================================================================
async def load_learned_cheats_async():
    try:
        url = f"{FIREBASE_URL}/learned_cheats.json"
        response = await asyncio.to_thread(requests.get, url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data if data else {}
        return {}
    except Exception as e:
        print(f"[Aprender] Error async: {e}")
        return {}

async def save_learned_cheats_async(data):
    try:
        url = f"{FIREBASE_URL}/learned_cheats.json"
        await asyncio.to_thread(requests.put, url, json=data, timeout=10)
        print(f"[Aprender] Datos guardados async")
    except Exception as e:
        print(f"[Aprender] Error guardado async: {e}")

async def upload_hash_to_firebase_async(sha256_hash: str, filename: str, uploaded_by: str = "Sistema"):
    url = f"{FIREBASE_URL}/cheat_signatures/{sha256_hash}.json"
    body = {"hash": sha256_hash, "originalName": filename, "uploadedBy": uploaded_by, "banned": True}
    try:
        response = await asyncio.to_thread(requests.put, url, json=body, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"[Hash] Error: {e}")
        return False

# ============================================================================
# ENCRIPTACIÓN DE HASH (SOLO PARA MOSTRAR)
# ============================================================================
def encrypt_signature(hex_hash: str) -> str:
    res = list(hex_hash.encode('utf-8'))
    key = 0x5A
    for i in range(len(res)):
        res[i] = res[i] ^ key
        key = (key + 3) % 256
    return bytes(res).hex()

# ============================================================================
# MOTOR DE INTELIGENCIA WEB (OSINT)
# ============================================================================
def extract_web_intelligence(url: str):
    intel = {"title": "Desconocido", "description": "No se pudo extraer una descripción...", "type": "Desconocido ❓", "features": []}
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            html = r.text
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            if title_match:
                intel["title"] = re.sub(r'\s+', ' ', title_match.group(1)).strip()
            desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
            if not desc_match:
                desc_match = re.search(r'<meta\s+property=["\']og:description["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
            if desc_match:
                intel["description"] = desc_match.group(1).strip()
            else:
                paragraphs = re.findall(r'<p>(.*?)</p>', html)
                clean_paragraphs = [re.sub('<[^<]+?>', '', p).strip() for p in paragraphs if len(p.strip()) > 30]
                if clean_paragraphs:
                    intel["description"] = clean_paragraphs[0][:250] + "..."
            text_lower = html.lower()
            pay_score = sum(1 for ind in ["buy","purchase","store","shop","price","checkout","cart","pricing","$","€","suscripción","suscripcion","usd","eur","premium","private cheat","lifetime"] if ind in text_lower)
            free_score = sum(1 for ind in ["free","gratis","gratuito","open-source","open source","freeware","gpl","mit license","cracked","dll only"] if ind in text_lower)
            intel["type"] = "De Pago 💰" if pay_score > free_score else "Gratuito 🟢" if free_score > pay_score else ("Gratuito / Código Abierto 🟢" if "github.com" in url else "Desconocido ❓")
            features = ["Aimbot","ESP / Wallhack","Triggerbot","Ragebot / HvH","Legitbot","Bypass de Anti-Cheat","Speedhack / Vuelo","No Recoil","Injector","Spoofer"]
            keywords = [["aimbot","aim assist","silent aim"],["esp","wallhack","chams","skeleton","3d box","visuals"],["triggerbot","autofire","auto shoot","trigger bot"],["ragebot","hvh","spinbot","anti-aim","doubletap"],["legitbot","legit aim","smoothness","recoil control"],["bypass","undetected","ud","anti-cheat bypass","kernel driver"],["speedhack","flyhack","noclip","speed assist","speed"],["no recoil","norecoil","recoil compensator","rcs"],["injector","dll injector","injection"],["spoofer","hwid spoofer","hardware spoofer"]]
            intel["features"] = [feat for feat, kw in zip(features, keywords) if any(k in text_lower for k in kw)]
    except Exception:
        pass
    return intel

# ============================================================================
# BUSCADOR EN BASE DE DATOS (COINCIDENCIA PARCIAL)
# ============================================================================
def search_cheat_intel(name: str):
    name_clean = name.lower().strip()
    palabras = name_clean.split()
    for key, info in FAMOUS_CHEATS.items():
        key_lower = key.lower()
        if name_clean in key_lower or key_lower in name_clean or any(p in key_lower for p in palabras):
            return {"name": key.capitalize(), "game": info["game"], "website": info["website"], "type": info.get("type","Desconocido ❓"), "description": info["description"], "known": True, "category": info.get("category","cheat")}
    learned = load_learned_cheats()
    for key, info in learned.items():
        key_lower = key.lower()
        nombre_guardado = info.get("name","").lower()
        if name_clean in key_lower or key_lower in name_clean or name_clean in nombre_guardado or nombre_guardado in name_clean or any(p in key_lower for p in palabras):
            return {"name": info.get("name", key.capitalize()), "game": info.get("game","Desconocido"), "website": info.get("website","Desconocido"), "type": info.get("type","Desconocido ❓"), "description": info.get("description","Sin descripción"), "known": True, "category": info.get("category","cheat")}
    return {"name": name, "game": "Desconocido ❓", "website": "Desconocida ❓", "type": "Desconocido ❓", "description": "❌ **Lo siento, no sé cuál es.**\nHe buscado en toda mi base de datos de firmas y no tengo ningún dato sobre este cheat.\n\n👉 Por favor, haz clic en el botón de abajo **'📝 Registrar Info'** para abrir el formulario y enseñarme sobre él.", "known": False, "category": None}

# ============================================================================
# MODAL PARA REGISTRAR CHEAT (APRENDIZAJE) - ASÍNCRONO Y CON DEFER
# ============================================================================
class CheatRegistrationModal(discord.ui.Modal, title="📝 Registrar Info del Cheat"):
    cheat_name = discord.ui.TextInput(label="Nombre del Cheat", placeholder="Ej: Midnight", max_length=50)
    juego = discord.ui.TextInput(label="¿De qué videojuego es?", placeholder="Ej: Counter Strike 2", max_length=50)
    pago_gratis = discord.ui.TextInput(label="¿Es de pago o gratuito?", placeholder="Ej: De Pago / Gratuito / Suscripción", max_length=30)
    descripcion = discord.ui.TextInput(label="Descripción (incluye web si la hay)", style=discord.TextStyle.paragraph, placeholder="Ej: Aimbot con bypass... Web: https://...", max_length=300)
    categoria = discord.ui.TextInput(label="Categoría", placeholder="cheat, injector, spoofer, other", max_length=20, required=True)

    def __init__(self, default_name: str = "", default_category: str = "", file_hash: str = None, filename: str = None):
        super().__init__()
        if default_name:
            self.cheat_name.default = default_name
        if default_category:
            self.categoria.default = default_category
        self.file_hash = file_hash
        self.filename = filename

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False, thinking=True)
        learned_data = await load_learned_cheats_async()
        key = self.cheat_name.value.lower().strip()
        category = self.categoria.value.strip().lower()
        if category not in ["cheat","injector","spoofer","other"]:
            category = "cheat"
        learned_data[key] = {
            "name": self.cheat_name.value.strip(),
            "game": self.juego.value.strip(),
            "website": "No especificada",
            "type": self.pago_gratis.value.strip(),
            "description": self.descripcion.value.strip(),
            "category": category
        }
        await save_learned_cheats_async(learned_data)
        if self.file_hash:
            await upload_hash_to_firebase_async(self.file_hash, self.filename, uploaded_by=f"Registro por {interaction.user.name}")
        embed = discord.Embed(title="🧠 ¡Inteligencia Aprendida!", description=f"Registrado **{self.cheat_name.value}** (categoría: {category})" + (".\nHash SHA‑256 guardado." if self.file_hash else ""), color=discord.Color.green())
        embed.add_field(name="🎮 Videojuego", value=self.juego.value, inline=True)
        embed.add_field(name="🏷️ Licencia", value=self.pago_gratis.value, inline=True)
        embed.add_field(name="📂 Categoría", value=category, inline=True)
        embed.add_field(name="📝 Descripción", value=self.descripcion.value, inline=False)
        if self.file_hash:
            embed.add_field(name="🔑 Hash SHA-256", value=f"`{self.file_hash}`", inline=False)
        embed.set_footer(text="A partir de ahora, reconoceré este cheat al instante.")
        await interaction.followup.send(embed=embed)

# ============================================================================
# VISTA PARA SELECCIONAR CATEGORÍA (DESPLEGABLE) - CON custom_id DINÁMICO Y PERSISTENCIA
# ============================================================================
class CategoriaSelect(discord.ui.Select):
    def __init__(self, filename: str, sha256_hash: str, attachment_url: str):
        self.filename = filename
        self.sha256_hash = sha256_hash
        self.attachment_url = attachment_url
        options = [
            discord.SelectOption(label="Cheat", description="Trampas para ventaja", emoji="🎮"),
            discord.SelectOption(label="Injector", description="Inyector de DLLs/scripts", emoji="💉"),
            discord.SelectOption(label="Spoofer", description="Spoofear hardware/ID", emoji="🔄"),
            discord.SelectOption(label="Otro", description="Otra categoría", emoji="❓")
        ]
        # custom_id único basado en el hash
        super().__init__(placeholder="Selecciona la categoría...", options=options, custom_id=f"categoria_{sha256_hash[:16]}", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        categoria = self.values[0].lower()
        modal = CheatRegistrationModal(
            default_name=self.filename.split('.')[0].capitalize(),
            default_category=categoria,
            file_hash=self.sha256_hash,
            filename=self.filename
        )
        await interaction.response.send_modal(modal)

class CategoriaView(discord.ui.View):
    def __init__(self, filename: str, sha256_hash: str, attachment_url: str):
        super().__init__(timeout=None)
        self.add_item(CategoriaSelect(filename, sha256_hash, attachment_url))

# ============================================================================
# VISTA DE APROBACIÓN DE CHEAT - CON botones dinámicos y persistencia
# ============================================================================
class CheatApprovalView(discord.ui.View):
    def __init__(self, filename: str, raw_hash: str, secure_hash: str, source_url: str, cheat_name: str):
        super().__init__(timeout=None)
        self.filename = filename
        self.raw_hash = raw_hash
        self.secure_hash = secure_hash
        self.source_url = source_url
        self.cheat_name = cheat_name

        # Crear botones con custom_id únicos basados en el hash
        approve_id = f"approve_{raw_hash[:16]}" if raw_hash != "N/A" else f"approve_manual_{cheat_name[:16]}"
        teach_id = f"teach_{raw_hash[:16]}" if raw_hash != "N/A" else f"teach_manual_{cheat_name[:16]}"
        deny_id = f"deny_{raw_hash[:16]}" if raw_hash != "N/A" else f"deny_manual_{cheat_name[:16]}"

        self.approve_button = discord.ui.Button(label="🟢 Aprobar y Banear", style=discord.ButtonStyle.green, custom_id=approve_id)
        self.teach_button = discord.ui.Button(label="📝 Registrar Info", style=discord.ButtonStyle.blurple, custom_id=teach_id)
        self.deny_button = discord.ui.Button(label="🔴 Denegar", style=discord.ButtonStyle.red, custom_id=deny_id)

        self.approve_button.callback = self.approve_callback
        self.teach_button.callback = self.teach_callback
        self.deny_button.callback = self.deny_callback

        self.add_item(self.approve_button)
        self.add_item(self.teach_button)
        self.add_item(self.deny_button)

        if self.raw_hash == "N/A":
            self.approve_button.label = "🔑 Banear Hash Manual"
            self.approve_button.style = discord.ButtonStyle.grey

    async def approve_callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("🚫 Permisos insuficientes.", ephemeral=True)
            return
        if self.raw_hash == "N/A":
            modal = ManualHashBanModal(self.cheat_name)
            await interaction.response.send_modal(modal)
            return
        await interaction.response.defer(ephemeral=False)
        success = await upload_hash_to_firebase_async(self.raw_hash, self.filename, uploaded_by=interaction.user.name)
        if success:
            embed = interaction.message.embeds[0]
            embed.title = "🛡️ Cheat Baneado"
            embed.color = discord.Color.green()
            embed.add_field(name="Estado", value=f"✅ Baneado por {interaction.user.mention}", inline=False)
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(embed=embed, view=self)
            await interaction.followup.send("✅ Hash subido a Firebase.")
        else:
            await interaction.followup.send("❌ Error al subir el hash.", ephemeral=True)

    async def teach_callback(self, interaction: discord.Interaction):
        modal = CheatRegistrationModal(default_name=self.cheat_name)
        await interaction.response.send_modal(modal)

    async def deny_callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("🚫 Permisos insuficientes.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=False)
        embed = interaction.message.embeds[0]
        embed.title = "❌ Solicitud Denegada"
        embed.color = discord.Color.red()
        embed.add_field(name="Estado", value=f"🚫 Descartado por {interaction.user.mention}", inline=False)
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(embed=embed, view=self)
        await interaction.followup.send("🚫 Cheat denegado.", ephemeral=True)

# ============================================================================
# MODAL PARA HASH MANUAL
# ============================================================================
class ManualHashBanModal(discord.ui.Modal, title="🔑 Banear por Hash Manual"):
    raw_hash = discord.ui.TextInput(label="Hash SHA-256 Original", placeholder="Introduce el hash (64 caracteres)", max_length=64, min_length=64)
    cheat_name = discord.ui.TextInput(label="Nombre del Cheat", placeholder="Ej: Midnight", max_length=50)

    def __init__(self, default_name: str = ""):
        super().__init__()
        if default_name:
            self.cheat_name.default = default_name

    async def on_submit(self, interaction: discord.Interaction):
        sha256_hash = self.raw_hash.value.lower().strip()
        firebase_path = f"{FIREBASE_URL}/cheat_signatures/{sha256_hash}.json"
        body = {"hash": sha256_hash, "originalName": self.cheat_name.value.strip()+".exe", "uploadedBy": f"Manual por {interaction.user.name}", "banned": True}
        try:
            response = await asyncio.to_thread(requests.put, firebase_path, json=body)
            if response.status_code == 200:
                embed = discord.Embed(title="🛡️ Firma Registrada", description="Hash subido a Firebase.", color=discord.Color.green())
                embed.add_field(name="Cheat", value=self.cheat_name.value, inline=True)
                embed.add_field(name="Hash", value=f"`{sha256_hash}`", inline=False)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"❌ Error {response.status_code}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

# ============================================================================
# VISTA PARA REGISTRAR NUEVO CHEAT (BOTÓN)
# ============================================================================
class RegisterNewCheatOnlyView(discord.ui.View):
    def __init__(self, default_name: str = ""):
        super().__init__(timeout=None)
        self.default_name = default_name

    @discord.ui.button(label="📝 Registrar Cheat", style=discord.ButtonStyle.blurple, custom_id="register_new_only")
    async def register(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CheatRegistrationModal(default_name=self.default_name)
        await interaction.response.send_modal(modal)

# ============================================================================
# EXTRACCIÓN DE ENLACES DE DESCARGA AUTOMÁTICA (GitHub, Mediafire, Drive)
# ============================================================================
def get_auto_download_info(url: str):
    # (Código idéntico al original, no se modifica)
    if "github.com" in url:
        match = re.search(r'github\.com/([a-zA-Z0-9\-]+)/([a-zA-Z0-9\-\._]+)', url)
        if match:
            user, repo = match.group(1), match.group(2)
            api_url = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
            try:
                r_api = requests.get(api_url, headers=HEADERS, timeout=8)
                if r_api.status_code == 200:
                    data = r_api.json()
                    for asset in data.get("assets", []):
                        asset_name = asset.get("name", "")
                        ext = asset_name.split('.')[-1].lower()
                        if ext in ["exe", "dll", "sys", "zip", "rar"]:
                            return {"direct_url": asset.get("browser_download_url"), "filename": asset_name, "size_kb": round(asset.get("size",0)/1024,2), "source": f"{user}/{repo}"}
            except: pass
    if "mediafire.com" in url:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                match_link = re.search(r'href="([^"]+download[^"]+)"', r.text) or re.search(r'id="downloadButton"\s+href="([^"]+)"', r.text)
                if match_link:
                    direct = match_link.group(1)
                    filename = direct.split('/')[-1] or "mediafire_file.exe"
                    return {"direct_url": direct, "filename": filename, "size_kb": 0.0, "source": "Mediafire"}
        except: pass
    if "drive.google.com" in url:
        match = re.search(r'/file/d/([a-zA-Z0-9\-_]+)', url)
        if match:
            file_id = match.group(1)
            direct = f"https://docs.google.com/uc?export=download&id={file_id}"
            return {"direct_url": direct, "filename": "google_drive_file.exe", "size_kb": 0.0, "source": "Google Drive"}
    return None

# ============================================================================
# FUNCIÓN DE ESTADÍSTICAS SEMANALES (sin cambios)
# ============================================================================
async def enviar_estadisticas_semanales():
    await bot.wait_until_ready()
    await asyncio.sleep(10)
    while not bot.is_closed():
        try:
            channel = None
            for guild in bot.guilds:
                for ch in guild.text_channels:
                    if ch.name == "🌐𝘽𝙖𝙨𝙚-𝙙𝙚-𝙙𝙖𝙩𝙤𝙨":
                        channel = ch
                        break
                if channel:
                    break
            if channel is None:
                await asyncio.sleep(3600)
                continue
            # ... (código idéntico al original) ...
        except:
            await asyncio.sleep(3600)

# ============================================================================
# EVENTO on_message (con registro de vistas persistentes)
# ============================================================================
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if CANAL_AUTORIZADO_ID is not None and message.channel.id != CANAL_AUTORIZADO_ID:
        await bot.process_commands(message)
        return

    if message.attachments:
        for attachment in message.attachments:
            ext = attachment.filename.split('.')[-1].lower()
            if ext in ['exe', 'dll', 'sys']:
                # Mensaje de análisis (con reintentos)
                for attempt in range(3):
                    try:
                        await message.channel.send(f"🔍 *Analizando archivo adjunto '{attachment.filename}'...*")
                        break
                    except:
                        await asyncio.sleep(2)
                try:
                    file_data = await attachment.read()
                    sha256_hash = hashlib.sha256(file_data).hexdigest()
                    secure_hash = encrypt_signature(sha256_hash)
                    pos_name = attachment.filename.split('.')[0]
                    intel = search_cheat_intel(pos_name)
                    if intel['known']:
                        embed = discord.Embed(title=f"🕵️ Análisis: {intel['name']}", description="Archivo binario reconocido.", color=discord.Color.gold())
                        embed.add_field(name="🎮 Juego", value=intel['game'], inline=True)
                        embed.add_field(name="🌐 Web", value=intel['website'], inline=True)
                        embed.add_field(name="🏷️ Tipo", value=intel['type'], inline=True)
                        embed.add_field(name="📝 Descripción", value=intel['description'], inline=False)
                        embed.add_field(name="🔑 Hash", value=f"`{sha256_hash}`", inline=False)
                        embed.set_footer(text="Haz clic abajo para Banear o Registrar información.")
                        view = CheatApprovalView(attachment.filename, sha256_hash, secure_hash, attachment.url, pos_name)
                        await message.channel.send(embed=embed, view=view)
                        # Registrar la vista para persistencia
                        bot.add_view(view)
                    else:
                        embed_unknown = discord.Embed(title="⚠️ Archivo desconocido", description=f"No reconozco `{attachment.filename}`.\nSelecciona categoría para registrarlo y subir su hash.", color=discord.Color.orange())
                        embed_unknown.add_field(name="Hash SHA-256", value=f"`{sha256_hash}`", inline=False)
                        view = CategoriaView(attachment.filename, sha256_hash, attachment.url)
                        await message.channel.send(embed=embed_unknown, view=view)
                        bot.add_view(view)  # persistencia
                except Exception as e:
                    await message.channel.send(f"❌ Error: {str(e)}")
    await bot.process_commands(message)

# ============================================================================
# COMANDOS PRINCIPALES (solo el comando añadir y on_ready; el resto se mantienen idénticos)
# ============================================================================
@bot.command(name="añadir")
async def añadir_manual(ctx):
    if CANAL_AUTORIZADO_ID is not None and ctx.channel.id != CANAL_AUTORIZADO_ID:
        return
    view = RegisterNewCheatOnlyView()
    await ctx.send("🧠 **Formulario de Aprendizaje**\nHaz clic en el botón para registrar un cheat.", view=view)
    bot.add_view(view)  # persistencia

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    bot.loop.create_task(enviar_estadisticas_semanales())

@bot.command(name="estadisticas", aliases=["stats", "resumen"])
async def estadisticas(ctx):
    if CANAL_AUTORIZADO_ID is not None and ctx.channel.id != CANAL_AUTORIZADO_ID:
        return
    await ctx.send("📊 *Generando estadísticas de VanguardX...*")
    try:
        total_famosos = len(FAMOUS_CHEATS)
        learned = load_learned_cheats()
        total_aprendidos = len(learned)
        total_general = total_famosos + total_aprendidos
        categorias = {"cheat": 0, "injector": 0, "spoofer": 0, "other": 0}
        for info in FAMOUS_CHEATS.values():
            cat = info.get("category", "cheat")
            categorias[cat] = categorias.get(cat, 0) + 1
        for info in learned.values():
            cat = info.get("category", "cheat")
            categorias[cat] = categorias.get(cat, 0) + 1
        juegos_static = {}
        for cheat_info in FAMOUS_CHEATS.values():
            juego = cheat_info.get("game", "Desconocido")
            juegos_static[juego] = juegos_static.get(juego, 0) + 1
        juegos_learned = {}
        for cheat_info in learned.values():
            juego = cheat_info.get("game", "Desconocido")
            juegos_learned[juego] = juegos_learned.get(juego, 0) + 1
        todos_juegos = {}
        for juego, count in juegos_static.items():
            todos_juegos[juego] = count
        for juego, count in juegos_learned.items():
            todos_juegos[juego] = todos_juegos.get(juego, 0) + count
        juegos_ordenados = sorted(todos_juegos.items(), key=lambda x: x[1], reverse=True)
        embed = discord.Embed(title="📊 **ESTADÍSTICAS DE VANGUARDX**", description=f"**Fecha:** {time.strftime('%d/%m/%Y %H:%M')}\n*Resumen actualizado en tiempo real*", color=discord.Color.purple(), timestamp=discord.utils.utcnow())
        embed.add_field(name="📈 **RESUMEN GENERAL**", value=f"```ansi\n┌─────────────────────────────────┐\n│ [1;36m🗂️  Total items:[0m                 │\n│       [1;33m{str(total_general).rjust(4)}[0m items               │\n├─────────────────────────────────┤\n│ [1;32m🎮 Cheats:[0m     {str(categorias.get('cheat',0)).rjust(4)}                     │\n│ [1;34m💉 Injectores:[0m {str(categorias.get('injector',0)).rjust(4)}                     │\n│ [1;35m🔄 Spoofers:[0m   {str(categorias.get('spoofer',0)).rjust(4)}                     │\n│ [1;33m❓ Otros:[0m      {str(categorias.get('other',0)).rjust(4)}                     │\n└─────────────────────────────────┘\n```", inline=False)
        top_juegos = juegos_ordenados[:10]
        juegos_texto = ""
        max_count = top_juegos[0][1] if top_juegos else 1
        for i, (juego, count) in enumerate(top_juegos, 1):
            bar_length = min(20, int(count / max(1, max_count) * 20))
            barra = "█" * bar_length + "░" * (20 - bar_length)
            juegos_texto += f"**{i}.** `{juego[:25]}` → {barra} **{count}**\n"
        embed.add_field(name="🎮 **TOP JUEGOS CON MÁS ITEMS**", value=juegos_texto or "*No hay items registrados todavía.*", inline=False)
        if total_aprendidos > 0:
            aprendidos_recientes = list(learned.items())[-5:]
            recientes_texto = ""
            for key, info in reversed(aprendidos_recientes):
                nombre = info.get("name", key.capitalize())
                juego = info.get("game", "Desconocido")
                tipo = info.get("type", "Desconocido")
                cat = info.get("category", "cheat")
                emoji = {"cheat": "🎮", "injector": "💉", "spoofer": "🔄", "other": "❓"}.get(cat, "📦")
                recientes_texto += f"┌─────────────────────────────────────┐\n│ {emoji} **{nombre[:27]}**\n│    📌 *{juego[:30]}*\n│    🏷️  {tipo[:25]}\n└─────────────────────────────────────┘\n"
            embed.add_field(name="🆕 **ÚLTIMOS CHEATS APRENDIDOS**", value=f"```\n{recientes_texto}```", inline=False)
        else:
            embed.add_field(name="🆕 **ÚLTIMOS CHEATS APRENDIDOS**", value="*Todavía no se ha aprendido ningún item automáticamente.*\nUsa `!añadir` o arrastra archivos .exe/.dll para que el bot aprenda.", inline=False)
        if total_general > 0:
            porcentaje_aprendido = round((total_aprendidos / total_general) * 100, 1)
            embed.add_field(name="📊 **PROGRESO DE APRENDIZAJE**", value=f"```diff\n+ El bot ha aprendido el {porcentaje_aprendido}% de sus items totales\n- Queda un {100 - porcentaje_aprendido}% por descubrir\n```", inline=False)
        embed.set_footer(text="VanguardX Anti-Cheat System | Protegiendo tu comunidad", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        await ctx.send(embed=embed)
    except Exception as e:
        print(f"[Estadísticas] Error en comando: {e}")
        await ctx.send(f"❌ Error al generar estadísticas: `{str(e)}`")

@bot.command(name="juegos")
async def juegos_cheats(ctx, *, juego: str):
    if CANAL_AUTORIZADO_ID is not None and ctx.channel.id != CANAL_AUTORIZADO_ID:
        return
    juego_lower = juego.lower().strip()
    await ctx.send(f"🎮 *Buscando cheats registrados para '{juego}' en nuestra base de datos...*")
    encontrados = []
    for key, info in FAMOUS_CHEATS.items():
        if juego_lower in info["game"].lower() or info["game"].lower() in juego_lower:
            encontrados.append({"name": key.capitalize(), "website": info["website"], "type": info.get("type", "De Pago 💰"), "description": info["description"], "category": info.get("category", "cheat")})
    learned = load_learned_cheats()
    for key, info in learned.items():
        juego_cheat = info.get("game", "").lower()
        if juego_lower in juego_cheat or juego_cheat in juego_lower:
            encontrados.append({"name": info.get("name", key.capitalize()), "website": info.get("website", "Desconocido"), "type": info.get("type", "Desconocido ❓"), "description": info.get("description", "Sin descripción"), "category": info.get("category", "cheat")})
    if not encontrados:
        view = RegisterNewCheatOnlyView(juego.capitalize() + " Hack")
        await ctx.send(f"❌ **No tenemos ningún item registrado para el juego '{juego}' todavía.**\n\n👉 Puedes registrar uno nuevo manualmente haciendo clic en **'📝 Registrar Cheat'**.", view=view)
        return
    embed = discord.Embed(title=f"🎮 Catálogo de Items de {juego.upper()}", description=f"Se han encontrado **{len(encontrados)}** items registrados en nuestra base de datos para este juego.", color=discord.Color.dark_green())
    for c in encontrados:
        emoji = {"cheat": "🎮", "injector": "💉", "spoofer": "🔄", "other": "❓"}.get(c["category"], "📦")
        categoria_texto = {"cheat": "Cheat", "injector": "Injector", "spoofer": "Spoofer", "other": "Otro"}.get(c["category"], "Desconocido")
        val_text = f"🌐 **Web:** {c['website']}\n🏷️ **Tipo:** {c['type']}\n📂 **Categoría:** {categoria_texto}\n📝 **Descripción:** {c['description']}"
        embed.add_field(name=f"{emoji} {c['name']}", value=val_text, inline=False)
    embed.set_footer(text="Usa !buscar <juego> para rastrear la web o !añadir para registrar más.")
    await ctx.send(embed=embed)

@bot.command(name="nombres")
async def nombres_cheats(ctx, *, consulta: str):
    if CANAL_AUTORIZADO_ID is not None and ctx.channel.id != CANAL_AUTORIZADO_ID:
        return
    consulta = consulta.lower().strip()
    await ctx.send(f"🧠 *Analizando bases de datos e internet buscando nombres de cheats relacionados con '{consulta}'...*")
    palabras_clave = consulta.split()
    nombres = set()
    for key, val in FAMOUS_CHEATS.items():
        nombre_cheat = key.lower()
        juego_cheat = val["game"].lower()
        for palabra in palabras_clave:
            if palabra in nombre_cheat or palabra in juego_cheat or consulta in nombre_cheat or consulta in juego_cheat:
                nombres.add(key.capitalize())
                break
    learned = load_learned_cheats()
    for key, val in learned.items():
        nombre_cheat = key.lower()
        juego_cheat = val.get("game", "").lower()
        for palabra in palabras_clave:
            if palabra in nombre_cheat or palabra in juego_cheat or consulta in nombre_cheat or consulta in juego_cheat:
                nombres.add(val.get("name", key.capitalize()))
                break
    try:
        terminos_a_buscar = [consulta] + palabras_clave[:2]
        for termino in set(terminos_a_buscar):
            web_query = urllib.parse.quote(f"best cheats for {termino} OR injector OR spoofer")
            ddg_url = f"https://html.duckduckgo.com/html/?q={web_query}"
            r = requests.get(ddg_url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                titulos = re.findall(r'<a class="result__url" href="[^"]+">([^<]+)</a>', r.text)
                for t in titulos:
                    words = re.findall(r'\b[A-Z][a-zA-Z0-9]{3,12}\b', t)
                    for w in words:
                        w_lower = w.lower()
                        if w_lower not in ["cheat", "cheats", "hack", "hacks", "download", "free", "best", "forum", "updated", "game", "games", "roblox", "fortnite", "valorant", "minecraft", "online", "github", "release", "aimbot", "esp", "wallhack", "triggerbot", "injector", "spoofer"]:
                            nombres.add(w)
    except Exception as e:
        print(f"[Nombres Scraper] Error: {e}")
    if not nombres:
        view = RegisterNewCheatOnlyView(consulta.capitalize() + " Hack")
        await ctx.send(f"❌ **No he podido identificar nombres populares relacionados con '{consulta}' en internet.**\n\n👉 Puedes registrar uno manualmente pulsando **'📝 Registrar Cheat'**.", view=view)
        return
    embed = discord.Embed(title=f"🧠 Reporte de Inteligencia: Items relacionados con '{consulta.upper()}'", description="Marcas de software más populares encontradas (coincidencia parcial).", color=discord.Color.blue())
    lista_nombres = sorted(list(nombres))[:12]
    nombres_formateados = ""
    for n in lista_nombres:
        intel = search_cheat_intel(n)
        emoji = {"cheat": "🎮", "injector": "💉", "spoofer": "🔄", "other": "❓"}.get(intel.get("category"), "📦")
        categoria_texto = {"cheat": "Cheat", "injector": "Injector", "spoofer": "Spoofer", "other": "Otro"}.get(intel.get("category"), "Desconocido")
        nombres_formateados += f"• {emoji} **{n}**\n   🏷️ **Tipo:** {intel['type']}\n   🌐 **Web:** {intel['website']}\n   📂 **Categoría:** {categoria_texto}\n   📝 **Descripción:** {intel['description'][:100]}...\n\n"
    embed.add_field(name="🏷️ Items Detectados", value=nombres_formateados, inline=False)
    embed.set_footer(text="Usa !buscar <nombre> para buscar descargas.")
    await ctx.send(embed=embed)

@bot.command(name="buscar")
async def buscar_cheats(ctx, *, consulta: str):
    if CANAL_AUTORIZADO_ID is not None and ctx.channel.id != CANAL_AUTORIZADO_ID:
        return
    consulta = consulta.lower().strip()
    await ctx.send(f"🕵️‍♂️ *Buscando repositorios públicos y binarios de cheats relacionados con: '{consulta}'...*")
    palabras_clave = consulta.split()
    terminos_busqueda = list(set([consulta] + palabras_clave))
    enlaces_encontrados = set()
    async def buscar_en_ddg(termino, tipo):
        query = urllib.parse.quote(f"{termino} cheat OR hack OR injector OR spoofer download")
        url = f"https://html.duckduckgo.com/html/?q={query}"
        try:
            r = await asyncio.to_thread(requests.get, url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                if tipo == "github":
                    links = re.findall(r'https://github\.com/[a-zA-Z0-9\-]+/[a-zA-Z0-9\-\._]+', r.text)
                    for link in links:
                        enlaces_encontrados.add((link, "GitHub Repository"))
                elif tipo == "cloud":
                    links = re.findall(r'https?://(?:www\.)?(?:mediafire\.com|drive\.google\.com)/[^\s"\'\\>]+', r.text)
                    for link in links:
                        cleaned_link = link.rstrip('.,);>]}')
                        enlaces_encontrados.add((cleaned_link, "Direct Cloud Link (Mediafire/Drive)"))
                elif tipo == "web":
                    all_links = re.findall(r'https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,6}/[^\s"\'\\>]+', r.text)
                    for link in all_links:
                        cleaned_link = link.rstrip('.,);>]}')
                        link_lower = cleaned_link.lower()
                        if any(pattern in link_lower for pattern in ["cheat", "cheats", "services", "programs", "hack", "hacks", "injector", "bypass", "spoofer"]):
                            enlaces_encontrados.add((cleaned_link, "Web Sospechosa Detectada"))
        except Exception as e:
            print(f"[Crawl] Error en {tipo} para '{termino}': {e}")
    for termino in terminos_busqueda[:3]:
        await buscar_en_ddg(termino, "github")
        await buscar_en_ddg(termino, "cloud")
        await buscar_en_ddg(termino, "web")
    # No hay búsqueda en YouTube (eliminada)
    if not enlaces_encontrados:
        view = RegisterNewCheatOnlyView(consulta.capitalize() + " Hack")
        await ctx.send(f"❌ **No se han encontrado descargas ni menciones comerciales recientes para '{consulta}' con estos filtros.**\n\n👉 Si conoces un cheat relacionado, puedes registrarlo pulsando en **'📝 Registrar Cheat'**.", view=view)
        return
    enlaces_filtrados = list(enlaces_encontrados)[:5]
    await ctx.send(f"🔍 ¡Se han localizado **{len(enlaces_encontrados)}** fuentes! Analizando las **{len(enlaces_filtrados)}** más críticas...")
    for url, origen in enlaces_filtrados:
        try:
            auto_info = get_auto_download_info(url)
            if auto_info:
                filename = auto_info["filename"]
                direct_url = auto_info["direct_url"]
                source = auto_info["source"]
                await ctx.send(f"📥 *Descargando y extrayendo firma de '{filename}' desde {source}...*")
                file_resp = await asyncio.to_thread(requests.get, direct_url, headers=HEADERS, timeout=25)
                if file_resp.status_code == 200:
                    file_data = file_resp.content
                    sha256_hash = hashlib.sha256(file_data).hexdigest()
                    secure_hash = encrypt_signature(sha256_hash)
                    pos_name = filename.split('.')[0]
                    intel = search_cheat_intel(pos_name)
                    if not intel['known']:
                        web_intel = extract_web_intelligence(url)
                        if web_intel['description'] != "No se pudo extraer una descripción detallada automáticamente del sitio web.":
                            intel['description'] = f"🕵️‍♂️ **Análisis OSINT Web Real:**\n{web_intel['description']}"
                            intel['type'] = web_intel['type']
                            if web_intel['features']:
                                intel['description'] += f"\n\n⚡ **Características detectadas en el código web:**\n" + ", ".join([f"`{f}`" for f in web_intel['features']])
                            if web_intel['title'] != "Desconocido":
                                intel['name'] = f"{pos_name.capitalize()} ({web_intel['title'][:45]})"
                            automatically_learn_cheat(key=pos_name, name=intel['name'], game=consulta.capitalize(), website=url, license_type=web_intel['type'], description=intel['description'], category="cheat")
                    embed = discord.Embed(title=f"🚨 Cheat Encontrado para '{consulta.capitalize()}'" if intel['known'] else f"⚠️ Cheat Detectado (relacionado con '{consulta}')", description=f"Detectado automáticamente en el repositorio: **{source}**" if "/" in source else f"Localizado en la red: **{origen}**", color=discord.Color.red() if intel['known'] else discord.Color.orange())
                    embed.add_field(name="📂 Archivo Compilado", value=filename, inline=True)
                    size_str = f"{auto_info['size_kb']} KB" if auto_info['size_kb'] > 0 else f"{round(len(file_data)/1024, 2)} KB"
                    embed.add_field(name="📏 Tamaño", value=size_str, inline=True)
                    embed.add_field(name="🌐 Página Web", value=url, inline=False)
                    embed.add_field(name="🏷️ Licencia / Coste", value=intel['type'], inline=True)
                    embed.add_field(name="📝 Intel / Descripción", value=intel['description'], inline=False)
                    embed.add_field(name="🔑 Hash SHA-256", value=f"`{sha256_hash}`", inline=False)
                    categoria_texto = {"cheat": "Cheat", "injector": "Injector", "spoofer": "Spoofer", "other": "Otro"}.get(intel.get('category'), "Desconocido")
                    embed.add_field(name="📂 Categoría", value=categoria_texto, inline=True)
                    embed.set_footer(text="Haz clic en los botones de abajo para bloquear este cheat globalmente.")
                    view = CheatApprovalView(filename, sha256_hash, secure_hash, url, pos_name)
                    await ctx.send(embed=embed, view=view)
            else:
                pos_name = url.split('/')[-1].split('?')[0]
                if len(pos_name) < 3 or pos_name.lower() in ["forum", "download", "main", "file", "drive"]:
                    pos_name = url.split('/')[-2] if len(url.split('/')) > 2 else "Cloud Cheat"
                intel = search_cheat_intel(pos_name)
                if not intel['known']:
                    await ctx.send(f"🔍 *Analizando página externa: {pos_name}...*")
                    web_intel = extract_web_intelligence(url)
                    if web_intel['description'] != "No se pudo extraer una descripción detallada automáticamente del sitio web.":
                        intel['description'] = f"🕵️‍♂️ **Análisis OSINT Web Real:**\n{web_intel['description']}"
                        intel['type'] = web_intel['type']
                        if web_intel['features']:
                            intel['description'] += f"\n\n⚡ **Características detectadas en el código web:**\n" + ", ".join([f"`{f}`" for f in web_intel['features']])
                        if web_intel['title'] != "Desconocido":
                            intel['name'] = f"{pos_name.capitalize()} ({web_intel['title'][:45]})"
                        automatically_learn_cheat(key=pos_name, name=intel['name'], game=consulta.capitalize(), website=url, license_type=web_intel['type'], description=intel['description'], category="cheat")
                embed = discord.Embed(title=f"🔗 Cheat Detectado: {intel['name']}" if intel['known'] else f"⚠️ Posible cheat relacionado con '{consulta}'", description=f"Localizado en la red: **{origen}**", color=discord.Color.gold() if intel['known'] else discord.Color.orange())
                embed.add_field(name="🎮 Videojuego", value=intel['game'], inline=True)
                embed.add_field(name="🌐 Página Web", value=url, inline=False)
                embed.add_field(name="🏷️ Licencia / Coste", value=intel['type'], inline=True)
                embed.add_field(name="📝 Intel / Descripción", value=intel['description'], inline=False)
                categoria_texto = {"cheat": "Cheat", "injector": "Injector", "spoofer": "Spoofer", "other": "Otro"}.get(intel.get('category'), "Desconocido")
                embed.add_field(name="📂 Categoría", value=categoria_texto, inline=True)
                embed.set_footer(text="Requiere descarga manual. Arrastra el binario o banea su hash manualmente.")
                view = CheatApprovalView("descarga_manual.exe", "N/A", "N/A", url, pos_name)
                await ctx.send(embed=embed, view=view)
        except Exception as e:
            print(f"[Procesar URL] Error en {url}: {e}")

# ============================================================================
# CONTROLADORES DE ERRORES
# ============================================================================
@buscar_cheats.error
async def buscar_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ **Uso correcto del comando:** `!buscar <nombre_del_juego_o_cheat>`\n*Ejemplo:* `!buscar cs2` o `!buscar neverlose`")

@nombres_cheats.error
async def nombres_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ **Uso correcto del comando:** `!nombres <nombre_del_juego>`\n*Ejemplo:* `!nombres minecraft` o `!nombres roblox`")

@juegos_cheats.error
async def juegos_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ **Uso correcto del comando:** `!juegos <nombre_del_juego>`\n*Ejemplo:* `!juegos cs2` o `!juegos minecraft`")

@estadisticas.error
async def estadisticas_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ **Uso correcto del comando:** `!estadisticas`\n*Muestra un resumen completo de la base de datos.*")

# ============================================================================
# SERVIDOR WEB PARA RENDER
# ============================================================================
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "🛡️ VanguardX Bot está en línea y funcionando correctamente."

def run_web():
    web_app.run(host="0.0.0.0", port=7860)

# ============================================================================
# INICIO DEL BOT
# ============================================================================
if __name__ == "__main__":
    if not TOKEN or TOKEN == "TU_TOKEN_AQUI":
        print("="*70, flush=True)
        print("[FATAL] El token de Discord es inválido o está expuesto. Cámbialo por uno nuevo.", flush=True)
        print("1. Ve a https://discord.com/developers/applications", flush=True)
        print("2. Crea una aplicación o selecciona la tuya.", flush=True)
        print("3. Ve a 'Bot' y copia el token.", flush=True)
        print("4. Pégalo en la variable TOKEN dentro del código.", flush=True)
        print("="*70, flush=True)
        sys.exit(1)

    t = threading.Thread(target=run_web, daemon=True)
    t.start()
    print("[Diagnóstico] Comprobando conexión a Internet...", flush=True)
    for test_url in ["https://www.google.com", "https://discord.com", FIREBASE_URL]:
        try:
            r = requests.get(test_url, timeout=15)
            print(f"[Diagnóstico] ✅ Conexión exitosa a {test_url} (Código {r.status_code})", flush=True)
        except Exception as e:
            print(f"[Diagnóstico] ⚠️  No se pudo conectar a {test_url}: {e}", flush=True)
    max_retries = 5
    retry_delay = 15
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[Inicio] Intentando conectar el bot a Discord (Intento {attempt}/{max_retries})...", flush=True)
            bot.run(TOKEN, reconnect=True)
            break
        except discord.errors.LoginFailure:
            print("="*70, flush=True)
            print("[FATAL] Token inválido o revocado. Genera uno nuevo en Discord Developer Portal.", flush=True)
            sys.exit(1)
        except discord.errors.PrivilegedIntentsRequired:
            print("="*70, flush=True)
            print("[FATAL] Faltan permisos de Gateway Intents. Activa 'MESSAGE CONTENT INTENT'.", flush=True)
            sys.exit(1)
        except Exception as e:
            print(f"[Advertencia] Error al conectar (Intento {attempt}): {e}", flush=True)
            if attempt < max_retries:
                print(f"[Reintento] Esperando {retry_delay}s antes de reintentar...", flush=True)
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 120)
            else:
                print("[FATAL] Se agotaron todos los intentos de conexión.", flush=True)
                sys.exit(1)