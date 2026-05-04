import discord
from discord import app_commands
import os
import asyncio
from datetime import datetime

TOKEN = os.getenv("TOKEN")

PERM_ROLE_ID = 1500582215271055393

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ---------------- STATE ----------------

state = {
    "running": False,
    "players": set(),
    "leaderboard": {},
    "messages": []
}


# ---------------- HELPERS ----------------

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def add_lb(user):
    lb = state["leaderboard"]
    lb[user.id] = lb.get(user.id, 0) + 1


async def cleanup(channel):
    """Delete all bot messages from this stack"""
    for msg in state["messages"]:
        try:
            await msg.delete()
        except:
            pass
    state["messages"].clear()


def track(msg):
    state["messages"].append(msg)


# ---------------- FINISH STACK ----------------

async def finish(channel, reason="Completed"):

    players = list(state["players"])[:5]

    for p in players:
        add_lb(p)

    mentions = " ".join(p.mention for p in players)

    await cleanup(channel)

    msg1 = await channel.send(f"🔥 STACK STARTED\n{mentions}")
    msg2 = await channel.send(
        f"📜 STACK RECORD\n🕒 {now()}\n📌 {reason}\n👥 " +
        ", ".join(p.display_name for p in players)
    )

    track(msg1)
    track(msg2)

    state["players"].clear()
    state["running"] = False


# ---------------- BUTTONS ----------------

class StackView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # START STACK
    @discord.ui.button(label="Start Stack", style=discord.ButtonStyle.green)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):

        if state["running"]:
            await interaction.response.send_message("⚠️ Stack already running", ephemeral=True)
            return

        if not any(r.id == PERM_ROLE_ID for r in interaction.user.roles):
            await interaction.response.send_message("❌ Perm only", ephemeral=True)
            return

        state["running"] = True
        state["players"].add(interaction.user)

        msg = await interaction.response.send_message(
            "🎮 STACK STARTED — Press Join or Rotation",
            view=self
        )

    # JOIN STACK
    @discord.ui.button(label="Join Stack", style=discord.ButtonStyle.blurple)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not state["running"]:
            await interaction.response.send_message("No stack running", ephemeral=True)
            return

        state["players"].add(interaction.user)

        await interaction.response.send_message(
            f"➕ Joined ({len(state['players'])}/5)"
        )

        if len(state["players"]) >= 5:
            await finish(interaction.channel, "Full Stack (5/5)")

    # ROTATION BUTTON
    @discord.ui.button(label="Rotation Stack", style=discord.ButtonStyle.gray)
    async def rotation(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not state["running"]:
            await interaction.response.send_message("No stack running", ephemeral=True)
            return

        state["players"].add(interaction.user)

        await interaction.response.send_message(
            f"🔄 Rotation joined ({len(state['players'])}/5)"
        )

    # CANCEL / PLAY DECISION TRIGGER
    @discord.ui.button(label="Decision (Play/Cancel)", style=discord.ButtonStyle.red)
    async def decision(self, interaction: discord.Interaction, button: discord.ui.Button):

        if len(state["players"]) == 0:
            await interaction.response.send_message("No players", ephemeral=True)
            return

        view = DecisionView()
        msg = await interaction.channel.send("⚠️ Play or Cancel stack?", view=view)
        track(msg)

        await interaction.response.send_message("Decision opened", ephemeral=True)


# ---------------- DECISION BUTTONS ----------------

class DecisionView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Play Stack", style=discord.ButtonStyle.green)
    async def play(self, interaction: discord.Interaction, button: discord.ui.Button):

        await finish(interaction.channel, "Manually Played")

        await interaction.response.send_message("✅ Stack started")

    @discord.ui.button(label="Cancel Stack", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):

        await cleanup(interaction.channel)

        state["players"].clear()
        state["running"] = False

        await interaction.response.send_message("🛑 Stack cancelled")


# ---------------- LEADERBOARD ----------------

@tree.command(name="leaderboard", description="View stack leaderboard")
async def leaderboard(interaction: discord.Interaction):

    lb = state["leaderboard"]

    if not lb:
        await interaction.response.send_message("No data yet")
        return

    guild = interaction.guild

    sorted_lb = sorted(lb.items(), key=lambda x: x[1], reverse=True)

    text = []

    for uid, count in sorted_lb[:10]:
        member = guild.get_member(uid)
        name = member.display_name if member else "Unknown"
        text.append(f"{name}: {count}")

    await interaction.response.send_message(
        "🏆 STACK LEADERBOARD\n" + "\n".join(text)
    )


# ---------------- PANEL ----------------

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
