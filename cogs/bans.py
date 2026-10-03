import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio

class Diversao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roleta", description="Inicia o jogo da Roleta Russa com ban aleatório.")
    async def roleta(self, interaction: discord.Interaction):
        # 1. Permissão do Autor
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("🚫 **Alto lá!** Tens o cargo Imagina, mas não és Moderador. Não podes brincar com armas de fogo.", ephemeral=True)
            return

        # 2. Permissão do Bot
        if not interaction.guild.me.guild_permissions.ban_members:
            await interaction.response.send_message("❌ Eu não tenho permissão para banir membros no servidor! Dá-me a permissão de 'Banir Membros' nas configurações.", ephemeral=True)
            return

        # 3. Filtrar Alvos Válidos
        alvos_validos = [
            membro for membro in interaction.guild.members 
            if not membro.bot
            and membro != interaction.guild.owner
            and membro.top_role < interaction.guild.me.top_role
        ]

        if not alvos_validos:
            await interaction.response.send_message("❌ A sala está vazia! Não há ninguém válido que eu possa banir (todas as pessoas têm cargos superiores ao meu).", ephemeral=True)
            return

        # 4. Escolher a Vítima
        vitima = random.choice(alvos_validos)

        # 5. Suspense Interativo
        await interaction.response.send_message("🔫 **A Roleta Russa começou!** A colocar uma bala no tambor...")
        await asyncio.sleep(2)
        
        await interaction.edit_original_response(content="🔄 **A girar o tambor...** *Trr trr trr trr...*")
        await asyncio.sleep(2.5)
        
        await interaction.edit_original_response(content="😰 **A arma parou.** O Alfredo aponta a arma para a multidão com os olhos vendados...")
        await asyncio.sleep(2.5)
        
        await interaction.edit_original_response(content="☝️ **O dedo aperta lentamente o gatilho...**")
        await asyncio.sleep(3)

        # 6. O Disparo
        try:
            await vitima.ban(reason=f"Perdeu na Roleta Russa do Alfredo (Iniciada por {interaction.user.name})")
            await interaction.edit_original_response(content=f"💥 **BANG!** 🩸\n\nO(a) {vitima.mention} teve azar, levou um tiro e caiu inanimado (foi **banido** do servidor)! 💀")
        except discord.Forbidden:
            await interaction.edit_original_response(content=f"💥 **BANG!** ... *click*\n\nA arma encravou! Eu tentei dar um tiro no(a) {vitima.mention}, mas os deuses (o cargo dessa pessoa) impediram-me. Que sorte! 🍀")
        except Exception as e:
            await interaction.edit_original_response(content=f"❌ A arma explodiu na minha mão! Erro inesperado: {e}")

async def setup(bot):
    await bot.add_cog(Diversao(bot))