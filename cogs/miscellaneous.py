import random
import discord
import os, sys, json
from discord.ext import commands

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
import quizdata

os.chdir(os.getcwd())

copypastas, copypastainfo = quizdata.copypastas, quizdata.copypastainfo

#embed of list of pastas to display
pastas = []
for key, value in copypastainfo.items():
    pastas.append(key + "   ––––	" + value)
pastalist = discord.Embed(colour=0x9b59b6)
pastalist.add_field(name="Copypastas:", value="\n".join(pastas), inline=False)

jsondir = os.path.dirname(os.path.dirname(os.getcwd())) + "//jsonfiles"

def open_json(jsonfile):
	with open(jsondir + '//' + jsonfile, "r") as fp:
		return json.load(fp)	#openfunc for jsonfiles

def save_json(jsonfile, name):	#savefunc for jsonfiles
	with open(jsondir + '//' + jsonfile, "w") as fp:
		json.dump(name, fp)

def strip_str(text):		#function to remove punctuations, spaces and "the" from string and make it lowercase,
	punctuations = ''' !-;:`'"\,/_?'''			# in order to compare bot answers and user replies
	text2 = ""
	text.replace("the ", "")
	for char in text:
		if char not in punctuations:
			text2 = text2 + char
	return text2.lower()

class Miscellaneous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief = "See the top 10 cheese collectors.", aliases = ["board"])
    async def cheeseboard(self, ctx):
        users = open_json("users.json")
        onlycheese = {k: v["cheese"] for k, v in users.items()}         #create a dict of user ids and their cheese
        sort = {k: v for k, v in sorted(onlycheese.items(), key=lambda item: item[1], reverse=True)}      #sort the dictionary according to cheese amounts
        sortkeys, sortvalues = list(sort.keys()), list(sort.values())       #obtain lists of the keys and values for later use
        basetext = "Collector:                         Cheese amount:\n"
        for n in range(0, 10):
            user = ctx.guild.get_member(int(sortkeys[n]))
            if type(user) == discord.Member:        #if user is in the server it will display the name
                multiplier = 44 - len(user.display_name)
                if n == 9:          #if it's the 10th user it will be less indented to be in line with other users
                    basetext = basetext + str(n+1) + ")" + user.display_name + " "*(multiplier-1) + str(sortvalues[n])
                else:
                    basetext = basetext + str(n+1) + ")" + user.display_name + " "*multiplier + str(sortvalues[n]) + "\n"
            else:           #otherwise it will just say "hidden" instead
                if n == 9:        #if it's the 10th user it will be less indented to be in line with other users
                    basetext = basetext + str(n+1) + ")[Hidden User]" + " "*30 + str(sortvalues[n])
                else:
                    basetext = basetext + str(n+1) + ")[Hidden User]" + " "*31 + str(sortvalues[n]) + "\n"
        await ctx.send(f"```{basetext}```")

    @commands.command(brief = "Get a copy of a DotA copypasta.", aliases = ["pasta"])
    async def copypasta(self, ctx, pasta):
        if strip_str(pasta) in list(copypastas.keys()):
            await ctx.send(copypastas[strip_str(pasta)])
        else:
            await ctx.send("That is not one of the available copypastas: ", embed=pastalist)

    @commands.command()
    async def hohoohahaa(self, ctx):
        await ctx.send(file=discord.File('snoper.png'))

    @commands.command()
    async def newpatch(self, ctx):
        rng = open_json("rngfix.json")
        id = str(ctx.guild.id)
        if id not in rng.keys():
            rng[id] = {"questnumbers":[], "shopkeepnumbers":[], "iconquiznumbers":[], "audioquiznumbers":[], "scramblenumbers":[], "vacuumcd":16}
        rng[id]["vacuumcd"] += random.randint(1, 3)
        await ctx.send(f"""Vacuum cooldown has been increased, it is now **{rng[id]["vacuumcd"]}** seconds long.""")
        save_json("rngfix.json", rng)

    @commands.command()
    async def missedhook(self, ctx):
        await ctx.send(f"""You missed your hook "because" the ping is {round(self.bot.latency * 1000)}ms""")

    @copypasta.error
    async def copypastaerror(self, ctx, error):
        if isinstance (error, commands.MissingRequiredArgument):
            await ctx.send("You need to specify which copypasta you want like so: 322 copypasta <pasta> out of one of these copypastas: ", embed=pastalist)

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            pass
        else:
            raise error

async def setup(bot):
    await bot.add_cog(Miscellaneous(bot))
