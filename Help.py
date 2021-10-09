import discord
from discord.ext import commands
import os


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(title='List of Commands',
                              description='Want to know more about Neon Dungeons?\n'
                                          'Go to the [Neon Dungeons Website](https://neondungeon.tech/)',
                              colour=ctx.author.colour)
        cogs = dict(self.bot.cogs)
        # when someone DMs the help command
        if isinstance(ctx.author, discord.User):
            manage_roles = False
        else:
            manage_roles = ctx.author.guild_permissions.manage_roles

        for cog in cogs:
            command_list = ''
            for command in self.bot.cogs[cog].get_commands():
                if not command.hidden and command.help is not None:
                    command_list += f'`{command.name}`\n {command.help}\n\n'
            if command_list != '':
                cog_name = self.bot.cogs[cog].qualified_name

                cog_emojis = {"Fun": "🎉",
                              "Blender52": "📚",
                              "B52": "⚙"}
                try:
                    emoji = cog_emojis[cog_name]
                except Exception as e:
                    print(e)
                    emoji = ""
                embed.add_field(name=f"{emoji} {cog_name}", value=command_list, inline=False)

        await ctx.message.add_reaction(emoji='✉')
        await ctx.message.author.send(embed=embed)

    @commands.command()
    async def alias(self, ctx, cmd_name):
        command = self.bot.get_command(cmd_name)

        if command is not None:
            aliases = ''
            for i in command.aliases:
                aliases += f'{i}, '

            if aliases != '':
                await ctx.send(f"Aliases: {aliases[:-2]}")
            else:
                await ctx.send("Command has no aliases")
        else:
            await ctx.send("Command not found")


def setup(bot):
    bot.add_cog(Help(bot))
