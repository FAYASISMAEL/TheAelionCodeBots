import os
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import app_commands

load_dotenv()

# ENV VARIABLES
TOKEN = os.getenv("DISCORD_TOKEN")

WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", 0))
ANNOUNCE_CHANNEL_ID = int(os.getenv("ANNOUNCE_CHANNEL_ID", 0))
GUILD_ID = int(os.getenv("GUILD_ID", 0))

ROLE_DEFAULT = os.getenv("ROLE_DEFAULT", "Member")
ROLE_CLIENT = os.getenv("ROLE_CLIENT", "Client")
ROLE_DEVELOPER = os.getenv("ROLE_DEVELOPER", "Developer")
ROLE_CORE = os.getenv("ROLE_CORE", "Core Team")

# INTENTS
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AelionBot")

# ------------------------------------
# WELCOME EMBED
# ------------------------------------
def build_welcome_embed(member: discord.Member):
    embed = discord.Embed(
        title=f"Welcome to TheAelionCode, {member.name}! 👋",
        description="We're excited to have you here!",
        color=0xC5A46D
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(
        name="Get Started",
        value="✔ Read #rules\n✔ Introduce yourself in #introductions\n✔ Check #client-onboarding",
        inline=False
    )
    embed.set_footer(text="TheAelionCode © 2025")
    return embed


# ------------------------------------
# SAFE ROLE ASSIGNMENT
# ------------------------------------
async def assign_role(member: discord.Member, role_name: str):
    role = discord.utils.get(member.guild.roles, name=role_name)
    if role is None:
        logger.warning(f"Role '{role_name}' not found in guild.")
        return

    try:
        await member.add_roles(role)
        logger.info(f"Assigned role '{role_name}' to {member}.")
    except discord.Forbidden:
        logger.error(f"Bot missing permissions to assign role: {role_name}")
    except Exception as e:
        logger.error(f"Error assigning role {role_name}: {e}")


# ------------------------------------
# MEMBER JOIN EVENT
# ------------------------------------
@bot.event
async def on_member_join(member: discord.Member):
    if member.guild is None:
        return  # Safety check

    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)

    if channel:
        embed = build_welcome_embed(member)
        await channel.send(embed=embed)
    else:
        logger.warning("WELCOME_CHANNEL_ID is invalid.")

    # Assign default role
    await assign_role(member, ROLE_DEFAULT)

    # DM messages
    try:
        if "client" in member.name.lower():
            await assign_role(member, ROLE_CLIENT)
            await member.send(
                "Hello Client! 👋\n\nWelcome to TheAelionCode.\nOur team will contact you shortly."
            )
        else:
            await member.send(
                f"Welcome to TheAelionCode, {member.name}! 😊\n"
                "If you have questions, feel free to ask anytime."
            )
    except discord.Forbidden:
        logger.warning("Could not DM new member (DMs blocked).")


# ------------------------------------
# SPAM PROTECTION
# ------------------------------------
BLACKLIST = ["scam", "hack", "free nitro"]
MAX_EMOJIS = 10
MAX_MENTIONS = 5

import emoji

def count_emojis(text: str):
    return sum(1 for char in text if emoji.is_emoji(char))


@bot.event
async def on_message(message: discord.Message):

    if message.author.bot:
        return

    content = message.content.lower()

    # BLACKLIST FILTER
    if any(word in content for word in BLACKLIST):
        await message.delete()
        await message.channel.send(f"{message.author.mention} ⚠ Spam detected and removed.")
        return

    # EMOJI LIMIT
    if count_emojis(message.content) > MAX_EMOJIS:
        await message.delete()
        await message.channel.send("⚠ Too many emojis! Message removed.")
        return

    # MENTION LIMIT
    if len(message.mentions) > MAX_MENTIONS:
        await message.delete()
        await message.channel.send("⚠ Too many mentions! Please avoid tagging everyone.")
        return

    await bot.process_commands(message)


# ------------------------------------
# SLASH COMMAND: ANNOUNCE
# ------------------------------------
@tree.command(name="announce", description="Send an announcement")
@app_commands.default_permissions(administrator=True)
async def announce(interaction: discord.Interaction, message: str):

    channel = interaction.guild.get_channel(ANNOUNCE_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message("Announcement channel not found.", ephemeral=True)
        return

    embed = discord.Embed(
        title="📢 Announcement",
        description=message,
        color=0xE8C07D
    )
    embed.set_footer(text=f"Announced by {interaction.user}")

    await channel.send(embed=embed)
    await interaction.response.send_message("Announcement sent!", ephemeral=True)


# ------------------------------------
# SLASH COMMAND: PROJECT STATUS
# ------------------------------------
PROJECT_STATUS = "No updates yet."

@tree.command(name="project-status", description="View or update the project status")
async def project_status(interaction: discord.Interaction, update: str = None):
    global PROJECT_STATUS

    roles_required = {ROLE_DEVELOPER, ROLE_CORE}
    user_roles = {r.name for r in interaction.user.roles}

    if update:
        # Updating requires privilege
        if user_roles & roles_required:
            PROJECT_STATUS = update
            await interaction.response.send_message("Project status updated ✔")
        else:
            await interaction.response.send_message("Permission denied ❌", ephemeral=True)
        return

    # Viewing
    embed = discord.Embed(
        title="📌 Project Status",
        description=PROJECT_STATUS,
        color=0xA68B5B
    )
    await interaction.response.send_message(embed=embed)


# ------------------------------------
# BOT READY
# ------------------------------------
@bot.event
async def on_ready():
    try:
        guild = discord.Object(id=GUILD_ID)
        await tree.sync(guild=guild)
        logger.info("Slash commands synced successfully.")
    except Exception as e:
        logger.error(f"Command sync failed: {e}")

    logger.info(f"{bot.user} is now online!")


# ------------------------------------
# RUN BOT
# ------------------------------------
bot.run(TOKEN)
