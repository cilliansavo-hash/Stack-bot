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
    "sub_phase": False,
    "leaderboard": {},
    "logs": []
}

# ---------------- HELPERS ----------------

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def add_lb(user):
    lb = state["leaderboard"]
    lb[user.id] = lb.get(user.id, 0) + 1


def log_stack(players):
    state["logs"].append({
        "time": now(),
        "size": len(players),
        "players": [p.display_name for p in players]
    })


def reset():
    state["running"] = False
    state["players"].clear()
    state["sub_phase"] = False


# ---------------- FINISH ----------------

async def finish(channel):

    players = list(state["players"])[:5]

    for p in players:
        add_lb(p)

    log_stack(players)

    await channel.send(
        "🔥 STACK STARTED\n" +
        " ".join(p.mention for p in players)
    )

    await channel.send(
        "📜 STACK RECORD\n🕒 " + now() + "\n👥 " +
        ", ".join(p.display_name for p in players)
    )

    reset()


# ---------------- TIMER ----------------

async def timer(channel):

    await asyncio.sleep(300)  # 5 min

    if len(state["players"]) >= 5:
        await finish(channel)
        return

    state["sub_phase"] = True

    await channel.send(
        "🔄 SUBSTITUTES OPEN — JOIN NOW"
    )

    await channel.send(view=JoinView())


# ---------------- VIEWS ----------------

class PermView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="YES", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):

        state["players"].add(interaction.user)

        await interaction.response.send_message(
            f"➕ Joined ({len(state['players'])}/5)"
        )

        if len(state["players"]) >= 5:
            await finish(interaction.channel)

    @discord.ui.button(label="NO", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):

        state["sub_phase"] = True

        await interaction.response.send_message("Sub phase unlocked", ephemeral=True)


class JoinView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="JOIN STACK", style=discord.ButtonStyle.blurple)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):

        state["players"].add(interaction.user)

        await interaction.response.send_message(
            f"➕ Joined ({len(state['players'])}/5)"
        )

        if len(state["players"]) >= 5:
            await finish(interaction.channel)


# ---------------- COMMAND ----------------

@tree.command(name="stackpanel", description="Start system")
async def stackpanel(interaction: discord.Interaction):

    if state["running"]:
        await interaction.response.send_message("Already running", ephemeral=True)
        return

    state["running"] = True
    state["players"].clear()
    state["sub_phase"] = False

    await interaction.response.send_message(
        "🎮 STACK STARTED — PERM PHASE",
        view=PermView()
    )

    asyncio.create_task(timer(interaction.channel))


# ---------------- LEADERBOARD ----------------

@tree.command(name="leaderboard", description="View leaderboard")
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
        "🏆 LEADERBOARD\n" + "\n".join(text)
    )


# ---------------- LOGS ----------------

@tree.command(name="stacklogs", description="View stack history")
async def stacklogs(interaction: discord.Interaction):

    if not state["logs"]:
        await interaction.response.send_message("No logs yet")
        return

    text = []

    for log in state["logs"][-10:]:
        text.append(
            f"{log['time']} | {log['size']} stack | " +
            ", ".join(log["players"])
        )

    await interaction.response.send_message(
        "📜 STACK LOGS\n\n" + "\n\n".join(text)
    )


# ---------------- READY ----------------

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")


client.run(TOKEN)
