import discord
from discord import app_commands
import os
import asyncio

TOKEN = os.getenv("TOKEN")

PERM_ROLE_ID = 1500582215271055393
TEMP_ROLE_ID = 1500583939939500032

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")


@tree.command(name="startstack", description="Start Siege 5-stack system")
async def startstack(interaction: discord.Interaction):

    guild = interaction.guild

    # Phase 1 message
    await interaction.response.send_message(
        "🎮 **Stack Started**\n👑 Permanent members ONLY can join (5 mins)\nReact 👍",
        ephemeral=False
    )

    msg = await interaction.channel.send("👑 Permanent phase active — react 👍")
    await msg.add_reaction("👍")

    # Wait 5 minutes
    await asyncio.sleep(300)

    msg = await interaction.channel.fetch_message(msg.id)

    perm_players = set()

    for reaction in msg.reactions:
        if str(reaction.emoji) == "👍":
            async for user in reaction.users():
                if user.bot:
                    continue
                member = guild.get_member(user.id)
                if member and any(r.id == PERM_ROLE_ID for r in member.roles):
                    perm_players.add(member)

    stack = list(perm_players)

    # If full already
    if len(stack) >= 5:
        final_team = stack[:5]

    else:
        needed = 5 - len(stack)

        # Phase 2
        second_msg = await interaction.channel.send(
            f"⚠️ Not full ({len(stack)}/5). Opening to ALL players for {needed} spots (5 mins)"
        )
        await second_msg.add_reaction("👍")

        await asyncio.sleep(300)

        second_msg = await interaction.channel.fetch_message(second_msg.id)

        all_players = set(stack)

        for reaction in second_msg.reactions:
            if str(reaction.emoji) == "👍":
                async for user in reaction.users():
                    if user.bot:
                        continue
                    member = guild.get_member(user.id)
                    if member:
                        all_players.add(member)

        final_team = list(all_players)[:5]

    if not final_team:
        await interaction.channel.send("❌ No players joined stack.")
        return

    mentions = " ".join(m.mention for m in final_team)

    await interaction.channel.send(
        f"🔥 **FINAL SIEGE STACK READY:**\n{mentions}\n🎯 Good luck!"
    )


client.run(TOKEN)
