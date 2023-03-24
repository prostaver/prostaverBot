import asyncio
import discord
from discord.ext import commands
import pafy
import youtube_dl

class Player(commands.Cog):
    def __init__(self, client):
        self.client = client 
        self.song_queue = {}

        self.setup()

    def setup(self):
        #for guild in self.client.guilds:
        self.song_queue["test"] = []

    async def check_queue(self, ctx):
        queue_length = len(self.song_queue["test"])
        if queue_length > 0:
            self.song_queue["test"].pop(0)
            # if((queue_length - 1) > 0):
            await self.play_song(ctx, self.song_queue["test"][0])

    async def search_song(self, song, get_url=False):
        info = await self.client.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL({"format" : "bestaudio", "quiet" : True})
                .extract_info(f"ytsearch{1}:{song}", download=False, ie_key="YoutubeSearch"))
        if len(info["entries"]) == 0: return None

        song_info = {}
        for entry in info["entries"]:
            song_info = {"song_title":entry["title"], "song_url":entry["webpage_url"]}
        return song_info

    async def play_song(self, ctx, song_info):
        url = pafy.new(song_info["song_url"]).getbestaudio().url
        ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url)), after=lambda error: self.client.loop.create_task(self.check_queue(ctx)))
        ctx.voice_client.source.volume = 0.5

    @commands.command(brief="Make this bot join the channel the command sender is currently in.")
    async def join(self, ctx):
        if ctx.author.voice is None:
            return await ctx.send("You are not connected to a voice channel, please connect to the channel you want the bot to join.")

        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()

        await ctx.author.voice.channel.connect()

    @commands.command(brief="Leave the voi")
    async def leave(self, ctx):
        if ctx.voice_client is not None:
            self.song_queue["test"] = []
            return await ctx.voice_client.disconnect()

        await ctx.send("I am not connected to a voice channel.")

    @commands.command(brief="Make the bot leave the voice channel")
    async def play(self, ctx, *, song=None):
        if song is None:
            return await ctx.send("You must include a song to play.")

        if ctx.voice_client is None:
            await self.join(ctx)

        # handle song where song isn't url
        if not ("youtube.com/watch?" in song or "https://youtu.be/" in song):
            await ctx.send("Searching for song, this may take a few seconds.")

            result = await self.search_song(song, get_url=True)

            if result is None:
                return await ctx.send("Sorry, I could not find the given song, try using my search command.")

            song_info = result

        # print("voice client source")
        # print(ctx.voice_client.source)
        # print("not song queue")
        # print(not self.song_queue["test"])
        # print(self.song_queue["test"])
        if ctx.voice_client.source is not None:
            print(self.song_queue["test"])
            queue_len = len(self.song_queue["test"])
            print(queue_len)

            if queue_len < 10:
                self.song_queue["test"].append(song_info)
                return await ctx.send(f"I am currently playing a song, this song has been added to the queue at position: {queue_len+1}.")

            else:
                return await ctx.send("Sorry, I can only queue up to 10 songs, please wait for the current song to finish.")
        else:
            self.song_queue["test"].append(song_info)

        await self.play_song(ctx, song_info)
        await ctx.send("Now playing: "+song_info["song_url"])

    @commands.command(brief="Shows the songs currently queued in the playlist")
    async def queue(self, ctx): # display the current guilds queue
        if len(self.song_queue["test"]) == 0:
            return await ctx.send("There are currently no songs in the queue.")

        embed = discord.Embed(title="Song Queue", description="", colour=discord.Colour.dark_gold())
        i = 1
        for song_info in self.song_queue["test"]:
            title = song_info["song_title"]
            url = song_info["song_url"]
            embed.add_field(name=f"{i}) {title}", value=url, inline=False)

            i += 1

        embed.set_footer(text="Thanks for using me!")
        await ctx.send(embed=embed)

    @commands.command(brief="Skips the current song", description="Creates a poll to vote whether to skip the current song or not.")
    async def skip(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("I am not playing any song.")

        if ctx.author.voice is None:
            return await ctx.send("You are not connected to any voice channel.")

        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("I am not currently playing any songs for you.")

        poll = discord.Embed(title=f"Vote to Skip Song by - {ctx.author.name}#{ctx.author.discriminator}",
                description="**80% of the voice channel must vote to skip for it to pass.**", colour=discord.Colour.blue())
        poll.add_field(name="Skip", value=":white_check_mark:")
        poll.add_field(name="Stay", value=":no_entry_sign:")
        poll.set_footer(text="Voting ends in 15 seconds.")

        poll_msg = await ctx.send(embed=poll) # only returns temporary message, we need to get the cached message to get the reactions
        poll_id = poll_msg.id

        await poll_msg.add_reaction(u"\u2705") # yes
        await poll_msg.add_reaction(u"\U0001F6AB") # no
        
        await asyncio.sleep(15) # 15 seconds to vote

        poll_msg = await ctx.channel.fetch_message(poll_id)
        
        votes = {u"\u2705": 0, u"\U0001F6AB": 0}
        reacted = []

        for reaction in poll_msg.reactions:
            if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
                async for user in reaction.users():
                    if user.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted and not user.bot:
                        votes[reaction.emoji] += 1

                        reacted.append(user.id)

        skip = False

        if votes[u"\u2705"] > 0:
            if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (votes[u"\u2705"] + votes[u"\U0001F6AB"]) > 0.79: # 80% or higher
                skip = True
                embed = discord.Embed(title="Skip Successful", description="***Voting to skip the current song was succesful, skipping now.***", colour=discord.Colour.green())

        if not skip:
            embed = discord.Embed(title="Skip Failed", description="*Voting to skip the current song has failed.*\n\n**Voting failed, the vote requires at least 80% of the members to skip.**", colour=discord.Colour.red())

        embed.set_footer(text="Voting has ended.")

        await poll_msg.clear_reactions()
        await poll_msg.edit(embed=embed)

        if skip:
            ctx.voice_client.stop()

    @commands.command(brief="Pauses the current song.")
    async def pause(self, ctx):
        if ctx.voice_client.is_paused():
            return await ctx.send("I am already paused.")

        ctx.voice_client.pause()
        await ctx.send("The current song has been paused.")

    @commands.command(brief="Resumes the paused song.")
    async def resume(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("I am not connected to a voice channel.")

        if not ctx.voice_client.is_paused():
            return await ctx.send("I am already playing a song.")
        
        ctx.voice_client.resume()
        await ctx.send("The current song has been resumed.")

    @commands.command(brief="Stops the audio player.")
    async def stop(self, ctx):
        if not ctx.voice_client.is_playing():
            return await ctx.send("Audio player is not currently playing.")

        self.song_queue["test"] = []
        ctx.voice_client.stop()
        return await ctx.send("Audio player stopped.")

def setup(client):
    client.add_cog(Player(client))
    print("Cog Added")