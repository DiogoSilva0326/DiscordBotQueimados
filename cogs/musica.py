import discord
from discord.ext import commands, tasks
from discord import app_commands
import wavelink
import asyncio
import os
import random

# ====================================================================
# CLASSE DOS BOTÕES INTERATIVOS
# ====================================================================
class BotoesMusica(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(emoji="⏯️", label="Play/Pause", style=discord.ButtonStyle.primary)
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("Não estou em nenhum canal de voz.", ephemeral=True)
            return
            
        if isinstance(vc, wavelink.Player):
            await vc.pause(not vc.paused)
            estado = "pausada" if vc.paused else "retomada"
        else:
            if vc.is_playing():
                vc.pause()
                estado = "pausada"
            else:
                vc.resume()
                estado = "retomada"
                
        await interaction.response.send_message(f"⏯️ {estado.capitalize()}!", ephemeral=True)

    @discord.ui.button(emoji="⏭️", label="Skip", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("Não estou em nenhum canal.", ephemeral=True)
            return
            
        if isinstance(vc, wavelink.Player):
            if vc.playing:
                await vc.skip(force=True)
                await interaction.response.send_message("⏭️ Passada à frente!", ephemeral=True)
        else:
            if vc.is_playing():
                vc.stop()
                await interaction.response.send_message("⏭️ Áudio cancelado!", ephemeral=True)

    @discord.ui.button(emoji="⏹️", label="Stop", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc:
            if isinstance(vc, wavelink.Player):
                vc.queue.clear()
            await vc.disconnect()
            await interaction.response.send_message("👋 Saí da chamada!", ephemeral=True)


class Musica(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.conectar_lavalink())
        self.audios_aleatorios.start()

    def cog_unload(self):
        self.audios_aleatorios.cancel()

    async def conectar_lavalink(self):
        await self.bot.wait_until_ready()
        
        nodos = [
            wavelink.Node(
                uri="https://lavalink.serenetia.com:443", 
                password="https://dsc.gg/ajidevserver"
            )
        ]
        
        await wavelink.Pool.connect(nodes=nodos, client=self.bot, cache_capacity=100)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        print(f"✅ Lavalink conectado com sucesso! Nodo: {payload.node.identifier}")

    # ====================================================================
    # TAREFA: ÁUDIOS ALEATÓRIOS A CADA 15 MINUTOS
    # ====================================================================
    @tasks.loop(minutes=15)
    async def audios_aleatorios(self):
        for guild in self.bot.guilds:
            vc = guild.voice_client
            if not vc:
                continue

            is_playing = (vc.playing or vc.paused) if isinstance(vc, wavelink.Player) else (vc.is_playing() or vc.is_paused())

            if not is_playing:
                pasta_audios = os.path.join(os.getcwd(), 'audios')
                if os.path.exists(pasta_audios):
                    ficheiros = [f for f in os.listdir(pasta_audios) if f.endswith(('.mp3', '.wav', '.ogg'))]
                    
                    if ficheiros:
                        audio = random.choice(ficheiros)
                        caminho = os.path.join(pasta_audios, audio)
                        
                        try:
                            if isinstance(vc, wavelink.Player) and hasattr(vc, 'canal_texto'):
                                ficheiro_discord = discord.File(caminho)
                                msg = await vc.canal_texto.send(f"🎲 *Áudio Aleatório:* `{audio}`", file=ficheiro_discord)
                                url = msg.attachments[0].url
                                
                                resultados = await wavelink.Playable.search(url)
                                if resultados:
                                    track = resultados.tracks[0] if isinstance(resultados, wavelink.Playlist) else resultados[0]
                                    await vc.play(track)

                            elif not isinstance(vc, wavelink.Player):
                                fonte = discord.FFmpegPCMAudio(caminho)
                                vc.play(fonte)
                        except Exception as e:
                            if "Not connected to voice" in str(e):
                                pass
                            else:
                                print(f"❌ Erro no áudio aleatório: {e}")

    @audios_aleatorios.before_loop
    async def antes_dos_audios(self):
        await self.bot.wait_until_ready()

    # ====================================================================
    # EVENTOS DA MÚSICA
    # ====================================================================
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        player: wavelink.Player = payload.player
        track: wavelink.Playable = payload.track
        
        if not track:
            return

        if "cdn.discordapp.com" in track.uri or "discordapp.net" in track.uri:
            return

        embed = discord.Embed(
            title="🎵 A Tocar Agora",
            description=f"**[{track.title}]({track.uri})**",
            color=discord.Color.brand_red()
        )
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)
            
        duracao_formatada = f"{track.length // 60000}:{(track.length // 1000) % 60:02d}"
        embed.add_field(name="Duração", value=duracao_formatada, inline=True)
        embed.add_field(name="Autor", value=track.author, inline=True)
        
        if hasattr(player, 'canal_texto'):
            await player.canal_texto.send(embed=embed, view=BotoesMusica())

    # ====================================================================
    # COMANDOS (SLASH)
    # ====================================================================
    @app_commands.command(name="join", description="Faz o bot entrar no canal de voz para áudios.")
    async def join(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ Tens de estar num canal de voz primeiro!", ephemeral=True)
            return
            
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.defer()
            vc = await interaction.user.voice.channel.connect()
            await interaction.followup.send("✅ Entrei no canal! *(Modo Convívio / Áudios Aleatórios)*")

            pasta_audios = os.path.join(os.getcwd(), 'audios')
            if os.path.exists(pasta_audios):
                ficheiros = [f for f in os.listdir(pasta_audios) if f.endswith(('.mp3', '.wav', '.ogg'))]
                if ficheiros:
                    audio_escolhido = random.choice(ficheiros)
                    caminho_completo = os.path.join(pasta_audios, audio_escolhido)
                    try:
                        fonte = discord.FFmpegPCMAudio(caminho_completo)
                        vc.play(fonte)
                    except Exception as e:
                        print(f"❌ Erro ao tocar áudio de entrada: {e}")
                        
        elif isinstance(vc, wavelink.Player):
            await interaction.response.send_message("Já estou no canal em **Modo Música (Lavalink)**! 🎵")
        else:
            await interaction.response.send_message("Já estou no canal!")

    @app_commands.command(name="play", description="Toca uma música do YouTube, Spotify ou SoundCloud.")
    @app_commands.describe(pesquisa="Nome da música ou link direto")
    async def play(self, interaction: discord.Interaction, pesquisa: str):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ Tens de estar num canal de voz!", ephemeral=True)
            return
            
        await interaction.response.defer()
        vc = interaction.guild.voice_client

        if vc and not isinstance(vc, wavelink.Player):
            await vc.disconnect()
            await asyncio.sleep(1)
            vc = None

        if not vc:
            player: wavelink.Player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
            player.canal_texto = interaction.channel 
            player.autoplay = wavelink.AutoPlayMode.partial 
        else:
            player = vc
            player.canal_texto = interaction.channel
        
        texto_pesquisa = pesquisa if len(pesquisa) < 50 else pesquisa[:50] + "..."
        mensagem = await interaction.followup.send(f"🔍 A procurar: `{texto_pesquisa}`...", wait=True)

        try:
            resultados = await wavelink.Playable.search(pesquisa)
            
            if not resultados and not pesquisa.startswith("http"):
                await mensagem.edit(content=f"🔍 Não encontrei no YT. A tentar no Spotify: `{texto_pesquisa}`...")
                resultados = await wavelink.Playable.search(f"spsearch:{pesquisa}")
                
            if not resultados and not pesquisa.startswith("http"):
                await mensagem.edit(content=f"🔍 Não encontrei no Spotify. A tentar no SoundCloud: `{texto_pesquisa}`...")
                resultados = await wavelink.Playable.search(f"scsearch:{pesquisa}")

            if not resultados:
                await mensagem.edit(content="❌ Não encontrei essa música no YouTube, nem no Spotify, nem no SoundCloud.")
                return

            if isinstance(resultados, wavelink.Playlist):
                for track in resultados.tracks:
                    await player.queue.put_wait(track)
                
                await mensagem.edit(content=f"🎶 **Playlist Adicionada!** Foram adicionadas **{len(resultados.tracks)}** músicas à fila.")
                if not player.playing:
                    await player.play(player.queue.get())
            else:
                musica = resultados[0]
                await player.queue.put_wait(musica)

                if player.playing:
                    embed = discord.Embed(
                        title="📝 Adicionada à Fila",
                        description=f"**[{musica.title}]({musica.uri})**",
                        color=discord.Color.green()
                    )
                    if musica.artwork:
                        embed.set_thumbnail(url=musica.artwork)
                    await mensagem.edit(content=None, embed=embed)
                else:
                    await mensagem.delete()
                    await player.play(player.queue.get())
                
        except Exception as e:
            await mensagem.edit(content=f"❌ Erro ao tentar processar a música. ({e})")

    @app_commands.command(name="fila", description="Mostra as músicas na fila de reprodução.")
    async def fila(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if isinstance(vc, wavelink.Player) and not vc.queue.is_empty:
            embed = discord.Embed(title="📜 Fila de Reprodução", color=discord.Color.blue())
            texto = ""
            for i, track in enumerate(vc.queue):
                if i >= 10: 
                    texto += f"\n*... e mais {len(vc.queue) - 10} músicas.*"
                    break
                texto += f"**{i+1}.** [{track.title}]({track.uri})\n"
            
            embed.description = texto
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("A fila está vazia ou estou em Modo Convívio.")

    @app_commands.command(name="skip", description="Passa para a próxima música da fila.")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if isinstance(vc, wavelink.Player) and vc.playing:
            await vc.skip(force=True)
            await interaction.response.send_message("⏭️ Música passada à frente!")
        elif vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("⏭️ Áudio cancelado!")
        else:
            await interaction.response.send_message("Não há nada a tocar.", ephemeral=True)

    @app_commands.command(name="stop", description="Para a música e desconecta o bot.")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            if isinstance(vc, wavelink.Player):
                vc.queue.clear()
            await vc.disconnect()
            await interaction.response.send_message("👋 Sessão terminada!")
        else:
            await interaction.response.send_message("Não estou em nenhum canal de voz.", ephemeral=True)

    @app_commands.command(name="audio", description="Toca um áudio aleatório da pasta de sons.")
    async def audio(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ Tens de estar num canal de voz para eu mandar o áudio!", ephemeral=True)
            return
            
        await interaction.response.defer()
        vc = interaction.guild.voice_client
        if not vc:
            vc = await interaction.user.voice.channel.connect()
            await interaction.followup.send("✅ Entrei no canal para mandar um áudio à sorte!")
            
        pasta_audios = os.path.join(os.getcwd(), 'audios')
        if not os.path.exists(pasta_audios):
            await interaction.followup.send("❌ Não consegui encontrar a pasta 'audios'.")
            return
            
        ficheiros = [f for f in os.listdir(pasta_audios) if f.endswith(('.mp3', '.wav', '.ogg'))]
        if not ficheiros:
            await interaction.followup.send("❌ A pasta de áudios está vazia!")
            return
            
        audio_escolhido = random.choice(ficheiros)
        caminho_completo = os.path.join(pasta_audios, audio_escolhido)

        try:
            if isinstance(vc, wavelink.Player):
                ficheiro_discord = discord.File(caminho_completo)
                msg = await interaction.followup.send(f"🎲 *Áudio surpresa adicionado à fila:* `{audio_escolhido}`", file=ficheiro_discord)
                url = msg.attachments[0].url
                
                resultados = await wavelink.Playable.search(url)
                if resultados:
                    track = resultados.tracks[0] if isinstance(resultados, wavelink.Playlist) else resultados[0]
                    await vc.queue.put_wait(track)
                    
                    if not vc.playing:
                        await vc.play(vc.queue.get())
            else:
                if vc.is_playing():
                    vc.stop()
                    
                fonte = discord.FFmpegPCMAudio(caminho_completo)
                vc.play(fonte)
                await interaction.followup.send(f"📢 **Toma lá disto:** `{audio_escolhido}`")
                
        except Exception as e:
            await interaction.followup.send(f"❌ Oops, o áudio engasgou-se: {e}")

    @app_commands.command(name="leave", description="Desconecta o bot do canal de voz.")
    async def leave(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            if isinstance(vc, wavelink.Player):
                vc.queue.clear()
                
            await vc.disconnect()
            await interaction.response.send_message("👋 Fui embora! Chupem-mos.")
        else:
            await interaction.response.send_message("❌ Eu não estou em nenhum canal de voz!", ephemeral=True)


    @app_commands.command(name="shuffle", description="Baralha as músicas que estão atualmente na fila.")
    async def shuffle(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        
        # Verifica se está no Lavalink e se a fila tem músicas
        if isinstance(vc, wavelink.Player) and not vc.queue.is_empty:
            vc.queue.shuffle()
            await interaction.response.send_message("🔀 **Fila baralhada!** As músicas foram misturadas com sucesso.")
        else:
            await interaction.response.send_message("❌ A fila está vazia ou eu não estou em Modo Música.", ephemeral=True)

    @app_commands.command(name="loop", description="Repete a música atual ou a fila inteira.")
    @app_commands.describe(modo="Escolhe o tipo de repetição que queres")
    @app_commands.choices(modo=[
        app_commands.Choice(name="Desativar (Tocar Normal)", value="normal"),
        app_commands.Choice(name="Repetir Música Atual", value="loop_track"),
        app_commands.Choice(name="Repetir a Fila Inteira", value="loop_queue")
    ])
    async def loop(self, interaction: discord.Interaction, modo: app_commands.Choice[str]):
        vc = interaction.guild.voice_client
        
        if not isinstance(vc, wavelink.Player):
            await interaction.response.send_message("❌ Não estou a tocar música neste momento.", ephemeral=True)
            return

        # Aplica o modo de repetição escolhido
        if modo.value == "normal":
            vc.queue.mode = wavelink.QueueMode.normal
            await interaction.response.send_message("▶️ **Repetição desativada!** As músicas vão tocar normalmente.")
            
        elif modo.value == "loop_track":
            vc.queue.mode = wavelink.QueueMode.loop
            await interaction.response.send_message("🔂 **Loop ativado!** A música atual vai repetir sem parar.")
            
        elif modo.value == "loop_queue":
            vc.queue.mode = wavelink.QueueMode.loop_all
            await interaction.response.send_message("🔁 **Loop da Fila ativado!** A playlist vai tocar em ciclo infinito.")

async def setup(bot):
    await bot.add_cog(Musica(bot))