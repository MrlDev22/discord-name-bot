"""
Discord Name Availability Bot
Verifica nomes de 1 a 5 dígitos e avisa no canal quando um fica disponível.
"""

import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import string
import json
import os
from datetime import datetime
from itertools import product

# ─────────────────────────────────────────
#  CONFIGURAÇÕES — edite aqui
# ─────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "SEU_TOKEN_AQUI")          # Token do bot
CHANNEL_ID     = 1526306182653022218        # ID do canal onde mandar alertas
CHECK_INTERVAL = 10                        # Intervalo em minutos entre cada verificação
MIN_LENGTH     = 1                         # Tamanho mínimo de nome a verificar
MAX_LENGTH     = 5                         # Tamanho máximo de nome a verificar
CHARS          = string.digits             # Caracteres: só números (troque por string.ascii_lowercase para letras)
STATE_FILE     = "available_names.json"   # Arquivo para salvar estado
# ─────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Nomes já conhecidos como disponíveis (para não repetir alertas)
known_available: set = set()


def load_state():
    """Carrega nomes já avisados de disco."""
    global known_available
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            known_available = set(json.load(f))
    print(f"[Estado] {len(known_available)} nomes já conhecidos carregados.")


def save_state():
    """Salva nomes já avisados em disco."""
    with open(STATE_FILE, "w") as f:
        json.dump(list(known_available), f)


def generate_names(min_len: int, max_len: int, chars: str):
    """Gera todos os nomes possíveis com os comprimentos e chars definidos."""
    names = []
    for length in range(min_len, max_len + 1):
        for combo in product(chars, repeat=length):
            names.append("".join(combo))
    return names


async def is_username_available(session: aiohttp.ClientSession, username: str) -> bool:
    """
    Verifica se um username está disponível na API pública do Discord.
    Retorna True se disponível, False caso contrário.
    """
    url = f"https://discord.com/api/v10/unique-username/username-attempt-unauthed"
    payload = {"username": username}
    try:
        async with session.post(url, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("taken") is False
            elif resp.status == 429:
                # Rate limit — espera e tenta novamente
                retry_after = float(resp.headers.get("Retry-After", 5))
                await asyncio.sleep(retry_after)
                return await is_username_available(session, username)
            else:
                return False
    except Exception as e:
        print(f"[Erro] Verificando '{username}': {e}")
        return False


@tasks.loop(minutes=CHECK_INTERVAL)
async def check_names():
    """Task periódica que verifica todos os nomes e avisa no canal."""
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"[Erro] Canal {CHANNEL_ID} não encontrado!")
        return

    all_names = generate_names(MIN_LENGTH, MAX_LENGTH, CHARS)
    newly_available = []

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Verificando {len(all_names)} nomes...")

    async with aiohttp.ClientSession() as session:
        for name in all_names:
            available = await is_username_available(session, name)

            if available and name not in known_available:
                newly_available.append(name)
                known_available.add(name)
                print(f"  ✅ DISPONÍVEL: {name}")
            elif not available and name in known_available:
                # Nome foi tomado após ter sido avisado
                known_available.discard(name)
                print(f"  ❌ Tomado: {name}")

            # Delay gentil para não bater no rate limit
            await asyncio.sleep(0.3)

    save_state()

    if newly_available:
        # Agrupa em chunks para não extrapolar o limite de 2000 chars do Discord
        chunks = chunk_list(newly_available, 30)
        for i, chunk in enumerate(chunks):
            names_fmt = " • ".join(f"`{n}`" for n in chunk)
            embed = discord.Embed(
                title=f"🎉 Nomes disponíveis! ({len(newly_available)} encontrados)",
                description=names_fmt,
                color=0x5865F2,
                timestamp=datetime.utcnow(),
            )
            embed.set_footer(text=f"Parte {i+1}/{len(chunks)} • Bot de nomes")
            await channel.send(embed=embed)
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Nenhum nome novo disponível.")


def chunk_list(lst, size):
    """Divide uma lista em pedaços de tamanho `size`."""
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


# ─── Comandos ───────────────────────────

@bot.command(name="check")
async def check_now(ctx):
    """!check — força uma verificação imediata."""
    await ctx.send("🔍 Iniciando verificação manual...")
    await check_names()


@bot.command(name="status")
async def status(ctx):
    """!status — mostra quantos nomes disponíveis foram detectados até agora."""
    all_names = generate_names(MIN_LENGTH, MAX_LENGTH, CHARS)
    embed = discord.Embed(title="📊 Status do bot", color=0x57F287)
    embed.add_field(name="Total de nomes monitorados", value=str(len(all_names)), inline=True)
    embed.add_field(name="Disponíveis detectados", value=str(len(known_available)), inline=True)
    embed.add_field(name="Intervalo de verificação", value=f"{CHECK_INTERVAL} minutos", inline=True)
    embed.add_field(name="Comprimentos monitorados", value=f"{MIN_LENGTH} a {MAX_LENGTH} dígitos", inline=True)
    await ctx.send(embed=embed)


@bot.command(name="lista")
async def lista(ctx):
    """!lista — lista os nomes disponíveis conhecidos."""
    if not known_available:
        await ctx.send("Nenhum nome disponível detectado ainda.")
        return
    names = sorted(known_available, key=len)
    chunks = list(chunk_list(names, 30))
    for i, chunk in enumerate(chunks):
        desc = " • ".join(f"`{n}`" for n in chunk)
        embed = discord.Embed(
            title=f"📋 Nomes disponíveis (parte {i+1}/{len(chunks)})",
            description=desc,
            color=0x5865F2,
        )
        await ctx.send(embed=embed)


# ─── Eventos ────────────────────────────

@bot.event
async def on_ready():
    load_state()
    print(f"✅ Bot conectado como {bot.user}")
    print(f"📡 Monitorando canal {CHANNEL_ID}")
    print(f"⏱️  Verificando a cada {CHECK_INTERVAL} minutos")
    check_names.start()


# ─── Entry point ────────────────────────
if __name__ == "__main__":
    bot.run(BOT_TOKEN)
