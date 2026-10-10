import asyncio
import random
import time
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands


INVITE_TIMEOUT = 120
CHOICE_TIMEOUT = 10
CHEST_KEYS = {
    "chest": "chests",
    "mega": "mega_chests",
    "ultra": "ultra_chests",
}
CHEST_LABELS = {
    "chest": "🎁 Chest",
    "mega": "💎 Mega Chest",
    "ultra": "⚡ Ultra Chest",
}
CHOICES = {
    "rock": ("🪨", "Rock"),
    "paper": ("📄", "Paper"),
    "scissors": ("✂️", "Scissors"),
}


class RPSGame:
    def __init__(self, cog, challenger, opponent, chest_type, amount):
        self.cog = cog
        self.challenger = challenger
        self.opponent = opponent
        self.chest_type = chest_type
        self.amount = amount
        self.message = None
        self.accepted = False
        self.started = False
        self.finished = False
        self.choices = {}
        self.lock = asyncio.Lock()
        self.invite_deadline = int(time.time()) + INVITE_TIMEOUT

    @property
    def total_pot(self):
        return self.amount * 2

    def chest_label(self):
        return CHEST_LABELS[self.chest_type]

    def layout(self, text, view=None, color=discord.Color.blurple()):
        # Standard Discord embeds/views are used here for broad compatibility.
        return discord.Embed(description=text, color=color)

    async def change_balances(self, deltas):
        """Apply balance changes together using the existing Chests cog storage."""
        chest_cog = self.cog.chests_cog()
        if chest_cog is None:
            raise RuntimeError("Chests cog is not loaded")

        key = CHEST_KEYS[self.chest_type]
        async with chest_cog.open_lock:
            users = {}
            for member in (self.challenger, self.opponent):
                users[member.id] = chest_cog.get_user_data(member.id)

            for member_id, delta in deltas.items():
                if users[member_id].get(key, 0) + delta < 0:
                    return False

            for member_id, delta in deltas.items():
                users[member_id][key] += delta

            await chest_cog.save_data()
        return True

    async def refund(self):
        return await self.change_balances({
            self.challenger.id: self.amount,
            self.opponent.id: self.amount,
        })

    async def settle(self, winner_id=None):
        if self.finished:
            return
        self.finished = True
        if winner_id is None:
            await self.refund()
            result = "🤝 **It's a draw!** Both players get their stakes back."
            color = discord.Color.gold()
        else:
            loser_id = self.opponent.id if winner_id == self.challenger.id else self.challenger.id
            # Both stakes were reserved when the challenge was accepted.
            # Give the full pot to the winner.
            ok = await self.change_balances({winner_id: self.total_pot})
            if not ok:
                # This should not normally happen; return each reserved stake safely.
                await self.refund()
                result = "⚠️ The payout could not be completed, so both stakes were refunded."
                color = discord.Color.orange()
            else:
                winner = self.challenger if winner_id == self.challenger.id else self.opponent
                result = f"🏆 **{winner.mention} wins!** They receive **{self.total_pot} {self.chest_label()}**."
                color = discord.Color.green()

        if self.message:
            try:
                await self.message.edit(
                    content=None,
                    embed=discord.Embed(
                        title="🎮 Rock Paper Scissors — Finished",
                        description=(
                            f"{self.player_line(self.challenger)}\n"
                            f"{self.player_line(self.opponent)}\n\n"
                            f"{result}\n\n"
                            f"📦 Stake: **{self.amount} {self.chest_label()} each**"
                        ),
                        color=color,
                    ),
                    view=None,
                )
            except (discord.HTTPException, discord.NotFound):
                pass

    def player_line(self, member):
        choice = self.choices.get(member.id)
        if choice:
            emoji, label = CHOICES[choice]
            return f"✅ {member.mention}: {emoji} **{label}**"
        return f"❌ {member.mention}: *Waiting for choice…*"

    def invite_embed(self):
        return discord.Embed(
            title="🎮 Rock Paper Scissors Challenge",
            description=(
                f"{self.challenger.mention} challenges {self.opponent.mention}!\n\n"
                f"📦 Stake: **{self.amount} {self.chest_label()} each**\n"
                f"🏆 Winner gets **{self.total_pot}**. A draw refunds both stakes.\n"
                f"⏳ Expires <t:{self.invite_deadline}:R>."
            ),
            color=discord.Color.blurple(),
        )

    def game_embed(self):
        return discord.Embed(
            title="🎮 Rock Paper Scissors",
            description=(
                f"{self.player_line(self.challenger)}\n"
                f"{self.player_line(self.opponent)}\n\n"
                f"📦 Stake: **{self.amount} {self.chest_label()} each**\n"
                f"⏱️ Choose within **{CHOICE_TIMEOUT} seconds**. Missing choices become random."
            ),
            color=discord.Color.green(),
        )


