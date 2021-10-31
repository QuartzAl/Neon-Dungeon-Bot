import asyncio
import os
import psycopg2
from discord.ext import commands
import discord
import random
import typing
from urllib.parse import urlparse


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
        await ctx.send(f"Your save roll is {save}! 🎲")

    @commands.command()
    async def turn(self, ctx):
        turn = random.randint(1, 6)
        await ctx.send(f"On this turn you rolled a {turn}! 🎲")

    @commands.command()
    async def register(self, ctx):
        await ctx.author.send("Welcome to the Neon Dungeon, as the guard and keeper of this dungeon "
                              "I will guide you through the registration process")
        own_embed = discord.Embed(
            title="First of all, Do you own a [Neon Dungeon](https://opensea.io/collection/neondungeon) character card?",
            description="Just like the image to the right")
        own_embed.set_thumbnail(url="https://neondungeon.tech/wp-content/uploads/2021/10/4-726x1024.png")

        message = await ctx.author.send(embed=own_embed)
        reactions = ['✅', '❌']
        for emoji in reactions:
            await message.add_reaction(emoji)

        def check(reaction, reacted_user):
            return reacted_user == ctx.author and str(reaction.emoji) in reactions

        reaction, reacted_user = await self.bot.wait_for('reaction_add', check=check)
        # if they said that they don't own an NFT
        if reaction.emoji == reactions[1]:
            market_embed = discord.Embed(
                title="In that case, [visit the market🏪](https://opensea.io/collection/neondungeon) first to pick a card!")
            await ctx.author.send(embed=market_embed)
        else:
            embed = discord.Embed(title="Cool! To prove to my masters that you own this card",
                                  description="I would need the link to this card on [Opensea](https://opensea.io/account)")
            embed.add_field(name="Example", value="https://opensea.io/assets/matic/"
                                                  "0x2953399124f0cbb46d2cbacd8a89cf0599974963/"
                                                  "71443629031568156881543435975776152234932282614143584443465170428761898745857")
            await ctx.author.send(embed=embed)
            message = await self.bot.wait_for('message')
            link = urlparse(message.content)
            not_accepted = True
            while not_accepted:
                if link[0] == '':
                    await ctx.author.send("That isn't a valid link")
                elif link[1].lower() != 'opensea.io':
                    await ctx.author.send("That isn't a valid link")
                elif link[2].split('/')[2] == '0x2953399124f0cbb46d2cbacd8a89cf0599974963':
                    await ctx.author.send("That one clearly isn't yours")
                elif



            message = "Cool! I can't wait to know your friend more, can I know your friend's race?\n" \
                      "React to a choice down below ⬇"
            await ctx.author.send(message)

    # TODO: Finish challenge command, this adds new session in database for the challenger and challenged
    @commands.command()
    async def challenge(self, ctx, user: discord.User, wager: typing.Optional[int]):
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

        database_url = os.environ['DATABASE_URL']
        connection = psycopg2.connect(database_url, sslmode='prefer')
        cursor = connection.cursor()

        cursor.execute(f"SELECT * from cards where user_id = {ctx.author.id}")
        author_card = cursor.fetchone()

        cursor.execute(f"SELECT * from cards where user_id = {user.id}")
        user_cards = cursor.fetchone()

        if reaction.emoji == reactions[1]:
            await ctx.send("Challenge declined")

        elif not user_cards or not author_card:

            if not user_cards and not author_card:
                await ctx.send(
                    f"{user.mention} and {ctx.author.mention}, both of you haven't registered your cards yet! "
                    "Use `.register` then you can start playing!")
            elif not user_cards:
                await ctx.send(f"{user.mention}, you haven't registered your cards yet! "
                               "Use `.register` and I'll show you how")
            elif not author_card:
                await ctx.send(f"{ctx.author.mention}, you haven't registered your cards yet! "
                               "Use `.register` and I'll show you how")

        else:
            await ctx.send("Challenge accepted!")

            if len(user_cards) > 1 or len(author_card) > 1:
                await ctx.send("Please wait until the contestants are finished picking the card they want to use")
                if len(user_cards) > 1:
                    while True:
                        embed = discord.Embed(title="⚔ Please select the card you would like to use in this battle ⚔",
                                              description="Type in a number to the corresponding card you'd like to use")

                        cards = []
                        for number, card in enumerate(user_cards):
                            card_name = card[2]
                            card_id = card[0]
                            embed.add_field(name=card_name, value=str(number + 1))
                            cards.append(card_id)

                        await user.send(embed=embed)
                        reply = await self.bot.wait_for("message", timeout=60)

                        while not reply.isdigit() or int(reply) > len(cards):
                            if not reply.isdigit():
                                await user.send("That isn't a number, please input a valid number")
                            elif int(reply) > len(cards):
                                await user.send(
                                    f"You only have {len(cards)}, please pick a number from the list provided")
                            reply = await self.bot.wait_for("message")

                        reply = int(reply) - 1
                        confirmation = discord.Embed(title="Confirm Selection?",
                                                     description=f"`{user_cards[reply][2]}` will be used for this battle",
                                                     colour=discord.Colour.green())

                        confirm_msg = await ctx.send(embed=confirmation)
                        reactions = ['✅', '❌']
                        for emoji in reactions:
                            await confirm_msg.add_reaction(emoji)

                        def check(reaction, reacted_user):
                            return reacted_user == user and str(reaction.emoji) in reactions

                        reaction, reacted_user = await self.bot.wait_for('reaction_add', check=check)

                        if reaction.emoji == reactions[0]:
                            await user.send("Selection Confirmed!")
                            break
                        else:
                            await confirm_msg.delete()

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
                await ctx.send(
                    f"{ctx.author.mention}, {user.display_name} refuses to accept that you won against him 😦")
        else:
            await ctx.send("You can't win against yourself silly!")

    @commands.command()
    async def profile(self, ctx):
        profile = discord.Embed(title=f"{ctx.author.display_name}'s Profile",
                                description="Followed by a list of items owned!")


def setup(bot):
    bot.add_cog(Game(bot))
