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
rotation_open = False


class StackView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Start Stack (Perm)", style=discord.ButtonStyle.green)
    async def start_stack(self, interaction: discord.Interaction, button: discord.ui.Button):

        global active_players, stack_active

        if stack_active:
            await interaction.response.send_message("⚠️ Stack already running", ephemeral=True)
            return

        member = interaction.user

        if not any(r.id == PERM_ROLE_ID for r in member.roles):
            await interaction.response.send_message("❌ Permanent members only", ephemeral=True)
            return

        stack_active = True
        active_players.add(member)

        await interaction.response.send_message(
            f"🎮 **STACK STARTED** by {member.mention}\n"
            f"👑 Permanent phase active (5 mins)\n"
            f"<@&{PERM_ROLE_ID}> <@&{TEMP_ROLE_ID}>",
            allowed_mentions=discord.AllowedMentions(roles=True)
        )

        await run_timer(interaction.channel)


class RotationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Join Stack (Rotation)", style=discord.ButtonStyle.blurple)
    async def join_stack(self, interaction: discord.Interaction, button: discord.ui.Button):

        global active_players

        member = interaction.user

        if member in active_players:
            await interaction.response.send_message("Already in stack", ephemeral=True)
            return

        active_players.add(member)

        await interaction.response.send_message(
            f"➕ {member.mention} joined stack ({len(active_players)}/5)",
            allowed_mentions=discord.AllowedMentions(users=True)
        )

        if len(active_players) >= 5:
            await finish_stack(interaction.channel)


async def run_timer(channel):

    global rotation_open

    await asyncio.sleep(300)

    if len(active_players) < 5:
        rotation_open = True

        await channel.send(
            "⚠️ Not full after 5 mins\n"
            "🔄 Rotation phase now open (click to join)"
        )

        await channel.send(view=RotationView())

    else:
        await finish_stack(channel)


async def finish_stack(channel):

    global active_players, stack_active, rotation_open

    if len(active_players) < 5:
        return

    final_team = list(active_players)[:5]

    mentions = " ".join(m.mention for m in final_team)

    await channel.send(
        f"🔥 **STACK READY**\n{mentions}\n🎯 Good luck!"
    )

    active_players.clear()
    stack_active = False
    rotation_open = False


@tree.command(name="stackpanel", description="Open stack system")
async def stackpanel(interaction: discord.Interaction):

    await interaction.response.send_message(
        "🎮 **Siege Stack Panel Ready**\nPress button to start",
        view=StackView()
    )


@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")


client.run(TOKEN)