class InviteView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=INVITE_TIMEOUT)
        self.game = game

    @discord.ui.button(label="Accept", emoji="✅", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        game = self.game
        if interaction.user.id != game.opponent.id:
            await interaction.response.send_message("Only the invited player can accept this challenge.", ephemeral=True)
            return
        if game.accepted or game.finished:
            await interaction.response.send_message("This challenge is no longer available.", ephemeral=True)
            return

        chest_cog = game.cog.chests_cog()
        if chest_cog is None:
            await interaction.response.send_message("The chest system is unavailable right now.", ephemeral=True)
            return

        key = CHEST_KEYS[game.chest_type]
        async with chest_cog.open_lock:
            challenger_data = chest_cog.get_user_data(game.challenger.id)
            opponent_data = chest_cog.get_user_data(game.opponent.id)
            if challenger_data.get(key, 0) < game.amount or opponent_data.get(key, 0) < game.amount:
                await interaction.response.send_message(
                    "One of the players no longer has enough chests. The challenge was cancelled.",
                    ephemeral=True,
                )
                game.finished = True
                self.stop()
                await interaction.message.edit(embed=discord.Embed(
                    title="❌ Challenge Cancelled",
                    description="One of the players does not have enough chests for this stake.",
                    color=discord.Color.red(),
                ), view=None)
                return
            challenger_data[key] -= game.amount
            opponent_data[key] -= game.amount
            await chest_cog.save_data()

        game.accepted = True
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="✅ Challenge Accepted",
                description=(
                    f"{game.opponent.mention} accepted the challenge.\n\n"
                    f"📦 **{game.amount} {game.chest_label()}** from each player is reserved.\n"
                    f"Only {game.challenger.mention} can press **Start Game**."
                ),
                color=discord.Color.green(),
            ),
            view=AcceptedView(game),
        )
        self.stop()

    @discord.ui.button(label="Cancel", emoji="✖️", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        game = self.game
        if interaction.user.id != game.challenger.id:
            await interaction.response.send_message("Only the player who sent the challenge can cancel it.", ephemeral=True)
            return
        if game.finished:
            await interaction.response.send_message("This challenge is already closed.", ephemeral=True)
            return
        game.finished = True
        await interaction.response.edit_message(
            embed=discord.Embed(title="❌ Challenge Cancelled", description="The challenge was cancelled.", color=discord.Color.red()),
            view=None,
        )
        self.stop()

    async def on_timeout(self):
        game = self.game
        if game.accepted or game.finished:
            return
        game.finished = True
        if game.message:
            try:
                await game.message.edit(
                    embed=discord.Embed(
                        title="⏰ Challenge Expired",
                        description="The challenge expired because it was not accepted in time.",
                        color=discord.Color.gold(),
                    ),
                    view=None,
                )
            except (discord.HTTPException, discord.NotFound):
                pass


class AcceptedView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=None)
        self.game = game

    @discord.ui.button(label="Start Game", emoji="▶️", style=discord.ButtonStyle.success)
    async def start_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        game = self.game
        if interaction.user.id != game.challenger.id:
            await interaction.response.send_message("Only the challenger can start the game.", ephemeral=True)
            return
        if game.finished or game.started:
            await interaction.response.send_message("This game is already closed or started.", ephemeral=True)
            return
        game.started = True
        view = GameView(game)
        await interaction.response.edit_message(embed=game.game_embed(), view=view)
        game.message = interaction.message
        view.task = asyncio.create_task(view.run_timer())

    @discord.ui.button(label="Cancel and Refund", emoji="↩️", style=discord.ButtonStyle.danger)
    async def cancel_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        game = self.game
        if interaction.user.id != game.challenger.id:
            await interaction.response.send_message("Only the challenger can cancel this game.", ephemeral=True)
            return
        if game.started or game.finished:
            await interaction.response.send_message("The game has already started or finished.", ephemeral=True)
            return
        await game.refund()
        game.finished = True
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="↩️ Challenge Cancelled",
                description="The reserved stakes have been returned to both players.",
                color=discord.Color.gold(),
            ),
            view=None,
        )
        self.stop()


