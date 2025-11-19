import os
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import app_commands

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
ANNOUNCE_CHANNEL_ID = int(os.getenv("ANNOUNCE_CHANNEL_ID"))
GUILD_ID = int(os.getenv("GUILD_ID"))

ROLE_DEFAULT = os.getenv("ROLE_DEFAULT", "Member")
ROLE_CLIENT = os.getenv("ROLE_CLIENT", "Client")
ROLE_DEVELOPER = os.getenv("ROLE_DEVELOPER", "Developer")
ROLE_CORE = os.getenv("ROLE_CORE", "Core Team")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AelionBot")

# -------------------------------
# BUILD WELCOME EMBED
# -------------------------------
def build_welcome_embed(member):
    embed = discord.Embed(
        title=f"Welcome to TheAelionCode, {member.name}! 👋",
        description="We're excited to have you here!",
        color=0xC5A46D,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(
        name="Get Started",
        value="✔ Read #rules\n✔ Introduce yourself in #introductions\n✔ Check #client-onboarding",
        inline=False
    )
    embed.set_footer(text="TheAelionCode © 2025")
    return embed


# -------------------------------
# ASSIGN DEFAULT ROLES & CLIENT ROLES
# -------------------------------
async def assign_role(member, role_name):
    role = discord.utils.get(member.guild.roles, name=role_name)
    if role:
        await member.add_roles(role)
        logger.info(f"Assigned {role_name} to {member.name}")
    else:
        logger.warning(f"Role '{role_name}' not found.")


# -------------------------------
# ON MEMBER JOIN
# -------------------------------
@bot.event
async def on_member_join(member):
    guild = member.guild
    channel = guild.get_channel(WELCOME_CHANNEL_ID)

    # PUBLIC WELCOME
    embed = build_welcome_embed(member)
    await channel.send(embed=embed)

    # DEFAULT ROLE
    await assign_role(member, ROLE_DEFAULT)

    # SPECIAL DM FOR CLIENTS
    if "client" in member.name.lower():
        await assign_role(member, ROLE_CLIENT)
        await member.send(
            "Hello Client! 👋\n\nWelcome to TheAelionCode.\nOur team will contact you shortly for onboarding."
        )

    else:
        # REGULAR MEMBER DM
        await member.send(
            f"Welcome to TheAelionCode, {member.name}! 😊\n\nIf you have questions, feel free to message us anytime."
        )


# -------------------------------
# SPAM PROTECTION
# -------------------------------
BLACKLIST = ["scam", "hack", "free nitro", "http://", "https://"]
MAX_EMOJIS = 10
MAX_MENTIONS = 5


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # BLOCK BLACKLISTED WORDS
    if any(word in message.content.lower() for word in BLACKLIST):
        await message.delete()
        await message.channel.send(f"{message.author.mention} ⚠ Spam detected and removed.")
        return

    # TOO MANY EMOJIS
    if sum(char in discord.emoji.EMOJI_DATA for char in message.content) > MAX_EMOJIS:
        await message.delete()
        await message.channel.send("⚠ Too many emojis! Message removed.")
        return

    # TOO MANY MENTIONS
    if len(message.mentions) > MAX_MENTIONS:
        await message.delete()
        await message.channel.send("⚠ Too many mentions! Please avoid tagging everyone.")
        return

    await bot.process_commands(message)


# -------------------------------
# SLASH COMMAND: ANNOUNCE
# -------------------------------
@tree.command(name="announce", description="Send an announcement")
@app_commands.default_permissions(administrator=True)
async def announce(interaction: discord.Interaction, message: str):
    channel = interaction.guild.get_channel(ANNOUNCE_CHANNEL_ID)

    embed = discord.Embed(
        title="📢 Announcement",
        description=message,
        color=0xE8C07D,
    )
    embed.set_footer(text=f"Announced by {interaction.user}")

    await channel.send(embed=embed)
    await interaction.response.send_message("Announcement sent!", ephemeral=True)


# -------------------------------
# SLASH COMMAND: PROJECT STATUS
# -------------------------------
PROJECT_STATUS = "No updates yet."


@tree.command(name="project-status", description="View or update project status")
async def project_status(interaction: discord.Interaction, update: str = None):
    global PROJECT_STATUS

    # Developer / Core Team can update
    allowed_roles = ["Developer", "Core Team"]

    if update:
        if any(role.name in allowed_roles for role in interaction.user.roles):
            PROJECT_STATUS = update
            await interaction.response.send_message("Project status updated ✔")
        else:
            await interaction.response.send_message("Permission denied ❌", ephemeral=True)
    else:
        # Clients can only view
        embed = discord.Embed(
            title="📌 Project Status",
            description=PROJECT_STATUS,
            color=0xA68B5B
        )
        await interaction.response.send_message(embed=embed)


# -------------------------------
# BOT READY
# -------------------------------
@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    logger.info("AelionCode Bot is online!")


bot.run(TOKEN)
