import discord
from discord import app_commands
import os
import asyncio
from datetime import datetime

TOKEN = os.getenv("TOKEN")

PERM_ROLE_ID = 1500582215271055393
TEMP_ROLE_ID = 1500583939939500032

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

state = {
    "players": set(),
    "running": False
}


# ---------------- HELPERS ----------------

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def reset():
    state["players"].clear()
    state["running"] = False


# ---------------- BUTTON SYSTEM ----------------

class StackView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # START STACK
    @discord.ui.button(label="Start Stack (Perm)", style=discord.ButtonStyle.green)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):

        if state["running"]:
            await interaction.response.send_message("⚠️ Stack already running", ephemeral=True)
            return

        if not any(r.id == PERM_ROLE_ID for r in interaction.user.roles):
            await interaction.response.send_message("❌ Perm only", ephemeral=True)
            return

        state["running"] = True
        state["players"].add(interaction.user)

        await interaction.response.send_message(
            f"🎮 STACK STARTED\n<@&{PERM_ROLE_ID}>\nClick join below",
            view=self
        )

        asyncio.create_task(timer(interaction.channel))

    # JOIN STACK
    @discord.ui.button(label="Join Stack", style=discord.ButtonStyle.blurple)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not state["running"]:
            await interaction.response.send_message("No stack running", ephemeral=True)
            return

        if interaction.user in state["players"]:
            await interaction.response.send_message("Already joined", ephemeral=True)
            return

        state["players"].add(interaction.user)

        await interaction.response.send_message(
            f"➕ Joined ({len(state['players'])}/5)"
        )

        if len(state["players"]) >= 5:
            await finish(interaction.channel)

    # CANCEL
    @discord.ui.button(label="Cancel Stack", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):

        reset()

        await interaction.response.send_message(
            f"🛑 STACK CANCELLED\n🕒 {now()}"
        )


# ---------------- TIMER ----------------

async def timer(channel):

    await asyncio.sleep(300)

    if len(state["players"]) >= 5:
        await finish(channel)
        return

    await channel.send(
        "🔄 Rotation / Final phase started\nKeep joining!"
    )

    await asyncio.sleep(600)

    if len(state["players"]) < 5:
        await channel.send("❌ Not enough players — stack failed")
        reset()


# ---------------- FINISH STACK ----------------

async def finish(channel):

    players = list(state["players"])[:5]

    mentions = " ".join(p.mention for p in players)

    await channel.send(
        f"🔥 STACK STARTED\n{mentions}"
    )

    await channel.send(
        f"📜 STACK RECORD\n🕒 {now()}\n👥 " +
        ", ".join(p.display_name for p in players)
    )

    reset()


# ---------------- COMMAND ----------------

@tree.command(name="stackpanel", description="Open stack system")
async def stackpanel(interaction: discord.Interaction):

    await interaction.response.send_message(
        "🎮 STACK SYSTEM READY",
        view=StackView()
    )


# ---------------- READY ----------------

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")


client.run(TOKEN)
