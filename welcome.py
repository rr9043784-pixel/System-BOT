
from __future__ import annotations

import logging

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

WELCOME_CHANNEL_ID = 1522585690389483550
AUTO_ROLE_ID = 1522587434208989344


class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild

        # Give the automatic role
        role = guild.get_role(AUTO_ROLE_ID)

        if role is not None:
            try:
                await member.add_roles(
                    role,
                    reason="Automatic welcome role"
                )
            except discord.Forbidden:
                logger.error(
                    "Cannot assign role. Check Manage Roles permission "
                    "and bot role hierarchy."
                )
            except discord.HTTPException:
                logger.exception("Failed to assign welcome role.")
        else:
            logger.error("Welcome role not found: %s", AUTO_ROLE_ID)

        # Get welcome channel
        channel = guild.get_channel(WELCOME_CHANNEL_ID)

        if channel is None:
            try:
                channel = await self.bot.fetch_channel(
                    WELCOME_CHANNEL_ID
                )
            except discord.HTTPException:
                logger.exception("Welcome channel not found.")
                return

        if not isinstance(channel, discord.TextChannel):
            logger.error("Welcome channel is not a text channel.")
            return

        # Welcome embed
        embed = discord.Embed(
            description=(
                f"Hello! **{member.mention}** You're on the server "
                f"`{guild.name}`\n"
                f"Now in the north it has become `{guild.member_count}`\n"
                f"-# -------------------------------\n\n"
                f"* Please complete verification before chatting "
                f"on the server! ┃<#{1546998884830683176}>\n\n"
                f"* You get a role ┃<@&{AUTO_ROLE_ID}>\n\n"
                f"* Please go to this channel and make whoever you "
                f"need (required) ┃<#{1541336807508017252}>\n\n"
                f"* You will be able to select the ping role to "
                f"receive notifications about new server news! "
                f"┃<#{1541718209533575228}>\n\n"
                f"* Here you can see how many members there are "
                f"on the server, and so on ┃<#{1542994435472760953}>\n\n"
                f"* And be sure to read the server rules! "
                f"┃<#{1544445189156769834}>"
            ),
            color=discord.Color.from_rgb(0, 0, 0)
        )

        try:
            await channel.send(
                content=f"{member.mention}",
                embed=embed,
                allowed_mentions=discord.AllowedMentions(
                    users=True,
                    roles=False
                )
            )
        except discord.HTTPException:
            logger.exception("Failed to send welcome message.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
 
