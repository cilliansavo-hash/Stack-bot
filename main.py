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

# ---------------- SAFE STATE (NO GLOBAL KEYWORDS NEEDED) ----------------

state = {
    "active_players": set(),
    "stack_running": False,
    "leaderboard": {}
}


# ---------------- LEADERBOARD ----------------

def add_point(member):
    lb = state["leaderboard"]
    lb[member.id] = lb.get(member.id, 0) + 1


def format_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------- MESSAGE FILTER (optional spam control) ----------------

@client.event
async def on_message(message):

    if message.author.bot:
        return

    if not state["stack_running"]:
        return

    allowed = ["/stackpanel", "/join", "/leaderboard"]

    if any(message.content.startswith(cmd) for cmd in allowed):
        return

    try:
        await message.delete()
    except:
        pass


# ---------------- STACK FLOW ----------------

async def stack_flow(channel):

    players = state["active_players"]

    # 5 min perm phase
    await asyncio.sleep(300)

    await channel.send(
        f"🔄 Rotation phase open\n"
        f"<@&{TEMP_ROLE_ID}>\n"
        f"Players: {len(players)}"
    )

    # 10 min rotation phase
    await asyncio.sleep(600)

    if len(players) >= 5:
        await finish_stack(channel, "Auto Confirmed")
        return

    await channel.send(
        "⚠️ FINAL DECISION PHASE\n"
        + "\n".join([p.display_name for p in players])
    )

    await channel.send(view=DecisionView())


# ---------------- FINISH STACK ----------------

async def finish_stack(channel, reason):

    players = list(state["active_players"])[:5]

    if not players:
        state["stack_running"] = False
        return

    for p in players:
        add_point(p)

    mentions = " ".join(p.mention for p in players)

    record = (
        f"📜 STACK RECORD\n"
        f"🕒 {format_time()}\n"
        f"📌 {reason}\n"
        f"👥 " + ", ".join(p.display_name for p in players)
    )

    await channel.send(f"🔥 STACK CONFIRMED\n{mentions}")
    await channel.send(record)

    state["active_players"].clear()
    state["stack_running"] = False


# ---------------- DECISION BUTTONS ----------------

class DecisionView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Play Stack", style=discord.ButtonStyle.green)
    async def play(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.message.edit(view=None)

        await finish_stack(interaction.channel, "Manual Play")

        await interaction.response.send_message("✅ Stack started")

    @discord.ui.button(label="Cancel Stack", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):

        record = (
            f"📜 STACK RECORD\n"
            f"🕒 {format_time()}\n"
            f"❌ CANCELLED\n"
            + ", ".join(p.display_name for p in state["active_players"])
        )

        await interaction.message.edit(view=None)
        await interaction.channel.send(record)

        state["active_players"].clear()
        state["stack_running"] = False

        await interaction.response.send_message("🛑 Cancelled")


# ---------------- COMMANDS ----------------

@tree.command(name="stackpanel", description="Start stack system")
async def stackpanel(interaction: discord.Interaction):

    if state["stack_running"]:
        await interaction.response.send_message("⚠️ Stack already running", ephemeral=True)
        return

    state["stack_running"] = True
    state["active_players"].clear()

    await interaction.response.send_message(
        f"🎮 STACK STARTED\n<@&{PERM_ROLE_ID}>"
    )

    asyncio.create_task(stack_flow(interaction.channel))


@tree.command(name="join", description="Join stack")
async def join(interaction: discord.Interaction):

    member = interaction.user

    if member in state["active_players"]:
        await interaction.response.send_message("Already joined", ephemeral=True)
        return

    state["active_players"].add(member)

    await interaction.response.send_message(
        f"➕ Joined ({len(state['active_players'])}/5)"
    )


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


# ---------------- READY ----------------

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")


client.run(TOKEN)
