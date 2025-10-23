from io import BytesIO
import traceback
from typing import Any, Callable
import discord

from utils import memerequest, seekrandomframe


class ScrollerButton(discord.ui.ActionRow):
    def __init__(self, view):
        super().__init__()
        self.__view = view

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⬅️")
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Scroll left in the response list."""
        self.__view.count = max(0, self.__view.count - 1)

        embed = self.__view.containerfunc(self.__view.responselst, self.__view.count)

        self.update(embed)

        await interaction.response.edit_message(view=self.__view)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="➡️")
    async def right(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Scroll right in the response list."""
        new_count = min((self.__view.total_count) - 1, self.__view.count + 1)
        self.__view.count = new_count

        embed = self.__view.containerfunc(self.__view.responselst, self.__view.count)

        self.update(embed)

        await interaction.response.edit_message(view=self.__view)

    def update(self, embed):
        """updates view to match new container"""
        for ii in range(len(embed.children)):
            cont_child = self.__view.container.children[ii]
            embed_child = embed.children[ii]

            if isinstance(cont_child, discord.ui.TextDisplay):
                cont_child.content = embed_child.content
            elif isinstance(cont_child, discord.ui.MediaGallery):
                cont_child.items = embed_child.items


class ScrollerV2(discord.ui.LayoutView):
    def __init__(
        self,
        responselst: list[str],
        containerfunc: Callable[[Any, int], Any],
    ) -> None:
        super().__init__(timeout=25)
        self.count = 0
        self.responselst = responselst
        self.total_count = len(responselst)
        self.containerfunc = containerfunc
        self.message = None
        container = self.containerfunc(self.responselst, 0)

        self.buttons = ScrollerButton(self)
        container.add_item(self.buttons)
        self.container = container
        self.add_item(container)

    async def on_timeout(self) -> None:
        for child in self.walk_children():
            child.disabled = True  # type: ignore

        await self.message.edit(view=self)


class Form(discord.ui.Modal, title="Form"):
    def __init__(self, url: str, filename) -> None:
        super().__init__()
        self.background = url
        self.filename = filename

    text: discord.ui.TextInput = discord.ui.TextInput(
        label="caption",
        placeholder="Enter image caption ...",
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handles the submission of the form to generate a meme."""
        imagebytes = await memerequest(self.background, self.text.value)
        await interaction.response.send_message(
            file=discord.File(fp=BytesIO(imagebytes), filename=self.filename),
        )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.response.send_message(
            "Oops! Something went wrong.", ephemeral=True
        )

        # Make sure we know what the error actually is
        traceback.print_exception(type(error), error)


class EditViewButton(discord.ui.ActionRow):
    def __init__(self, view):
        super().__init__()
        self.__view = view

    @discord.ui.button(style=discord.ButtonStyle.primary, label="Edit")
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            Form(self.__view.background, self.__view.filename)
        )


class EditView(discord.ui.LayoutView):
    def __init__(self, url: str, filename: str, imagebytes: bytes) -> None:
        super().__init__(timeout=60)
        self.background = url
        self.filename = filename
        self.message = None

        container = discord.ui.Container(
            discord.ui.MediaGallery().add_item(
                media=discord.File(fp=BytesIO(imagebytes), filename=filename)
            ),
            EditViewButton(self),
        )
        self.add_item(container)

    async def on_timeout(self) -> None:
        for child in self.walk_children():
            child.disabled = True  # type: ignore

        await self.message.edit(view=self)


class RerollButton(discord.ui.ActionRow):
    def __init__(self, view):
        super().__init__()
        self.__view = view

    @discord.ui.button(style=discord.ButtonStyle.gray, label="Reroll")
    async def reroll(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Rerolls to get a different frame from the image bytes."""
        image_binary = seekrandomframe(self.__view.imgbytes)
        output_file = discord.File(fp=image_binary, filename=self.__view.filename)
        await interaction.response.send_message(
            content=interaction.user.mention, file=output_file
        )


class RerollView(discord.ui.LayoutView):
    def __init__(self, imgbytes: bytes, filename: str, image_binary: BytesIO) -> None:
        super().__init__(timeout=60)
        self.imgbytes = imgbytes
        self.filename = filename
        self.message = None

        container = discord.ui.Container()
        image_gallery = discord.ui.MediaGallery()
        image_gallery.add_item(media=discord.File(fp=image_binary, filename=filename))
        container.add_item(image_gallery)

        self.buttons = RerollButton(self)
        container.add_item(self.buttons)
        self.add_item(container)

    async def on_timeout(self) -> None:
        for child in self.walk_children():
            child.disabled = True  # type: ignore

        await self.message.edit(view=self)
