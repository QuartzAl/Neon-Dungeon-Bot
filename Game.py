from discord.ext import commands
import discord
import random


class Game(commands.Cog):
    """Commands related to the game system"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, ctx):
        """Start rolling to check out your modifiers and buffs!"""
        stats = ['Strength', 'Agility', 'Wisdom', 'Temper', 'Magic']
        message = ""
        for stat in stats:
            mod = random.randint(-5, 15)
            if mod == abs(mod):
                message += f"{stat} +{mod}\n"
            else:
                message += f"{stat} {mod}\n"
        message += '\n'
        responses = open("buffs.txt").readlines()
        buff = responses[random.randrange(0, len(responses))]
        message += f'Buff: "{buff[:-1]}"'

        await ctx.send(message)

    @commands.command(alias=['turn'])
    async def save(self, ctx):
        save = random.randint(1, 6)
        await ctx.send(f"Your save roll is {save}!")


def setup(bot):
    bot.add_cog(Game(bot))