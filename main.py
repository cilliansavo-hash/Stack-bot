import discord
from discord import app_commands
import os
import asyncio

TOKEN = os.getenv("TOKEN")

PERM_ROLE_ID = 1500582215271055393
TEMP_ROLE_ID = 1500583939939500032

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

active_players = set()
stack_active = False


class StackView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Start Stack (Perm)", style=discord.ButtonStyle.green)
    async def start_perm(self, interaction: discord.Interaction, button: discord.ui.Button):

        global active_players, stack_active

        if stack_active:
            await interaction.response.send_message("⚠️ Stack already running", ephemeral=True)
            return

        member = interaction.user

        if not any(r.id == PERM_ROLE_ID for r in member.roles):
            await interaction.response.send_message("❌ Permanent only", ephemeral=True)
            return

        active_players.add(member)
        stack_active = True

        await interaction.response.send_message(
            f"👑 {member.display_name} joined stack\n⏳ 5 minute window started",
            ephemeral=False
        )

        await run_stack_timer(interaction.channel)


class RotationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Join Stack (Rotation)", style=discord.ButtonStyle.blurple)
    async def join_rot(self, interaction: discord.Interaction, button: discord.ui.Button):

        member = interaction.user

        if member in active_players:
            await interaction.response.send_message("Already joined", ephemeral=True)
            return

        active_players.add(member)

        await interaction.response.send_message(
            f"➕ {member.display_name} joined stack",
            ephemeral=False
        )

        if len(active_players) >= 5:
            await finish_stack(interaction.channel)


async def run_stack_timer(channel: discord.TextChannel):

    await asyncio.sleep(300)

    if len(active_players) < 5:
        await channel.send("⚠️ Not full — opening rotation join")
        await channel.send("Click to join:", view=RotationView())

    else:
        await finish_stack(channel)


async def finish_stack(channel):

    global active_players, stack_active

    if len(active_players) < 5:
        return

    final = list(active_players)[:5]

    mentions = " ".join(m.mention for m in final)

    await channel.send(
        f"🔥 **STACK STARTED**\n{mentions}\n🎯 Good luck!"
    )

    active_players.clear()
    stack_active = False


@tree.command(name="stackpanel", description="Create stack control panel")
async def stackpanel(interaction: discord.Interaction):

    await interaction.response.send_message(
        "🎮 **Stack Control Panel Ready**",
        view=StackView()
    )


@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")


client.run(TOKEN)
