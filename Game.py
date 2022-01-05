import asyncio
import datetime
import os
import psycopg2
from discord.ext import commands
import discord
import random
import typing
from urllib.parse import urlparse
import json


class Game(commands.Cog):
    """
    Commands related to the game system
    """

    def __init__(self, bot):
        self.bot = bot
        database_url = os.environ['DATABASE_URL']
        self.connection = psycopg2.connect(database_url, sslmode='prefer')
        self.cursor = self.connection.cursor()

    def get_race_emojis(self):
        """Gets all of the race emojis and returns as a list"""
        goblin = self.bot.get_emoji(902461392303587329)
        golem = self.bot.get_emoji(902461393146626048)
        human = self.bot.get_emoji(902461392311947284)
        kobold = self.bot.get_emoji(902461392139976714)
        skeleton = self.bot.get_emoji(902461392014180372)
        return [goblin, golem, human, kobold, skeleton]

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
        """
        Register your Neon Dungeon card you just got to the Skeleton Guard!
        """
        message = "Welcome to the Neon Dungeon, as the guard and keeper of this dungeon " \
                  "I will guide you through the registration process"
        own_embed = discord.Embed(
            title="Hi there, nice to meet you. I'm Baron Von Bones",
            description="First of all, Do you own a [Neon Dungeon](https://opensea.io/collection/neondungeon) character card?")
        own_embed.set_footer(text="Just like the image to the right ➡")
        own_embed.set_thumbnail(url="https://neondungeon.tech/wp-content/uploads/2021/10/4-726x1024.png")
        await ctx.message.add_reaction(emoji='✉')

        message = await ctx.author.send(message, embed=own_embed)
        user = ctx.author.dm_channel.recipient
        reactions = ['✅', '❌']
        for emoji in reactions:
            await message.add_reaction(emoji)

        def check(reaction, reacted_user):
            return reacted_user == user and reaction.emoji in reactions

        reaction, reacted_user = await self.bot.wait_for('reaction_add', check=check)
        await message.delete()
        # if they said that they don't own an NFT
        if reaction.emoji == reactions[1]:
            market_embed = discord.Embed(
                description="In that case, [visit the market 🏪](https://opensea.io/collection/neondungeon) first to pick a card!")
            await user.send(embed=market_embed)
        else:
            example_link = "https://opensea.io/assets/matic/" \
                           "0x2953399124f0cbb46d2cbacd8a89cf0599974963/" \
                           "71443629031568156881543435975776152234932282614143584443465170428761898745857"
            embed = discord.Embed(title="Cool! To prove to my masters that you own this card",
                                  description="I would need the link to this card on [Opensea](https://opensea.io/account)")
            embed.add_field(name="Example", value=example_link)
            await user.send(embed=embed)

            def check(check_message):
                return check_message.author == user

            wallet_address = None
            opensea_id = None
            while wallet_address is None and opensea_id is None:
                message = await self.bot.wait_for('message', check=check)
                link = urlparse(message.content)
                if link[0] == '':
                    await user.send("That isn't a valid link")

                elif link[1].lower() != 'opensea.io':
                    await user.send("I'm looking for a link from Opensea.io")

                elif len(link[2].split('/')) < 4:
                    await user.send("Yes, this is from Opensea, but it doesn't lead me to an NFT")

                elif link[2].split('/')[2] == '0x2953399124f0cbb46d2cbacd8a89cf0599974963':
                    await user.send("That one clearly isn't yours")

                elif message.content == example_link:
                    await user.send("You literally just copied my example, seriously?")

                else:
                    path = link[2].split('/')
                    wallet_address = path[3]
                    opensea_id = path[4]

            # Races
            race_reactions = self.get_race_emojis()

            message = "Cool! I can't wait to know your friend more, can I know your friend's race?\n" \
                      "(React to a choice down below ⬇)"
            message = await user.send(message)
            for emoji in race_reactions:
                await message.add_reaction(emoji)

            def check(reaction, reacted_user):
                return reacted_user == user and reaction.emoji in race_reactions and reaction.message == message

            reaction, reacted_user = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            await message.delete()
            with open("maps.json") as mapping:
                mapping = json.loads(mapping.read())["races"]
                emoji_index = race_reactions.index(reaction.emoji)
                race = mapping.index(race_reactions[emoji_index].name.lower())

            # Elements
            message = await user.send("I'll need to know what element you are as well\n"
                                      "(React to a choice down below ⬇)")
            element_emojis = {'🍃': "leaf", '🔥': "fire", '💧': "water"}

            for emoji in element_emojis:
                await message.add_reaction(emoji)

            def check(reaction, reacted_user):
                return reacted_user == user and str(reaction.emoji) in element_emojis and reaction.message == message

            reaction, reacted_user = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            await message.delete()
            with open("maps.json") as mapping:
                mapping = json.loads(mapping.read())["elements"]
                name = element_emojis[reaction.emoji]
                element = mapping.index(name)

            def dm_check(message):
                return message.channel == user.dm_channel

            # get Armor value
            await user.send(
                "Now, how tough is your character's armor? This should be at the **top left** of your card\n"
                "This is your character's armor")
            await asyncio.sleep(0.1)
            while True:
                armor = await self.bot.wait_for("message", check=dm_check, timeout=60)
                if armor.content.isdigit():
                    if 5 <= int(armor.content) <= 10:
                        break
                await user.send("I don't know how you rate armor strength but it's supposed to be from 5 to 10")

            # get Health value
            await user.send(
                "How much health does your character have? This should be at the **top right** of the card\n"
                "This is your character's health")

            while True:
                health = await self.bot.wait_for("message", check=dm_check, timeout=60)
                if health.content.isdigit():
                    if 80 <= int(health.content) <= 120:
                        break
                await user.send("I'm not sure if that's right, it should be around 80 - 120")

            # get Gem value
            await user.send(
                "And what quality gem was given to your character? This should be at the **bottom left** of the card\n"
                "This is your character's gem number")
            while True:
                gem = await self.bot.wait_for("message", check=dm_check, timeout=60)
                if gem.content.isdigit():
                    if 1 <= int(gem.content) <= 9:
                        break
                await user.send("I don't think I know this gem rating system, it should be on a scale of 1 - 9")

            await user.send("Look, I'd love to ask one by one, but can you just give me all of the rest of the stats? "
                            "These should be in the middle of the card\n"
                            "Send all your stats in the format `strength` `agility` `wisdom` `temper` `magic`\n"
                            "Ex: 52 91 10 27 40")
            await asyncio.sleep(0.5)
            stats = await self.bot.wait_for("message", check=dm_check, timeout=60)

            while True:
                try:
                    split = stats.content.split(" ")
                    for i in range(0, 4):
                        number = int(split[i])
                        if 1 > number > 100:
                            raise ValueError

                    await asyncio.sleep(0.1)
                    break
                except Exception:
                    await user.send("I don't think that's in the right format")
                    await asyncio.sleep(0.1)
                    stats = await self.bot.wait_for("message", timeout=60)
            await user.send("Alright thanks! I just need one last thing...\n"
                            "**What would you like to name your character?** (You can change the name again after registration)")
            sure = False
            while not sure:
                await asyncio.sleep(0.5)
                name = await self.bot.wait_for("message", timeout=60)
                message = await user.send(f"So your character's name is going to be **{name.content}**?")
                reactions = ['✅', '❌']
                for emoji in reactions:
                    await message.add_reaction(emoji)

                def check(reaction, reacted_user):
                    return reacted_user == user and reaction.emoji in reactions

                reaction, reacted_user = await self.bot.wait_for('reaction_add', check=check)
                await message.delete()
                # If sure then break out of loop
                if reaction.emoji == reactions[0]:
                    sure = True
                else:
                    await user.send("Then what name do you want your character to be?")

            self.cursor.execute("INSERT INTO users(user_id, wallet_address, daily) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                                (user.id, wallet_address, datetime.datetime.now()))
            self.cursor.execute("""
                            INSERT INTO 
                            cards(user_id, card_name, race, element, armor, health, gem, strength, agility, wisdom, temper, magic, opensea_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                            """,
                                (user.id, name.content, race, element, armor.content, health.content, gem.content,
                                 split[0], split[1], split[2], split[3], split[4], opensea_id))
            self.connection.commit()

            await user.send("Alright then, give me a second to sort out the paperwork and you should be able to start "
                            "battling in the **Neon Dungeon** in no time!\n"
                            "Use `challenge` to challenge someone to a battle!\n"
                            "And you can check your profile with `profile`! Have fun battling!")

    @commands.command()
    async def challenge(self, ctx, user: discord.User, wager: typing.Optional[int]):
        """
        Challenge someone to battle with you!
        Usage: challenge (@User to battle with) (Optional: Wager)
        Examples:
            Challenge @AlexanderQuartz
            Challenge @AlexanderQuartz 20
        """
        if user == ctx.author:
            await ctx.send("You can't challenge yourself silly!")
            return 1
        challenge_embed = discord.Embed(title=f"{ctx.author.display_name} Challenges you to a battle!",
                                        description="Do you accept?")

        if wager is not None:
            self.cursor.execute(f"select coins from users where user_id = {ctx.author.id}")
            author_coins = self.cursor.fetchone()[0]
            self.cursor.execute(f"select coins from users where user_id = {user.id}")
            user_coins = self.cursor.fetchone()[0]
            if user_coins < wager > author_coins:
                await ctx.send(f"One of you two doesn't have enough coins to wager {wager} coin(s)")
                return 0
            if wager > 0:
                challenge_embed.add_field(name="A wager has been proposed!",
                                          value=f"This will automatically deduct **{wager} "
                                                "coins** for both participants, until a winner has been found")
        else:
            wager = 0

        message = await ctx.send(embed=challenge_embed)
        reactions = ['✅', '❌']
        for emoji in reactions:
            await message.add_reaction(emoji)

        def check(reaction, reacted_user):
            return reacted_user == user and str(reaction.emoji) in reactions

        reaction, reacted_user = await self.bot.wait_for('reaction_add', check=check)

        self.cursor.execute(
            f"select * from cards where card_id in (select active_card from users where user_id = {ctx.author.id}) limit 1")
        author_card = self.cursor.fetchone()

        self.cursor.execute(
            f"select * from cards where card_id in (select active_card from users where user_id = {user.id}) limit 1")
        user_card = self.cursor.fetchone()

        if reaction.emoji == reactions[1]:
            await ctx.send("Challenge declined")

        elif not user_card or not author_card:

            if not user_card and not author_card:
                await ctx.send(
                    f"{user.mention} and {ctx.author.mention}, both of you haven't set a card to be active yet! Use `.setactive` to set an active card!")
            elif not user_card:
                await ctx.send(f"{user.mention}, you haven't set a card to be active yet! Use `.setactive` to set an active card!")
            elif not author_card:
                await ctx.send(f"{ctx.author.mention}, you haven't set a card to be active yet! Use `.setactive` to set an active card!")

        else:
            await ctx.send("Challenge accepted!")
            await message.delete()



            # Checks if has set an active card or not
            if not user_card or not author_card:
                await ctx.send("You haven't set a card to be active yet! Use `.setactive` to set an active card!")

            author_gem = author_card[7]
            user_gem = user_card[7]
            if author_gem > user_gem:
                # Swap the values
                user1_card, user2_card = author_card, user_card
                user1, user2 = ctx.author, user
            else:
                user1_card, user2_card = user_card, author_card
                user1, user2 = user, ctx.author

            await ctx.send(f"{user1.mention} has the higher gem number, you go first!\n"
                           f"Use `.attack` to tell me how much damage you took\n"
                           f"and use `.end` to end the battle and I'll calculate who won!")
            self.cursor.execute(f"""insert into 
                                battles(
                                user1_id, user1_card_id, user1_health, user1_armor_used, 
                                user2_id, user2_card_id, user2_health, user2_armor_used,
                                round, wager) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                                (user1.id, user1_card[0], user1_card[6], False, user2.id, user2_card[0],
                                 user2_card[6], False, 0, wager * 2))
            self.cursor.execute(
                f"update users set coins = coins - {wager} where user_id = {user1.id} or user_id = {user2.id}")
            self.connection.commit()

    @commands.command()
    async def profile(self, ctx):
        """
        Shows your profile and active character
        """
        profile = discord.Embed(title=f"{ctx.author.display_name}'s Profile",
                                description="Followed by a list of items owned!",
                                color=discord.Color.gold(),
                                timestamp=datetime.datetime.now(datetime.timezone.utc))
        profile.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        self.cursor.execute(f"Select card_name, race from cards where user_id = {ctx.author.id}")
        cards_owned = self.cursor.fetchall()
        if cards_owned:
            self.cursor.execute(
                f"select card_name, race from cards where card_id in (select active_card from users where user_id = {ctx.author.id}) limit 1")
            active_card = self.cursor.fetchone()
            if active_card:
                with open("maps.json") as mapping:
                    race = json.loads(mapping.read())["races"][active_card[1]]
                profile.add_field(name="Active character", value=active_card[0], inline=True)
                profile.add_field(name="Race", value=race.capitalize(), inline=True)

                self.cursor.execute(f"select wins, coins from users where user_id = {ctx.author.id}")
                data = self.cursor.fetchone()
                profile.add_field(name="Total Wins", value=data[0], inline=False)
                profile.add_field(name="Coins", value=data[1], inline=True)

                profile.add_field(name="Cards Owned", value=str(len(cards_owned)))
                await ctx.send(embed=profile)
            else:
                await ctx.send("You haven't set a card to be active yet! Use `.setactive` to set an active card!")
        else:
            await ctx.send("You don't have any cards registered yet!\n"
                           "Use `.register` to register your card to the Neon Dungeon")

    @commands.command()
    async def end(self, ctx):
        """
        End an ongoing battle and see who won!
        """
        self.cursor.execute(f"""select user1_id, user2_id, user1_health, user2_health, round, wager, user1_card_id, user2_card_id from battles
                                where user1_id = {ctx.author.id} or user2_id = {ctx.author.id}""")
        data = self.cursor.fetchone()
        if data:
            # if author is user 1
            if data[0] == ctx.author.id:
                other_user = self.bot.get_user(data[1])
                other_user_health = data[3]
                other_user_card = data[7]
                author_health = data[2]
                author_card = data[6]
            # if author is user 2
            else:
                other_user = self.bot.get_user(data[0])
                other_user_health = data[2]
                other_user_card = data[6]
                author_health = data[3]
                author_card = data[7]
            round_no = data[4]
            wager = data[5]

            embed = discord.Embed(title=f"{ctx.author.display_name} wants to end the battle with you",
                                  description=f"{other_user.display_name} do you accept to end this battle?")
            message = await ctx.send(embed=embed)
            reactions = ['✅', '❌']
            for emoji in reactions:
                await message.add_reaction(emoji)

            def check(reaction, reacted_user):
                return reacted_user == other_user and str(reaction.emoji) in reactions

            reaction, reacted_user = await self.bot.wait_for('reaction_add', check=check)
            await message.delete()
            if reaction.emoji == reactions[0]:
                await ctx.send("The winner is...")
                await asyncio.sleep(1)
                if author_health > other_user_health:
                    winner = ctx.author
                elif other_user_health > author_health:
                    winner = other_user
                else:
                    self.cursor.execute(f"select element from cards where card_id = {author_card}")
                    author_element = self.cursor.fetchone()
                    self.cursor.execute(f"select element from cards where card_id = {other_user_card}")
                    other_user_element = self.cursor.fetchone()

                    # covers 1-1 2-2 3-3
                    if author_element == other_user_element:
                        winner = None
                    # covers 1-2 1-3 2-3
                    elif author_element < other_user_element:
                        winner = ctx.author
                        if author_element == 1 and other_user_element == 3:
                            winner = other_user
                    # covers 2-1 3-1 3-2
                    elif author_element > other_user_element:
                        winner = other_user
                        if author_element == 3 and other_user_element == 1:
                            winner = ctx.author
                    else:
                        winner = None

                if winner is not None:
                    await ctx.send(f"{winner.mention}!!")
                    await ctx.send("you have obtained 25 coins!")
                    self.cursor.execute(f"UPDATE users SET wins = wins + 1 where user_id = {winner.id}")
                    if winner.id == ctx.author.id:
                        self.cursor.execute(f"UPDATE users SET loses = loses + 1 where user_id = {other_user.id}")
                    else:
                        self.cursor.execute(f"UPDATE users SET loses = loses + 1 where user_id = {ctx.author.id}")

                    self.cursor.execute(f"UPDATE users SET coins = coins + 25 where user_id = {winner.id}")
                else:
                    await ctx.send("There is no winner, it's a draw")
                if wager > 0:
                    await ctx.send(f"A wager was given in this battle! {winner.mention} gets {wager} extra coins!")
                    self.cursor.execute(f"UPDATE users SET coins = coins + {wager} where user_id = {winner.id}")

                self.cursor.execute(
                    f"DELETE FROM battles where user1_id = {ctx.author.id} or user2_id = {ctx.author.id}")
                self.connection.commit()

                if random.randint(1, 10) == 1:
                    await asyncio.sleep(1)
                    responses = open("winner.txt").readlines()
                    response = responses[random.randrange(0, len(responses))]
                    await ctx.send(response)

        else:
            await ctx.send("You don't have any ongoing battles at the moment! challenge someone to a battle right now "
                           "with `challenge` `@user`")

    @commands.command()
    async def attack(self, ctx, damage: int):
        """
        Register the amount of damage you dealt to an enemy
        """
        self.cursor.execute(f"""select user1_id, user2_id, user1_health, user2_health, round, wager, user1_card_id, user2_card_id from battles
                                where user1_id = {ctx.author.id} or user2_id = {ctx.author.id}""")
        data = self.cursor.fetchone()
        if data:
            if data[0] == ctx.author.id:
                other_user = self.bot.get_user(data[1])
            else:
                other_user = self.bot.get_user(data[0])
            embed = discord.Embed(title="Damage taken confirmation",
                                  description=f"Did you take {damage} damage?",
                                  colour=discord.Colour.red())
            message = await ctx.send(embed=embed)
            reactions = ['✅', '❌']
            for emoji in reactions:
                await message.add_reaction(emoji)

            def check(reaction, reacted_user):
                return reacted_user == other_user and str(reaction.emoji) in reactions

            reaction, reacted_user = await self.bot.wait_for('reaction_add', check=check)
            await message.delete()
            if reaction.emoji == reactions[0]:
                if data[0] == ctx.author.id:
                    other_user_health = data[3]
                    other_user_card = data[7]
                    author_health = data[2]
                    author_card = data[6]
                    self.cursor.execute(f"UPDATE battles SET user2_health = user2_health - {damage} "
                                        f"where user1_id = {ctx.author.id} or user2_id = {ctx.author.id}")

                else:
                    other_user_health = data[2]
                    other_user_card = data[6]
                    author_health = data[3]
                    author_card = data[7]
                    self.cursor.execute(f"UPDATE battles SET user1_health = user1_health - {damage} "
                                        f"where user1_id = {ctx.author.id} or user2_id = {ctx.author.id}")
                round_no = data[4]
                wager = data[5]

                resulting_health = other_user_health - damage
                if resulting_health <= 0:
                    await ctx.send("Final Blow!! Your health has reached 0")
                    await ctx.send(f"{ctx.author.mention} is the winner!")
                    await ctx.send("you have obtained 25 coins!")
                    self.cursor.execute(f"UPDATE users SET wins = wins + 1 where user_id = {ctx.author.id}")
                    self.cursor.execute(f"UPDATE users SET loses = loses + 1 where user_id = {other_user.id}")
                    self.cursor.execute(f"UPDATE users SET coins = coins + 25 where user_id = {ctx.author.id}")
                    self.cursor.execute(
                        f"DELETE FROM battles where  user1_id = {ctx.author.id} or user2_id = {ctx.author.id}")
                    if wager > 0:
                        await ctx.send(f"A wager was given in this battle! {ctx.author.mention} gets {wager} coins!")
                        self.cursor.execute(f"UPDATE users SET coins = coins + {wager} where user_id = {ctx.author.id}")
                else:
                    await ctx.send(f"{other_user.mention} has taken {damage} damage, your health is now {resulting_health}")
                self.connection.commit()
        else:
            await ctx.send("You don't have any ongoing battles at the moment! challenge someone to a battle right now "
                           "with `challenge` `@user`")

    @commands.command()
    async def setactive(self, ctx):
        """Selects an active card to use for battle"""

        self.cursor.execute(f"Select * from cards where user_id = {ctx.author.id}")
        user_cards = self.cursor.fetchall()
        while len(user_cards) > 1:
            embed = discord.Embed(title="⚔ Please select the card you would like to use for battles ⚔",
                                  description="Type in a number to the corresponding card you'd like to set as active")
            card_ids = []
            for number, card in enumerate(user_cards):
                card_name = card[2]
                card_id = card[0]
                embed.add_field(name=card_name, value=str(number + 1))
                card_ids.append(card_id)

            def check(message):
                return message.author == ctx.author

            await ctx.send(embed=embed)
            reply = await self.bot.wait_for("message", timeout=60, check=check)

            while True:
                if not reply.content.isdigit():
                    await ctx.send("That isn't a number, please input a valid number")
                elif int(reply.content) > len(card_ids):
                    await ctx.send(f"You only have {len(card_ids)}, please pick a number from the list provided")
                else:
                    break
                reply = await self.bot.wait_for("message", timeout=60, check=check)

            reply = int(reply.content) - 1
            selected_card_name = user_cards[reply][2]
            selected_card_id = user_cards[reply][0]
            confirmation = discord.Embed(title="Confirm Selection?",
                                         description=f"`{selected_card_name}` will be used for battles",
                                         colour=discord.Colour.green())

            confirm_msg = await ctx.send(embed=confirmation)
            reactions = ['✅', '❌']
            for emoji in reactions:
                await confirm_msg.add_reaction(emoji)

            def check(reaction, reacted_user):
                return reacted_user == ctx.author and str(reaction.emoji) in reactions

            reaction, reacted_user = await self.bot.wait_for('reaction_add', check=check)
            await confirm_msg.delete()

            if reaction.emoji == reactions[0]:
                self.cursor.execute(
                    f"update users set active_card = {selected_card_id} where user_id = {ctx.author.id}")
                self.connection.commit()
                await ctx.send("Selection Confirmed!")
                break
        else:
            if len(user_cards) == 0:
                await ctx.send(f"{ctx.author.mention}, you don't have any cards registered yet! "
                               "Use `.register` and I'll show you how")
            else:
                user_card = user_cards[0]
                self.cursor.execute(f"UPDATE users SET active_card = {user_card[0]} WHERE user_id = {ctx.author.id}")
                self.connection.commit()
                await ctx.send("I have set your one card as the active card you are using")

    @commands.command()
    async def daily(self, ctx):
        """Claim your daily coins for the day!"""
        self.cursor.execute(f"SELECT daily FROM users WHERE user_id = {ctx.author.id}")
        daily = self.cursor.fetchone()
        if daily:
            today = datetime.datetime.now()
            daily_date = daily[0]
            one_day = datetime.timedelta(days=1)
            if today >= daily_date:
                self.cursor.execute(f"UPDATE users set coins = coins + 5 WHERE user_id = {ctx.author.id}")
                self.cursor.execute(f"UPDATE users set streak = streak + 1 WHERE user_id = {ctx.author.id}")
                self.cursor.execute("UPDATE users set daily = %s WHERE user_id = %s", (today + one_day, ctx.author.id))
                self.connection.commit()

                self.cursor.execute(f"select streak from users where user_id = {ctx.author.id}")
                streak = self.cursor.fetchone()[0]
                await ctx.send(f"Daily claimed! +5 Coins!!\n"
                               f"you are currently on a {streak} day streak!!")

            else:
                timeleft = daily_date - today
                await ctx.send(f"You still have **{timeleft.seconds} seconds** until your next daily!")
                if timeleft.seconds >= 3600:
                    await asyncio.sleep(2)
                    await ctx.send("I'm sorry, I don't know how to convert seconds into hours, I'm a skeleton okay")
        else:
            await ctx.send(f"{ctx.author.mention}, you don't have any cards registered yet! "
                           "Use `.register` and I'll show you how")

    @commands.command()
    async def stats(self, ctx):
        """Check your active card's stats"""

        self.cursor.execute(
            f"select race, element, armor, health, gem, strength, agility, wisdom, temper, magic, card_name "
            f"from cards where card_id in (select active_card from users where user_id = %s) limit 1",
            (ctx.author.id, ))
        active_card = self.cursor.fetchone()
        if active_card:
            profile = discord.Embed(title=f"{active_card[10]}'s Stats",
                                    color=discord.Color.gold(),
                                    timestamp=datetime.datetime.now(datetime.timezone.utc))
            profile.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

            with open("maps.json") as mapping:
                json_data = json.loads(mapping.read())
                race = json_data["races"][active_card[0]]
                element = json_data["elements"][active_card[1]]
            profile.add_field(name="Race", value=race.capitalize())
            profile.add_field(name="Element", value=element.capitalize())
            profile.add_field(name="Armor", value=active_card[2])
            profile.add_field(name="Health", value=active_card[3])
            profile.add_field(name="Gem Quality", value=active_card[4])

            profile.add_field(name="‎", value="‎", inline=False)

            profile.add_field(name="Strength", value=active_card[5])
            profile.add_field(name="Agility", value=active_card[6])
            profile.add_field(name="Wisdom", value=active_card[7])
            profile.add_field(name="Temper", value=active_card[8])
            profile.add_field(name="Magic", value=active_card[9])

            await ctx.send(embed=profile)
        else:
            await ctx.send("You haven't set a card to be active yet! Use `.setactive` to set an active card!")


def setup(bot):
    bot.add_cog(Game(bot))
