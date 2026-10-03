import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageEnhance, ImageSequence, ImageDraw, ImageFont
import io

class Imagens(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.marca_agua = Image.open("marca_de_agua.png").convert("RGBA")
        nivel_opacidade = 150
        dados_alpha = self.marca_agua.split()[3]
        dados_alpha = dados_alpha.point(lambda p: p * (nivel_opacidade / 255.0))
        self.marca_agua.putalpha(dados_alpha)

    @app_commands.command(name="marca", description="Aplica a marca de água oficial numa imagem ou GIF.")
    @app_commands.describe(ficheiro="A imagem ou GIF a processar", link="Ou o link direto da imagem/GIF")
    async def marca(self, interaction: discord.Interaction, ficheiro: discord.Attachment = None, link: str = None):
        url_imagem = None

        if ficheiro:
            if ficheiro.content_type and ficheiro.content_type.startswith('image/'):
                url_imagem = ficheiro.url
        elif link:
            if link.startswith("http://") or link.startswith("https://"):
                url_imagem = link

        if not url_imagem:
            await interaction.response.send_message("❌ Por favor, anexa uma imagem/GIF ou fornece um link válido.", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url_imagem) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("❌ Não consegui descarregar essa imagem/GIF.")
                        return
                    image_bytes = await resp.read()

            with Image.open(io.BytesIO(image_bytes)) as img:
                if getattr(img, "is_animated", False):
                    frames_modificados = []
                    duracoes = []
                    
                    marca_agua_temp = self.marca_agua.copy()
                    tamanho_proporcional = (img.width // 4, img.height // 4)
                    marca_agua_temp.thumbnail(tamanho_proporcional)

                    x = img.width - marca_agua_temp.width - 10
                    y = img.height - marca_agua_temp.height - 10

                    for frame in ImageSequence.Iterator(img):
                        frame_rgba = frame.convert("RGBA")
                        frame_rgba.paste(marca_agua_temp, (x, y), marca_agua_temp)
                        duracoes.append(frame.info.get('duration', 100))
                        frames_modificados.append(frame_rgba.convert("RGB"))

                    output = io.BytesIO()
                    frames_modificados[0].save(
                        output,
                        format="GIF",
                        save_all=True,
                        append_images=frames_modificados[1:],
                        duration=duracoes,
                        loop=img.info.get('loop', 0)
                    )
                    output.seek(0)
                    ficheiro_final = discord.File(output, filename="com_marca.gif")
                else:
                    imagem_base = img.convert("RGBA")
                    marca_agua_temp = self.marca_agua.copy()

                    tamanho_proporcional = (imagem_base.width // 4, imagem_base.height // 4)
                    marca_agua_temp.thumbnail(tamanho_proporcional)

                    x = imagem_base.width - marca_agua_temp.width - 10
                    y = imagem_base.height - marca_agua_temp.height - 10

                    imagem_base.paste(marca_agua_temp, (x, y), marca_agua_temp)

                    formato = img.format if img.format else "PNG"
                    extensao = "gif" if formato == "GIF" else "png"

                    output = io.BytesIO()
                    if formato == "GIF":
                        imagem_base.convert("RGB").save(output, format="GIF")
                    else:
                        imagem_base.save(output, format="PNG")
                        
                    output.seek(0)
                    ficheiro_final = discord.File(output, filename=f"com_marca.{extensao}")
                    imagem_base.close()

                await interaction.followup.send(file=ficheiro_final)
                output.close()
                marca_agua_temp.close()

        except Exception as e:
            await interaction.followup.send(f"❌ Ocorreu um erro ao processar o ficheiro: {e}")

    @app_commands.command(name="gif", description="Converte uma imagem estática para o formato GIF.")
    @app_commands.describe(ficheiro="A imagem a converter", link="Ou o link direto da imagem")
    async def criar_gif(self, interaction: discord.Interaction, ficheiro: discord.Attachment = None, link: str = None):
        url_imagem = None

        if ficheiro:
            if ficheiro.content_type and ficheiro.content_type.startswith('image/'):
                url_imagem = ficheiro.url
        elif link:
            if link.startswith("http://") or link.startswith("https://"):
                url_imagem = link

        if not url_imagem:
            await interaction.response.send_message("❌ Por favor, anexa uma imagem ou indica um link.", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url_imagem) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("❌ Não consegui descarregar a imagem.")
                        return
                    image_bytes = await resp.read()

            with Image.open(io.BytesIO(image_bytes)) as img:
                if getattr(img, "is_animated", False):
                    await interaction.followup.send("❌ Esse ficheiro já é um GIF animado!")
                    return
                
                output = io.BytesIO()
                img.save(output, format="GIF")
                output.seek(0)
                
                ficheiro_final = discord.File(output, filename="convertido.gif")
                await interaction.followup.send(file=ficheiro_final)
                output.close()

        except Exception as e:
            await interaction.followup.send(f"❌ Ocorreu um erro ao converter a imagem: {e}")

    @app_commands.command(name="caption", description="Adiciona uma legenda meme clássica em caixa branca.")
    @app_commands.describe(texto="O texto da legenda", ficheiro="A imagem/GIF", link="Ou o link direto")
    async def caption(self, interaction: discord.Interaction, texto: str, ficheiro: discord.Attachment = None, link: str = None):
        url_imagem = None

        if ficheiro:
            if ficheiro.content_type and ficheiro.content_type.startswith('image/'):
                url_imagem = ficheiro.url
        elif link:
            if link.startswith("http://") or link.startswith("https://"):
                url_imagem = link

        if not url_imagem:
            await interaction.response.send_message("❌ Anexa uma imagem/GIF ou fornece um link.", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url_imagem) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("❌ Não consegui descarregar a imagem.")
                        return
                    image_bytes = await resp.read()

            with Image.open(io.BytesIO(image_bytes)) as img:
                try:
                    tamanho_fonte = max(20, int(img.width * 0.12))
                    fonte = ImageFont.truetype("futura.otf", tamanho_fonte)
                except Exception:
                    await interaction.followup.send("❌ Erro fatal: O ficheiro `futura.otf` não está na pasta principal do bot!")
                    return

                draw_temp = ImageDraw.Draw(Image.new('RGB', (1, 1)))
                palavras = texto.split()
                linhas = []
                linha_atual = ""
                
                for palavra in palavras:
                    teste = f"{linha_atual} {palavra}".strip()
                    if draw_temp.textlength(teste, font=fonte) <= img.width - 40:
                        linha_atual = teste
                    else:
                        if linha_atual:
                            linhas.append(linha_atual)
                        linha_atual = palavra
                if linha_atual:
                    linhas.append(linha_atual)
                
                texto_formatado = "\n".join(linhas)

                bbox = draw_temp.multiline_textbbox((0, 0), texto_formatado, font=fonte, align="center")
                altura_texto = bbox[3] - bbox[1]
                padding_y = int(tamanho_fonte * 0.4)
                altura_caixa = int(altura_texto + (padding_y * 2.5))

                caixa_branca = Image.new("RGBA", (img.width, altura_caixa), "white")
                draw_caixa = ImageDraw.Draw(caixa_branca)
                draw_caixa.multiline_text(
                    (img.width / 2, padding_y), 
                    texto_formatado, 
                    font=fonte, 
                    fill="black", 
                    align="center", 
                    anchor="ma"
                )

                if getattr(img, "is_animated", False):
                    frames_modificados = []
                    duracoes = []
                    
                    for frame in ImageSequence.Iterator(img):
                        frame_rgba = frame.convert("RGBA")
                        novo_frame = Image.new("RGBA", (img.width, img.height + altura_caixa), "white")
                        novo_frame.paste(caixa_branca, (0, 0))
                        novo_frame.paste(frame_rgba, (0, altura_caixa), frame_rgba)
                        duracoes.append(frame.info.get('duration', 100))
                        frames_modificados.append(novo_frame.convert("RGB"))

                    output = io.BytesIO()
                    frames_modificados[0].save(
                        output,
                        format="GIF",
                        save_all=True,
                        append_images=frames_modificados[1:],
                        duration=duracoes,
                        loop=img.info.get('loop', 0)
                    )
                    output.seek(0)
                    ficheiro_final = discord.File(output, filename="caption.gif")
                else:
                    imagem_base = img.convert("RGBA")
                    nova_img = Image.new("RGBA", (img.width, img.height + altura_caixa), "white")
                    nova_img.paste(caixa_branca, (0, 0))
                    nova_img.paste(imagem_base, (0, altura_caixa), imagem_base)

                    formato = img.format if img.format else "PNG"
                    extensao = "gif" if formato == "GIF" else "png"

                    output = io.BytesIO()
                    if formato == "GIF":
                        nova_img.convert("RGB").save(output, format="GIF")
                    else:
                        nova_img.convert("RGB").save(output, format="PNG")
                        
                    output.seek(0)
                    ficheiro_final = discord.File(output, filename=f"caption.{extensao}")

                await interaction.followup.send(file=ficheiro_final)
                output.close()

        except Exception as e:
            await interaction.followup.send(f"❌ Ocorreu um erro: {e}")

    @app_commands.command(name="uncaption", description="Corta automaticamente a legenda no topo de uma imagem ou GIF.")
    @app_commands.describe(ficheiro="A imagem/GIF", link="Ou o link direto")
    async def uncaption(self, interaction: discord.Interaction, ficheiro: discord.Attachment = None, link: str = None):
        url_imagem = None

        if ficheiro:
            if ficheiro.content_type and ficheiro.content_type.startswith('image/'):
                url_imagem = ficheiro.url
        elif link:
            if link.startswith("http://") or link.startswith("https://"):
                url_imagem = link

        if not url_imagem:
            await interaction.response.send_message("❌ Por favor, anexa uma imagem/GIF ou fornece um link.", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url_imagem) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("❌ Não consegui descarregar a imagem.")
                        return
                    image_bytes = await resp.read()

            with Image.open(io.BytesIO(image_bytes)) as img:
                img_rgb = img.convert("RGB")
                width, height = img_rgb.size
                
                bg_color = img_rgb.getpixel((0, 0))
                
                def diferenca_cor(c1, c2):
                    return abs(c1[0]-c2[0]) + abs(c1[1]-c2[1]) + abs(c1[2]-c2[2])
                
                crop_y = 0
                for y in range(height):
                    esq = img_rgb.getpixel((min(5, width-1), y))
                    dir_pix = img_rgb.getpixel((max(width-6, 0), y))
                    
                    if diferenca_cor(esq, bg_color) > 15 or diferenca_cor(dir_pix, bg_color) > 15:
                        crop_y = y
                        break
                
                if crop_y == 0 or crop_y >= height - 10:
                    await interaction.followup.send("❌ Não consegui detetar uma legenda no topo desta imagem!")
                    return

                box_corte = (0, crop_y, width, height)

                if getattr(img, "is_animated", False):
                    frames_modificados = []
                    duracoes = []
                    
                    for frame in ImageSequence.Iterator(img):
                        frame_rgba = frame.convert("RGBA")
                        frame_cortado = frame_rgba.crop(box_corte)
                        duracoes.append(frame.info.get('duration', 100))
                        frames_modificados.append(frame_cortado.convert("RGB"))

                    output = io.BytesIO()
                    frames_modificados[0].save(
                        output,
                        format="GIF",
                        save_all=True,
                        append_images=frames_modificados[1:],
                        duration=duracoes,
                        loop=img.info.get('loop', 0)
                    )
                    output.seek(0)
                    ficheiro_final = discord.File(output, filename="uncaption.gif")
                else:
                    imagem_base = img.convert("RGBA")
                    imagem_cortada = imagem_base.crop(box_corte)

                    formato = img.format if img.format else "PNG"
                    extensao = "gif" if formato == "GIF" else "png"

                    output = io.BytesIO()
                    if formato == "GIF":
                        imagem_cortada.convert("RGB").save(output, format="GIF")
                    else:
                        imagem_cortada.save(output, format="PNG")
                        
                    output.seek(0)
                    ficheiro_final = discord.File(output, filename=f"uncaption.{extensao}")
                    imagem_base.close()

                await interaction.followup.send(file=ficheiro_final)
                output.close()

        except Exception as e:
            await interaction.followup.send(f"❌ Ocorreu um erro ao cortar a legenda: {e}")

    # ====================================================================
    # FUNÇÃO MESTRE
    # ====================================================================
    async def aplicar_efeito(self, interaction: discord.Interaction, ficheiro: discord.Attachment, link: str, nome_ficheiro: str, funcao_efeito):
        url_imagem = None

        if ficheiro:
            if ficheiro.content_type and ficheiro.content_type.startswith('image/'):
                url_imagem = ficheiro.url
        elif link:
            if link.startswith("http://") or link.startswith("https://"):
                url_imagem = link

        if not url_imagem:
            await interaction.response.send_message("❌ Por favor, anexa uma imagem/GIF ou fornece um link.", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url_imagem) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("❌ Não consegui descarregar a imagem.")
                        return
                    image_bytes = await resp.read()

            with Image.open(io.BytesIO(image_bytes)) as img:
                formato = img.format if img.format else "PNG"
                extensao = "gif" if formato == "GIF" else "png"

                if getattr(img, "is_animated", False):
                    frames_modificados = []
                    duracoes = []
                    
                    for frame in ImageSequence.Iterator(img):
                        frame_editado = funcao_efeito(frame.convert("RGBA"))
                        frames_modificados.append(frame_editado.convert("RGB"))
                        duracoes.append(frame.info.get('duration', 100))

                    output = io.BytesIO()
                    frames_modificados[0].save(
                        output, format="GIF", save_all=True,
                        append_images=frames_modificados[1:],
                        duration=duracoes, loop=img.info.get('loop', 0)
                    )
                    output.seek(0)
                else:
                    imagem_base = img.convert("RGBA")
                    imagem_editada = funcao_efeito(imagem_base)

                    output = io.BytesIO()
                    if formato == "GIF":
                        imagem_editada.convert("RGB").save(output, format="GIF")
                    else:
                        imagem_editada.save(output, format="PNG")
                    output.seek(0)

                ficheiro_final = discord.File(output, filename=f"{nome_ficheiro}.{extensao}")
                await interaction.followup.send(file=ficheiro_final)

        except Exception as e:
            await interaction.followup.send(f"❌ Ocorreu um erro ao editar a imagem: {e}")

    # ====================================================================
    # COMANDOS DE EFEITOS
    # ====================================================================
    @app_commands.command(name="haah", description="Espelha o lado esquerdo da imagem para o lado direito.")
    @app_commands.describe(ficheiro="A imagem/GIF", link="Ou o link direto")
    async def haah(self, interaction: discord.Interaction, ficheiro: discord.Attachment = None, link: str = None):
        def efeito_haah(img):
            width, height = img.size
            meio = (width + 1) // 2
            metade_esq = img.crop((0, 0, meio, height))
            metade_dir = metade_esq.transpose(Image.FLIP_LEFT_RIGHT)
            nova = Image.new("RGBA", (width, height))
            nova.paste(metade_esq, (0, 0))
            nova.paste(metade_dir, (width - meio, 0))
            return nova

        await self.aplicar_efeito(interaction, ficheiro, link, "haah", efeito_haah)

    @app_commands.command(name="hooh", description="Espelha a parte inferior da imagem para a parte superior.")
    @app_commands.describe(ficheiro="A imagem/GIF", link="Ou o link direto")
    async def hooh(self, interaction: discord.Interaction, ficheiro: discord.Attachment = None, link: str = None):
        def efeito_hooh(img):
            width, height = img.size
            meio = (height + 1) // 2
            metade_baixo = img.crop((0, height - meio, width, height))
            metade_cima = metade_baixo.transpose(Image.FLIP_TOP_BOTTOM)
            nova = Image.new("RGBA", (width, height))
            nova.paste(metade_baixo, (0, height - meio))
            nova.paste(metade_cima, (0, 0))
            return nova

        await self.aplicar_efeito(interaction, ficheiro, link, "hooh", efeito_hooh)

    @app_commands.command(name="deepfry", description="Frita a imagem (estoura cores, contraste e nitidez).")
    @app_commands.describe(ficheiro="A imagem/GIF", link="Ou o link direto")
    async def deepfry(self, interaction: discord.Interaction, ficheiro: discord.Attachment = None, link: str = None):
        def efeito_deepfry(img):
            img = img.convert("RGB")
            img = ImageEnhance.Color(img).enhance(4.0)
            img = ImageEnhance.Contrast(img).enhance(3.5)
            img = ImageEnhance.Sharpness(img).enhance(7.0)
            r, g, b = img.split()
            r = r.point(lambda i: min(255, int(i * 1.5)))
            g = g.point(lambda i: min(255, int(i * 1.1)))
            img = Image.merge("RGB", (r, g, b))
            return img.convert("RGBA")

        await self.aplicar_efeito(interaction, ficheiro, link, "deepfry", efeito_deepfry)

async def setup(bot):
    await bot.add_cog(Imagens(bot))