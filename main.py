import discord
from discord import app_commands
import asyncio
import os

TOKEN = os.getenv("TOKEN")

PERMANENT_ROLE = 1500582215271055393
TEMP_ROLE = 1500583939939500032

MAX_PLAYERS = 5

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

active_stack = {
    "running": False,
    "phase": "none",
    "players": []
}

class JoinView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Join Stack", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not active_stack["running"]:
            await interaction.response.send_message("No active stack.", ephemeral=True)
            return

        member = interaction.user

        has_perm = any(r.id == PERMANENT_ROLE for r in member.roles)
        has_temp = any(r.id == TEMP_ROLE for r in member.roles)

        if not (has_perm or has_temp):
            await interaction.response.send_message("Not in stack roles.", ephemeral=True)
            return

        if active_stack["phase"] == "priority" and not has_perm:
            await interaction.response.send_message("Permanent priority only.", ephemeral=True)
            return

        if member.id in active_stack["players"]:
            await interaction.response.send_message("Already joined.", ephemeral=True)
            return

        if len(active_stack["players"]) >= MAX_PLAYERS:
            await interaction.response.send_message("Stack full.", ephemeral=True)
            return

        active_stack["players"].append(member.id)
        await interaction.response.send_message("Joined!", ephemeral=True)

        if len(active_stack["players"]) == MAX_PLAYERS:
            await end_stack(interaction.channel)


async def end_stack(channel):
    active_stack["running"] = False

    members = [f"<@{uid}>" for uid in active_stack["players"]]
    ping = " ".join(members)

    await channel.send(
        "🎮 **STACK READY**\n\n"
        + "\n".join(members)
        + f"\n\n🚀 {ping}"
    )

    active_stack["players"] = []
    active_stack["phase"] = "none"


@tree.command(name="startstack", description="Start Siege stack")
async def startstack(interaction: discord.Interaction):

    if active_stack["running"]:
        await interaction.response.send_message("Stack already running.", ephemeral=True)
        return

    active_stack["running"] = True
    active_stack["phase"] = "priority"
    active_stack["players"] = []

    view = JoinView()

    await interaction.channel.send(
        "🎮 **SIEGE STACK STARTED**\n"
        "Permanent members first (5 mins)",
        view=view
    )

    await interaction.response.send_message("Started.", ephemeral=True)

    await asyncio.sleep(300)

    if not active_stack["running"]:
        return

    active_stack["phase"] = "open"

    await interaction.channel.send("Temporary members can join now!")

    await asyncio.sleep(300)

    if active_stack["running"]:
        await end_stack(interaction.channel)


@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")


client.run(TOKEN)