class GameView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=None)
        self.game = game
        self.task = None

        for key, (emoji, label) in CHOICES.items():
            button = discord.ui.Button(label=label, emoji=emoji, style=discord.ButtonStyle.primary)
            button.callback = self.make_choice_callback(key)
            self.add_item(button)

    def make_choice_callback(self, choice):
        async def callback(interaction: discord.Interaction):
            game = self.game
            if interaction.user.id not in (game.challenger.id, game.opponent.id):
                await interaction.response.send_message("You are not a player in this game.", ephemeral=True)
                return
            if game.finished:
                await interaction.response.send_message("This game has already finished.", ephemeral=True)
                return

            old = game.choices.get(interaction.user.id)
            if old == choice:
                await interaction.response.send_message("You have already selected that option.", ephemeral=True)
                return
            game.choices[interaction.user.id] = choice
            if old:
                old_label = CHOICES[old][1]
                new_label = CHOICES[choice][1]
                await interaction.response.send_message(f"You changed your choice: **{old_label} → {new_label}**.", ephemeral=True)
                await game.message.edit(embed=game.game_embed(), view=self)
            else:
                await interaction.response.edit_message(embed=game.game_embed(), view=self)

            if len(game.choices) == 2:
                await self.finish_round()
        return callback

    async def run_timer(self):
        try:
            await asyncio.sleep(CHOICE_TIMEOUT)
            if self.game.finished:
                return
            for player in (self.game.challenger, self.game.opponent):
                if player.id not in self.game.choices:
                    self.game.choices[player.id] = random.choice(tuple(CHOICES.keys()))
            await self.finish_round()
        except asyncio.CancelledError:
            pass

    async def finish_round(self):
        game = self.game
        async with game.lock:
            if game.finished:
                return
            a = game.choices.get(game.challenger.id)
            b = game.choices.get(game.opponent.id)
            if not a or not b:
                return
            if a == b:
                winner_id = None
            elif (a, b) in (("rock", "scissors"), ("paper", "rock"), ("scissors", "paper")):
                winner_id = game.challenger.id
            else:
                winner_id = game.opponent.id
            if self.task and self.task is not asyncio.current_task():
                self.task.cancel()
            await game.settle(winner_id)
            self.stop()


class RPS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def chests_cog(self):
        return self.bot.get_cog("Chests")

    @app_commands.command(name="rps", description="Challenge a player to Rock Paper Scissors for chests.")
    @app_commands.describe(
        invite="The player you want to challenge",
        chest_type="Which chest type to stake",
        amount="How many chests each player stakes",
    )
    async def rps(
        self,
        interaction: discord.Interaction,
        invite: discord.Member,
        chest_type: Literal["chest", "mega", "ultra"],
        amount: app_commands.Range[int, 1, 100000],
    ):
        if invite.bot:
            await interaction.response.send_message("You cannot challenge a bot.", ephemeral=True)
            return
        if invite.id == interaction.user.id:
            await interaction.response.send_message("You cannot challenge yourself.", ephemeral=True)
            return
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        chest_cog = self.chests_cog()
        if chest_cog is None:
            await interaction.response.send_message("The chest system is unavailable right now.", ephemeral=True)
            return

        key = CHEST_KEYS[chest_type]
        async with chest_cog.open_lock:
            challenger_data = chest_cog.get_user_data(interaction.user.id)
            opponent_data = chest_cog.get_user_data(invite.id)
            if challenger_data.get(key, 0) < amount:
                await interaction.response.send_message(
                    f"You do not have enough {CHEST_LABELS[chest_type]}s. Your balance: **{challenger_data.get(key, 0)}**.",
                    ephemeral=True,
                )
                return
            if opponent_data.get(key, 0) < amount:
                await interaction.response.send_message(
                    f"{invite.mention} does not currently have enough {CHEST_LABELS[chest_type]}s for this stake.",
                    ephemeral=True,
                )
                return

        game = RPSGame(self, interaction.user, invite, chest_type, amount)
        view = InviteView(game)
        await interaction.response.send_message(embed=game.invite_embed(), view=view)
        game.message = await interaction.original_response()


async def setup(bot):
    await bot.add_cog(RPS(bot))
    print("✅ rps.py loaded!")
 
