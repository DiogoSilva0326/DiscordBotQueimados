import discord
from discord.ext import commands

class Mensagens(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # ==========================================================
        # O TEU ARQUIVO DE RESPOSTAS AUTOMÁTICAS (Estilo Carl-bot)
        # ==========================================================
        # Mantém as palavras do lado esquerdo sempre em MINÚSCULAS!
        
        self.respostas = {
            "crianças": "Defse? Olá?",
            "relva": "Deixa meter relba pedro",
            "eri": "Mesa",
            "chato": "Boohoo estou tão cansado!",
            "wow": "LEGION!?",
            "do": "eu perdi o do da minha violaa",
            "ajuda": "https://media2.giphy.com/media/eWBqHHp63bPGeHEB6a/giphy.gif",
            "mesa": "https://klipy.com/gifs/table-fabio",
            "nigger": "Não me chames disso pf!"
        }

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignora bots
        if message.author.bot:
            return

        # Limpa a mensagem (tira espaços extra no início/fim e mete em minúsculas)
        texto_mensagem = message.content.lower().strip()

        # Procura se a mensagem INTEIRA é exatamente igual a algum dos gatilhos
        for gatilho, resposta in self.respostas.items():
            
            # A VERIFICAÇÃO EXATA!
            if texto_mensagem == gatilho:
                await message.channel.send(resposta)
                break 

async def setup(bot):
    await bot.add_cog(Mensagens(bot))