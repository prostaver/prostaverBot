from discord import Intents
from discord.ext import commands

from Cogs import PlayerCog

cogs = [PlayerCog]

client = commands.Bot(command_prefix=".", intents=Intents.all())

for i in range(len(cogs)):
    cogs[i].setup(client)


@client.event
async def on_ready():
    print(f"{client.user.name} is ready.")


@client.command()
async def ping(ctx):
    await ctx.send("Pong!!")


client.run("")
