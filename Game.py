import asyncio
import os
import psycopg2
from discord.ext import commands
import discord
import random
import typing
from opensea import get_assets


class Game(commands.Cog):
    """
    Commands related to the game system
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, ctx):
        """
        Start rolling to check out your modifiers and buffs!
        """
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

    @commands.command()
    async def save(self, ctx):
        save = random.randint(1, 6)
        await ctx.send(f"Your save roll is {save}!")

    @commands.command()
    async def turn(self, ctx):
        turn = random.randint(1, 6)
        await ctx.send(f"On this turn you rolled a {turn}!")

    # TODO: Add challenge command, this adds new session in database for those two
    @commands.command()
    async def challenge(self, ctx, user: discord.User,  wager: typing.Optional[int]):
        challenge_embed = discord.Embed(title=f"{ctx.author.display_name} Challenges you to a battle!",
                                        description="Do you accept?")
        if wager is not None or wager >= 0:
            challenge_embed.add_field(name="A wager has been proposed!",
                                      value=f"This will automatically deduct {wager} "
                                            "coins for both participants, until a winner has been found")


        message = await ctx.send(embed=challenge_embed)
        reactions = ['✅', '❌']
        for emoji in reactions:
            await message.add_reaction(emoji)

        def check(reaction, reacted_user):
            return reacted_user == user and str(reaction.emoji) in reactions

        reaction, reacted_user = await self.bot.wait_for('reaction_add', check=check)

        if reaction.emoji == reactions[1]:
            await ctx.send("Challenge invite declined")
        else:
            await ctx.send("Challenge invite accepted!")
            await ctx.send("Please wait until both contestants are finished picking the card they want to use")

            def user1(sent_message):
                return sent_message.author == ctx.author

            HP_1 = await self.bot.wait_for('message')
            while not HP_1.isdigit():
                pass



    @commands.command()
    async def win(self, ctx, user: discord.User):
        """
        Use this after battle to register your win with someone!
        Usage: win (@enemy that lost)
        """
        if user != ctx.author:
            challenge_embed = discord.Embed(title=f"{user.display_name} did {ctx.author.display_name} win this battle?",
                                            description="Accepting will give him a win")
            message = await ctx.send(embed=challenge_embed)
            reactions = ['✅', '❌']
            for emoji in reactions:
                await message.add_reaction(emoji)

            def check(reaction, reacted_user):
                return reacted_user == user and str(reaction.emoji) in reactions

            reaction, reacted_user = await self.bot.wait_for('reaction_add', check=check)
            await message.delete()

            if reaction.emoji == reactions[0]:

                await ctx.send(f"And the winner is {ctx.author.display_name}!!")
                if random.randint(1, 10) == 1:
                    await asyncio.sleep(1)
                    responses = open("buffs.txt").readlines()
                    response = responses[random.randrange(0, len(responses))]
                    await ctx.send(response)

                database_url = os.environ['DATABASE_URL']
                connection = psycopg2.connect(database_url, sslmode='prefer')
                cursor = connection.cursor()

                cursor.execute(f"select user_id from users where user_id = {ctx.author.id}")
                author_exists = cursor.fetchone()
                cursor.execute(f"select user_id from users where user_id = {user.id}")
                user_exists = cursor.fetchone()
                if author_exists:
                    try:
                        cursor.execute(f"UPDATE users SET wins = wins + 1 WHERE user_id = {ctx.author.id}")
                    except Exception as e:
                        print(e)
                else:
                    cursor.execute(f"INSERT INTO users VALUES ({ctx.author.id}, 1, 0)")

                if user_exists:
                    try:
                        cursor.execute(f"UPDATE users SET loses = loses + 1 WHERE user_id = {user.id}")
                    except Exception as e:
                        print(e)
                else:
                    cursor.execute(f"INSERT INTO users VALUES ({user.id}, 0, 1)")

                connection.commit()

            else:
                await ctx.send(f"{ctx.author.mention}, {user.display_name} refuses to accept that you won against him 😦")
        else:
            await ctx.send("You can't win against yourself silly!")


def setup(bot):
    bot.add_cog(Game(bot))
