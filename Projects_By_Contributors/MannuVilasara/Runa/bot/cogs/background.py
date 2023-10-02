import nextcord
import NextcordUtils
from PIL import Image
import aiohttp
import time
import base64
import sys
import os

current = os.path.dirname(os.path.realpath("config.py"))
parent = os.path.dirname(current)
sys.path.append(parent)

from config import WEATHER_KEY
from io import BytesIO
from nextcord.abc import GuildChannel
from nextcord.ext import *
from nextcord import *


class Dropdown(nextcord.ui.Select):
    def __init__(self, message, images, user):
        self.message = message
        self.images = images
        self.user = user
        options = [
            nextcord.SelectOption(label="1"),
            nextcord.SelectOption(label="2"),
            nextcord.SelectOption(label="3"),
            nextcord.SelectOption(label="4"),
            nextcord.SelectOption(label="5"),
            nextcord.SelectOption(label="6"),
            nextcord.SelectOption(label="7"),
            nextcord.SelectOption(label="8"),
            nextcord.SelectOption(label="9"),
        ]
        super().__init__(
            placeholder="Choose the image you want to see!",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: nextcord.Interaction):
        if not int(self.user) == int(interaction.user.id):
            await interaction.response.send_message(
                "You are not the author of this message!", ephemeral=True
            )
        selection = int(self.values[0]) - 1
        image = BytesIO(base64.decodebytes(self.images[selection].encode("utf-8")))
        return await self.message.edit(
            content="Content generated by **craiyon.com**",
            file=nextcord.File(image, "generatedImage.png"),
            view=DropdownView(self.message, self.images, self.user),
        )


class DropdownView(nextcord.ui.View):
    def __init__(self, message, images, user):
        super().__init__()
        self.message = message
        self.images = images
        self.user = user
        self.add_item(Dropdown(self.message, self.images, self.user))


class BackCog(commands.Cog, name="Background"):
    """serverinfo, avatar, ai_paint, weather"""

    def __init__(self, bot):
        self.bot = bot

    # weather
    @nextcord.slash_command(description="Displays the weather")
    async def weather(self, interaction, *, city):
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_KEY}"
        params = {
            #'key': WEATHER_KEY,
            "q": city
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as res:
                data = await res.json()
                location = data["location"]["name"]
                temp_c = data["current"]["temp_c"]
                temp_f = data["current"]["temp_f"]
                humidity = data["current"]["humidity"]
                wind_kph = data["current"]["wind_kph"]
                wind_mph = data["current"]["wind_mph"]
                condition = data["current"]["condition"]["text"]
                image_url = "http:" + data["current"]["condition"]["icon"]

                embed = nextcord.Embed(
                    title=f"Weather for {location}",
                    description=f"The condition in {location} is {condition}",
                    color=0xFD9FA1,
                )
                embed.add_field(name="Temperature", value=f"C: {temp_c} | F: {temp_f}")
                embed.add_field(name="Humidity", value=f"{humidity}")
                embed.add_field(
                    name="Wind Speeds", value=f"KPH: {wind_kph} | MPH: {wind_mph}"
                )
                embed.set_thumbnail(url=image_url)

                await interaction.send(embed=embed)

    # server info
    @nextcord.slash_command(description="Displays the server info")
    async def serverinfo(self, interaction):
        role_count = len(interaction.guild.roles)
        list_of_bots = [bot.mention for bot in interaction.guild.members if bot.bot]
        serverinfoembed = nextcord.Embed(
            timestamp=interaction.created_at, color=interaction.user.color
        )
        serverinfoembed.add_field(
            name="Name", value=f"{interaction.guild.name}", inline=False
        )
        serverinfoembed.add_field(
            name="Member Count", value=f"{interaction.guild.member_count}", inline=False
        )
        serverinfoembed.add_field(
            name="Verification Level",
            value=str(interaction.guild.verification_level),
            inline=False,
        )
        serverinfoembed.add_field(
            name="Number of Roles", value=str(role_count), inline=False
        )
        serverinfoembed.add_field(
            name="Bots", value=", ".join(list_of_bots), inline=False
        )
        await interaction.send(embed=serverinfoembed)

    # avatar
    @nextcord.slash_command(description="Displays a user's profile picture")
    async def avatar(self, interaction, member: nextcord.Member = None):
        if member == None:
            member = interaction.user
        memberAvatar = member.avatar.url
        embed = nextcord.Embed(title=f"{member.name}'s Avatar", color=member.color)
        embed.set_image(url=memberAvatar)
        await interaction.send(embed=embed)

        # ai image generator
        @nextcord.slash_command(description="Generates an AI drawing of a given prompt")
        async def ai_paint(self, interaction, *, prompt: str):
            ETA = int(time.time() + 60)
            msg = await interaction.send(
                f"Go grab a coffee, this may take some time... ETA: <t:{ETA}:R>"
            )
            async with aiohttp.request(
                "POST", "https://backend.craiyon.com/generate", json={"prompt": prompt}
            ) as resp:
                r = await resp.json()
                images = r["images"]
                image = BytesIO(base64.decodebytes(images[0].encode("utf-8")))
                return await msg.edit(
                    content="Content generated by **craiyon.com**",
                    file=nextcord.File(image, "generatedImage.png"),
                    view=DropdownView(msg, images, interaction.user.id),
                )


def setup(bot):
    bot.add_cog(BackCog(bot))
    print("Background is loaded")
