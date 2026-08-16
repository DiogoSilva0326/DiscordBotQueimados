import discord
from discord.ext import commands
from PIL import Image
import io

# Configurar as permissões (Intents)
intents = discord.Intents.default()
intents.message_content = True

# Criar o bot com o prefixo '!'
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ O bot {bot.user} está online e pronto!')

@bot.command()
async def marca(ctx):
    if not ctx.message.attachments:
        await ctx.send("Por favor, envia uma imagem juntamente com o comando `!marca`.")
        return

    anexo = ctx.message.attachments[0]
    
    if not anexo.content_type.startswith('image/'):
        await ctx.send("O ficheiro precisa de ser uma imagem!")
        return

    mensagem_processo = await ctx.send("A aplicar a marca de água...")

    try:
        image_bytes = await anexo.read()
        imagem_base = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

        # 1. SUBSTITUI AQUI O NOME DO TEU FICHEIRO (que deve ser um .png sem fundo)
        marca_agua = Image.open("marca_de_agua.png").convert("RGBA")

        # 2. DEFINIR OPACIDADE (Transparência)
        # Nível de 0 a 255. (255 = totalmente sólido | 128 = ~50% transparente)
        nivel_opacidade = 150 
        
        # Este bloco altera a transparência do logótipo
        dados_alpha = marca_agua.split()[3] # Extrai o canal de transparência
        dados_alpha = dados_alpha.point(lambda p: p * (nivel_opacidade / 255.0))
        marca_agua.putalpha(dados_alpha)

        # Redimensionar a marca de água para 25% do tamanho da imagem base
        tamanho_proporcional = (imagem_base.width // 4, imagem_base.height // 4)
        marca_agua.thumbnail(tamanho_proporcional)

        # 3. COLOCAR NO CANTO INFERIOR DIREITO
        x = imagem_base.width - marca_agua.width - 10
        y = imagem_base.height - marca_agua.height - 10

        # Colar a marca de água 
        imagem_base.paste(marca_agua, (x, y), marca_agua)

        # Guardar e enviar
        output = io.BytesIO()
        imagem_base.save(output, format="PNG")
        output.seek(0)

        ficheiro_final = discord.File(output, filename="com_marca.png")
        await ctx.send(file=ficheiro_final)
        await mensagem_processo.delete()

    except Exception as e:
        await ctx.send(f"Ocorreu um erro ao processar a imagem: {e}")

# Executar o bot
bot.run('MTUzODI3NTQwODYyMDAzMjE3MQ.GyBSzU.da1eiEVtKHtB1InTGSHb9jhKWmIwQbeHFonfbo')