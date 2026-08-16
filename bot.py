import discord
from discord.ext import commands
from PIL import Image
import io
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ====================================================================
# OTIMIZAÇÃO 1: Preparar a marca de água UMA ÚNICA VEZ quando o bot liga
# ====================================================================
MARCA_AGUA_GLOBAL = Image.open("marca_de_agua.png").convert("RGBA")
nivel_opacidade = 150
dados_alpha = MARCA_AGUA_GLOBAL.split()[3]
dados_alpha = dados_alpha.point(lambda p: p * (nivel_opacidade / 255.0))
MARCA_AGUA_GLOBAL.putalpha(dados_alpha)
# ====================================================================

@bot.event
async def on_ready():
    print(f'✅ O bot {bot.user} está online e otimizado com novos comandos!')

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


# ====================================================================
# NOVOS COMANDOS (AVATAR, BANNER, SAY/IMPERSONATOR)
# ====================================================================

@bot.command()
async def avatar(ctx, membro: discord.Member = None):
    # Se não mencionar ninguém, o bot mostra o avatar de quem enviou o comando
    membro = membro or ctx.author
    
    # Verifica se tem avatar personalizado, senão usa o padrão do Discord
    avatar_url = membro.avatar.url if membro.avatar else membro.default_avatar.url
    await ctx.send(f"🖼️ **Avatar de {membro.display_name}:**\n{avatar_url}")

@bot.command()
async def banner(ctx, membro: discord.Member = None):
    membro = membro or ctx.author
    
    # Para o banner, o discord.py obriga-nos a "buscar" (fetch) o perfil completo do utilizador
    utilizador = await bot.fetch_user(membro.id)
    
    if utilizador.banner:
        await ctx.send(f"🌌 **Banner de {utilizador.display_name}:**\n{utilizador.banner.url}")
    else:
        await ctx.send(f"O utilizador **{utilizador.display_name}** não tem um banner de perfil personalizado.")

@bot.command()
async def say(ctx, membro: discord.Member, *, mensagem: str):
    # Apaga a mensagem original de quem enviou o comando para manter a ilusão
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass # Se o bot não tiver permissão para apagar mensagens, ignora

    # Procura se o bot já tem um Webhook neste canal
    webhooks = await ctx.channel.webhooks()
    webhook = next((wh for wh in webhooks if wh.user == bot.user), None)
    
    # Se não tiver, cria um Webhook novo
    if not webhook:
        webhook = await ctx.channel.create_webhook(name="BotQueimadosWebhook")
        
    # Obtém o avatar do membro que queremos imitar
    avatar_url = membro.avatar.url if membro.avatar else membro.default_avatar.url
    
    # Usa o webhook para enviar a mensagem disfarçada de outro utilizador
    await webhook.send(
        content=mensagem,
        username=membro.display_name,
        avatar_url=avatar_url
    )

@say.error
async def say_error(ctx, error):
    # Avisa caso a pessoa se esqueça de mencionar o alvo ou a mensagem
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Uso incorreto! O formato é: `!say @utilizador a mensagem que queres escrever`")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Não consegui encontrar esse utilizador. Tens de o mencionar com um @!")

# ====================================================================
# COMANDO DE AJUDA (!help)
# ====================================================================
bot.remove_command('help')
@bot.command()
async def ajuda(ctx):
    # Criar o formato visual da mensagem (Embed)
    embed = discord.Embed(
        title="🤖 Comandos do Alfredo",
        description="Aqui tens a lista de tudo o que eu consigo fazer:",
        color=discord.Color.blue() 
    )

    # Adicionar os blocos de texto para cada comando
    embed.add_field(
        name="🖼️ `!marca`", 
        value="Envia uma imagem no chat e escreve este comando na legenda.", 
        inline=False
    )
    
    embed.add_field(
        name="👤 `!avatar [@utilizador]`", 
        value="Mostra a foto de perfil em tamanho grande da pessoa que mencionares. Se usares o comando sozinho, mostro a tua foto.", 
        inline=False
    )
    
    embed.add_field(
        name="🌌 `!banner [@utilizador]`", 
        value="Mostra o banner de perfil da pessoa mencionada.", 
        inline=False
    )
    
    embed.add_field(
        name="🎭 `!say [@utilizador] [mensagem]`", 
        value="Prega uma partida! Eu apago a tua mensagem e envio o teu texto disfarçado (com o nome e foto) da pessoa que mencionaste.\n*Exemplo: `!say @Defse Imagina, adoro crianças mas`*", 
        inline=False
    )

    # Adicionar um rodapé
    embed.set_footer(text="Desenvolvido para a Unidade de Queimados 🔥")

    # Enviar a mensagem bonita para o chat
    await ctx.send(embed=embed)


# Executa o bot
token_seguro = os.getenv('DISCORD_TOKEN')
bot.run(token_seguro)