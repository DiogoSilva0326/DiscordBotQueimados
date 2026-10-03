import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ====================================================================
# SISTEMA DE SEGURANÇA
# ====================================================================
NOME_DA_ROLE = "Imagina" 

@bot.check
async def verificar_permissao(ctx):
    if ctx.guild is None:
        return False
        
    tem_permissao = discord.utils.get(ctx.author.roles, name=NOME_DA_ROLE)
    
    if tem_permissao is not None:
        return True 
    else:
        await ctx.send(f"❌ {ctx.author.mention}, não tens permissão! Precisas do cargo **{NOME_DA_ROLE}** para me conseguires usar.")
        return False 

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure) or isinstance(error, commands.CommandNotFound):
        pass
    else:
        print(f"Ocorreu um erro: {error}")

@bot.event
async def on_ready():
    # Esta é a linha mágica que avisa o Discord dos comandos "/"
    await bot.tree.sync() 
    print(f'✅ Logado como {bot.user}')

# ====================================================================
# INICIALIZAÇÃO DOS COGS E DO BOT
# ====================================================================
async def main():
    async with bot:
        # Lê a pasta 'cogs' e carrega todos os ficheiros .py que lá estiverem
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"⚙️ Módulo {filename} carregado com sucesso!")
        
        await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    asyncio.run(main())