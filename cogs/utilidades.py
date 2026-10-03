import discord
from discord.ext import commands
from discord import app_commands

class Utilidades(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="avatar", description="Mostra o avatar de um utilizador ou o teu.")
    @app_commands.describe(membro="O utilizador cujo avatar queres ver")
    async def avatar(self, interaction: discord.Interaction, membro: discord.Member = None):
        membro = membro or interaction.user
        avatar_url = membro.avatar.url if membro.avatar else membro.default_avatar.url
        await interaction.response.send_message(f"🖼️ **Avatar de {membro.display_name}:**\n{avatar_url}")

    @app_commands.command(name="banner", description="Mostra o banner de perfil de um utilizador.")
    @app_commands.describe(membro="O utilizador cujo banner queres ver")
    async def banner(self, interaction: discord.Interaction, membro: discord.Member = None):
        membro = membro or interaction.user
        utilizador = await self.bot.fetch_user(membro.id)
        
        if utilizador.banner:
            await interaction.response.send_message(f"🌌 **Banner de {utilizador.display_name}:**\n{utilizador.banner.url}")
        else:
            await interaction.response.send_message(f"O utilizador **{utilizador.display_name}** não tem um banner de perfil.")

    @app_commands.command(name="say", description="Faz o bot falar através de um webhook personificado.")
    @app_commands.describe(membro="O membro que queres personificar", mensagem="A mensagem a enviar")
    async def say(self, interaction: discord.Interaction, membro: discord.Member, mensagem: str):
        await interaction.response.defer(ephemeral=True)

        webhooks = await interaction.channel.webhooks()
        webhook = next((wh for wh in webhooks if wh.user == self.bot.user), None)
        
        if not webhook:
            webhook = await interaction.channel.create_webhook(name="BotQueimadosWebhook")
            
        avatar_url = membro.avatar.url if membro.avatar else membro.default_avatar.url
        
        await webhook.send(
            content=mensagem,
            username=membro.display_name,
            avatar_url=avatar_url
        )
        await interaction.followup.send("✅ Mensagem enviada com sucesso!", ephemeral=True)

    @app_commands.command(name="help", description="Apresenta o manual de comandos do Alfredo.")
    async def comando_ajuda(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 Manual do Alfredo",
            description="Aqui tens a lista de tudo o que eu consigo fazer.\n*Atenção: Apenas membros com o cargo **Imagina** é que merecem o meu respeito para usar estes comandos!*",
            color=discord.Color.dark_theme() 
        )

        embed.add_field(
            name="🖼️ Edição de Imagens e GIFs", 
            value=(
                "`/marca` - Cola a marca de água no canto da imagem/GIF.\n"
                "`/caption [texto]` - Cria a caixa branca de meme com o texto.\n"
                "`/uncaption` - Corta a legenda de cima de um meme.\n"
                "`/gif` - Converte uma imagem normal para formato .gif.\n"
                "`/haah` ou `/espelho1` - Espelha a esquerda na direita.\n"
                "`/hooh` ou `/espelho2` - Espelha o fundo no topo.\n"
                "`/deepfry` - Frita a imagem com saturação e contraste no máximo."
            ), 
            inline=False
        )

        embed.add_field(
            name="🎵 Música (SoundCloud)", 
            value=(
                "`/play [nome/link]` - Toca ou adiciona uma música à fila.\n"
                "`/fila` - Mostra as próximas músicas a tocar.\n"
                "`/skip` / `/stop` - Controlos (Também podes usar os botões interativos nas mensagens!)"
            ), 
            inline=False
        )

        embed.add_field(
            name="🔫 Servidor sério.", 
            value=(
                "`/roleta` - Inicia a Roleta Russa. Se tiveres permissão para banir, o bot vai escolher um membro do servidor à sorte e bani-lo! Não uses isto com cuidado."
            ), 
            inline=False
        )

        embed.add_field(
            name="🛠️ Utilidades", 
            value=(
                "`/avatar [@utilizador]` - Rouba a foto de perfil de alguém.\n"
                "`/banner [@utilizador]` - Rouba o banner de perfil de alguém.\n"
                "`/say [@utilizador] [texto]` - Faz outra pessoa falar a verdade."
            ), 
            inline=False
        )

        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else self.bot.user.default_avatar.url)
        embed.set_footer(text="Desenvolvido para os goats da Unidade de Queimados 🔥")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utilidades(bot))