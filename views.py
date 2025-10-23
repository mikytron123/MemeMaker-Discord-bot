import discord
from typing import Optional, Any, Callable
import traceback
from io import BytesIO
from utils import memerequest, seekrandomframe


class Scroller(discord.ui.View):
    """View class for scrolling, used due to link embed limitation on component v2"""

    def __init__(
        self,
        responselst: list[str],
        embedfunc: Optional[Callable[[Any, int], discord.Embed]] = None,
    ) -> None:
        super().__init__(timeout=20)
        self.count = 0
        self.responselst = responselst
        self.embedfunc = embedfunc

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="⬅️")
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Scroll left in the response list."""
        self.count = max(0, self.count - 1)
        # apply embedding function if it is present
        if self.embedfunc is not None:
            embed = self.embedfunc(self.responselst, self.count)
            await interaction.response.edit_message(embed=embed)
            return
        await interaction.response.edit_message(content=self.responselst[self.count])

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="➡️")
    async def right(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Scroll right in the response list."""
        self.count = min(len(self.responselst) - 1, self.count + 1)
        # apply embedding function if it is present
        if self.embedfunc is not None:
            embed = self.embedfunc(self.responselst, self.count)
            await interaction.response.edit_message(embed=embed)
            return
        await interaction.response.edit_message(content=self.responselst[self.count])
