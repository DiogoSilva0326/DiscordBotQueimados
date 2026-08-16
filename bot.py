import discord
from discord.ext import commands
from PIL import Image
import io
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ====================================================================
# OTIMIZAÇÃO 1: Preparar a marca de água UMA ÚNICA VEZ quando o bot liga
# ====================================================================
MARCA_AGUA_GLOBAL = Image.open("logo_queimados.png").convert("RGBA")
nivel_opacidade = 150
dados_alpha = MARCA_AGUA_GLOBAL.split()[3]
dados_alpha = dados_alpha.point(lambda p: p * (nivel_opacidade / 255.0))
MARCA_AGUA_GLOBAL.putalpha(dados_alpha)
# ====================================================================

@bot.event
async def on_ready():
    print(f'✅ O bot {bot.user} está online e otimizado!')

@bot.command()
async def marca(ctx):
    if not ctx.message.attachments:
        await ctx.send("Por favor, envia uma imagem juntamente com o comando `!marca`.")
        return

    anexo = ctx.message.attachments[0]
    
    if not anexo.content_type.startswith('image/'):
        await ctx.send("O ficheiro precisa de ser uma imagem!")
        return

    # ====================================================================
    # OTIMIZAÇÃO 2: Bloquear ficheiros pesados (Limite de 3MB)
    # (3 * 1024 bytes * 1024 bytes = 5 Megabytes)
    # ====================================================================
    TAMANHO_MAXIMO = 3 * 1024 * 1024
    if anexo.size > TAMANHO_MAXIMO:
        await ctx.send("❌ A imagem é demasiado pesada! Por favor, envia uma imagem com menos de 3MB para não sobrecarregar o bot.")
        return

    mensagem_processo = await ctx.send("A aplicar a marca de água...")

    try:
        image_bytes = await anexo.read()
        imagem_base = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

        # Em vez de ler do disco, fazemos apenas uma cópia rápida da variável global
        marca_agua = MARCA_AGUA_GLOBAL.copy()

        tamanho_proporcional = (imagem_base.width // 4, imagem_base.height // 4)
        marca_agua.thumbnail(tamanho_proporcional)

        x = imagem_base.width - marca_agua.width - 10
        y = imagem_base.height - marca_agua.height - 10

        imagem_base.paste(marca_agua, (x, y), marca_agua)

        output = io.BytesIO()
        imagem_base.save(output, format="PNG")
        output.seek(0)

        ficheiro_final = discord.File(output, filename="com_marca.png")
        await ctx.send(file=ficheiro_final)
        await mensagem_processo.delete()

        # ====================================================================
        # OTIMIZAÇÃO 3: Limpar imediatamente a memória RAM utilizada
        # ====================================================================
        imagem_base.close()
        marca_agua.close()
        output.close()

    except Exception as e:
        await ctx.send(f"Ocorreu um erro ao processar a imagem: {e}")

token_seguro = os.getenv('DISCORD_TOKEN')
bot.run(token_seguro)