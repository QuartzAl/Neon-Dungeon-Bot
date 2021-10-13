import asyncio
import discord
from discord.ext import commands
from discord.ext import tasks
import os
import random


# Declare the Intents
intents = discord.Intents.default()
# intents.members = True
# intents.reactions = True

# Initialize the Bot class
bot = commands.Bot(command_prefix=commands.when_mentioned_or('.'), case_insensitive=True, intents=intents)
bot.remove_command('help')


# Blocks all Dms
# @bot.check
# async def globally_block_dms(ctx):
#     return ctx.guild is not None


# Load in all the Cogs when ready
@bot.event
async def on_ready():
    cogs = ['Help',
            'Game']

    if __name__ == '__main__':
        for i in cogs:
            bot.load_extension(i)

    print(f"Online! logged in as {bot.user}")

    return await bot.change_presence(activity=discord.Activity(type=0, name="Neon Dungeons"))
    # type 1/0 = playing / streaming
    # type 2 = listening
    # type 3 = watching


@bot.command()
async def invite(ctx):
    embed = discord.Embed(
        title="Invite",
        colour=ctx.author.color,
        url=f"https://discord.com/oauth2/authorize?client_id={bot.user.id}&scope=bot&permissions=8"
    )
    await ctx.send(embed=embed)

secret = os.environ['SECRET']
bot.run(secret)
