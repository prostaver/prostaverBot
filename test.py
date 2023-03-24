class Player():
    def __init__(self):
        self.song_queue = {}

        self.setup()

    def setup(self):
        self.song_queue[5] = []

    def check_queue(self):
        if len(self.song_queue[5]) > 0:
            print("here")
            print(self.song_queue[5])
        #await self.play_song(ctx, self.song_queue[ctx.guild.id][0])
        #self.song_queue[ctx.guild.id].pop(0)

player = Player()
print(len(player.song_queue[5]))
player.song_queue[5].append("new song")

player.check_queue()
print(len(player.song_queue[5]))
player.song_queue[5].pop(0)
player.check_queue()
print(len(player.song_queue[5]))