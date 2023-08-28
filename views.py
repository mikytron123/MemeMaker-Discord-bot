import discord
from typing import Optional,Any,Callable
import traceback
from io import BytesIO
from utils import memerequest, seekrandomframe

class Scroller(discord.ui.View):
    def __init__(
        self,
        responselst,
        embedfunc: Optional[Callable[[Any, int], discord.Embed]] = None,
    ) -> None:
        super().__init__(timeout=20)
        self.count = 0
        self.responselst = responselst
        self.embedfunc = embedfunc

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="⬅️")
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.count = max(0, self.count - 1)
        if self.embedfunc is not None:
            embed = self.embedfunc(self.responselst, self.count)
            await interaction.response.edit_message(embed=embed)
            return
        await interaction.response.edit_message(content=self.responselst[self.count])

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="➡️")
    async def right(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.count = min(len(self.responselst) - 1, self.count + 1)
        if self.embedfunc is not None:
            embed = self.embedfunc(self.responselst, self.count)
            await interaction.response.edit_message(embed=embed)
            return
        await interaction.response.edit_message(content=self.responselst[self.count])

class Form(discord.ui.Modal, title="Form"):
    def __init__(self, url: str, filename) -> None:
        super().__init__()
        self.background = url
        self.filename = filename

    # This will be a short input, where the user can enter their name
    # It will also have a placeholder, as denoted by the `placeholder` kwarg.
    # By default, it is required and is a short-style input which is exactly
    # what we want.
    text = discord.ui.TextInput(
        label="caption",
        placeholder="Enter image caption ...",
    )

    async def on_submit(self, interaction: discord.Interaction):
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

class EditView(discord.ui.View):
    def __init__(self, url: str, filename: str) -> None:
        super().__init__(timeout=60)
        self.background = url
        self.filename = filename

    @discord.ui.button(style=discord.ButtonStyle.gray, label="Edit")
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(Form(self.background, self.filename))

class RerollView(discord.ui.View):
    def __init__(self, imgbytes:bytes, filename: str) -> None:
        super().__init__(timeout=60)
        self.imgbytes = imgbytes
        self.filename = filename

    @discord.ui.button(style=discord.ButtonStyle.gray, label="Reroll")
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        image_binary = seekrandomframe(self.imgbytes)
        output_file = discord.File(fp=image_binary, filename=self.filename)
        await interaction.response.send_message(content=interaction.user.mention,
                                                file=output_file)
