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

# ---------------- STATE ----------------

active_players = set()
stack_running = False
leaderboard = {}

# ---------------- LEADERBOARD ----------------

def add_point(member):
    leaderboard[member.id] = leaderboard.get(member.id, 0) + 1


def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------- STACK RECORD ----------------

def make_record(players, status):
    names = ", ".join([p.display_name for p in players])
    return f"📜 STACK RECORD\n🕒 {get_time()}\n👥 {names}\n📌 Status: {status}"


# ---------------- CLEANUP ----------------

@client.event
async def on_message(message):

    global stack_running

    if message.author.bot:
        return

    if not stack_running:
        return

    allowed = ["/stackpanel", "/join", "/leaderboard"]

    if any(message.content.startswith(cmd) for cmd in allowed):
        return

    try:
        await message.delete()
    except:
        pass


# ---------------- FLOW ----------------

async def stack_flow(channel):

    global active_players, stack_running

    # ---------------- PERM PHASE ----------------
    await asyncio.sleep(300)

    await channel.send(
        f"🔄 Rotation phase opening...\n"
        f"<@&{TEMP_ROLE_ID}>\n"
        f"Players: {len(active_players)}"
    )

    # ---------------- ROTATION PHASE ----------------
    await asyncio.sleep(600)

    if len(active_players) >= 5:

        await finish_stack(channel, "Auto Confirmed Stack 5")

        return

    await channel.send(
        "⚠️ **FINAL DECISION PHASE**\n"
        "Not enough players after 10 mins\n"
        "Choose:"
    )

    view = DecisionView()
    await channel.send(view=view)


# ---------------- FINAL DECISION ----------------

class DecisionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Play Stack", style=discord.ButtonStyle.green)
    async def play(self, interaction: discord.Interaction, button: discord.ui.Button):

        await finish_stack(interaction.channel, "Manual Play")

        await interaction.message.edit(view=None)

    @discord.ui.button(label="Cancel Stack", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.channel.send(
            make_record(active_players, "Cancelled")
        )

        global active_players, stack_running

        active_players.clear()
        stack_running = False

        await interaction.message.edit(view=None)


# ---------------- FINISH ----------------

async def finish_stack(channel, reason):

    global active_players, stack_running

    if len(active_players) == 0:
        return

    players = list(active_players)[:5]

    for p in players:
        add_point(p)

    mentions = " ".join(p.mention for p in players)

    await channel.send(
        f"🔥 **STACK CONFIRMED ({reason})**\n{mentions}"
    )

    await channel.send(make_record(players, "Completed"))

    active_players.clear()
    stack_running = False


# ---------------- COMMANDS ----------------

@tree.command(name="stackpanel", description="Start stack system")
async def stackpanel(interaction: discord.Interaction):

    global stack_running, active_players

    if stack_running:
        await interaction.response.send_message(
            "⚠️ Stack already running",
            ephemeral=True
        )
        return

    stack_running = True
    active_players = set()

    await interaction.response.send_message(
        f"🎮 **STACK STARTED**\n"
        f"<@&{PERM_ROLE_ID}>\n"
        f"Join now (5 min perm phase)"
    )

    asyncio.create_task(stack_flow(interaction.channel))


@tree.command(name="join", description="Join stack")
async def join(interaction: discord.Interaction):

    global active_players

    member = interaction.user

    if member in active_players:
        await interaction.response.send_message("Already joined", ephemeral=True)
        return

    active_players.add(member)

    await interaction.response.send_message(
        f"➕ Joined ({len(active_players)}/5)"
    )


@tree.command(name="leaderboard", description="Stack leaderboard")
async def leaderboard_cmd(interaction: discord.Interaction):

    if not leaderboard:
        await interaction.response.send_message("No data yet")
        return

    guild = interaction.guild

    sorted_lb = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)

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
