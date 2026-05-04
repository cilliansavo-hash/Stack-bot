import discord
from discord import app_commands
import os
import asyncio
from datetime import datetime, timedelta

TOKEN = os.getenv("TOKEN")

PERM_ROLE_ID = 1500582215271055393
TEMP_ROLE_ID = 1500583939939500032

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

active_players = set()
leaderboard = {}  # user_id -> count
stack_active = False


# ---------------- LEADERBOARD SYSTEM ----------------

def add_to_leaderboard(member):
    uid = member.id
    if uid not in leaderboard:
        leaderboard[uid] = 0
    leaderboard[uid] += 1


def get_ranked():
    return sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)


# ---------------- STACK LEVEL SYSTEM ----------------

def get_stack_level(count):
    if count <= 1:
        return "🥉 Stack 1"
    elif count == 2:
        return "🥈 Stack 2"
    elif count == 3:
        return "🥈 Stack 3"
    elif count == 4:
        return "🥇 Stack 4"
    else:
        return "🔥 Stack 5"


# ---------------- STACK FINISH ----------------

async def finish_stack(channel):

    global active_players

    for p in active_players:
        add_to_leaderboard(p)

    count = len(active_players)
    level = get_stack_level(count)

    mentions = " ".join(p.mention for p in active_players)

    await channel.send(
        f"{level} **STACK CONFIRMED**\n"
        f"{mentions}\n"
        f"🎯 Good luck!"
    )

    active_players.clear()


# ---------------- TIMER ----------------

async def stack_timer(channel):

    await asyncio.sleep(600)

    if len(active_players) >= 5:
        await finish_stack(channel)
    else:
        await channel.send(
            f"⚠️ Not full ({len(active_players)}/5)\nStack failed or waiting..."
        )


# ---------------- BUTTONS ----------------

class StackView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Join Stack", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):

        member = interaction.user

        if member in active_players:
            await interaction.response.send_message("Already joined", ephemeral=True)
            return

        active_players.add(member)

        await interaction.response.send_message(
            f"➕ {member.display_name} joined ({len(active_players)}/5)"
        )


# ---------------- COMMANDS ----------------

@tree.command(name="stackpanel", description="Start stack system")
async def stackpanel(interaction: discord.Interaction):

    await interaction.response.send_message(
        "🎮 Stack started — join now",
        view=StackView()
    )

    await stack_timer(interaction.channel)


@tree.command(name="leaderboard", description="Show stack leaderboard")
async def leaderboard_cmd(interaction: discord.Interaction):

    ranked = get_ranked()

    if not ranked:
        await interaction.response.send_message("No data yet")
        return

    guild = interaction.guild
    lines = []

    for uid, count in ranked[:10]:
        member = guild.get_member(uid)
        name = member.display_name if member else "Unknown"
        lines.append(f"{name}: {count} stacks")

    await interaction.response.send_message(
        "🏆 **STACK LEADERBOARD (Top 10)**\n" + "\n".join(lines)
    )


# ---------------- DAILY RESET ----------------

async def reset_leaderboard():
    while True:
        await asyncio.sleep(86400)  # 24h
        leaderboard.clear()
        print("Leaderboard reset")


@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")
    client.loop.create_task(reset_leaderboard())


client.run(TOKEN)
