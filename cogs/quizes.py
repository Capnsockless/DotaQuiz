import random
import discord
import json, time, os, asyncio
from fuzzywuzzy import fuzz
from mutagen.mp3 import MP3
from discord.ext import commands

os.chdir(os.getcwd())

#importing all quizes from quizdata
import quizdata
questlist, shopkeeplist, iconquizlist = quizdata.questlist, quizdata.shopkeeplist, quizdata.iconquizlist
#questdict is for quiz, blitz, duel, freeforall, shopkeepdict is for shopquiz, iconquizdict - iconquiz, audioquiz - audioquiz, scramblelist - scramble
audioquizdict, scramblelist = quizdata.audioquizdict, quizdata.scramblelist
#getting their lengths for the indicies, hence the -1
questlen, shopkeeplen, iconquizlen, audioquizlen, scramblelen = len(questlist)-1, len(shopkeeplist)-1, len(iconquizlist)-1, len(audioquizdict)-1, len(scramblelist)-1
#getting all of their keys and values as seperate lists
audioquizkeys, audioquizvalues = list(audioquizdict.keys()), list(audioquizdict.values())

#for shopquiz and simpleiconquiz
ingredients, iconnames, alphabet = quizdata.ingredients, quizdata.iconnames, quizdata.alphabet
#Prize percentages for 322 freeforall
prizeperc = {0:0.6, 1:0.2, 2:0.1, 3:0.05, 4:0.05}

jsondir = os.path.dirname(os.getcwd()) + 'jsonfiles'

def open_json(jsonfile):
	with open(jsondir + '//' + jsonfile, "r") as fp:
		return json.load(fp)	#openfunc for jsonfiles

def save_json(jsonfile, name):	#savefunc for jsonfiles
	with open(jsondir + '//' + jsonfile, "w") as fp:
		json.dump(name, fp)

def strip_str(text):		#function to remove punctuations, spaces and "the" from string and make it lowercase,
	punctuations = ''' !-;:`'".,/_?'''			# in order to compare bot answers and user replies
	text2 = ""
	for char in text.lower().replace("the ", ""):
		if char not in punctuations:
			text2 = text2 + char
	return text2

class Player():
	def __init__(self, author, ctx):
		self.server, self.channel, self.author = ctx.guild, ctx.channel, author
		self.users = open_json("users.json")
		self.rng = open_json("rngfix.json")
		id = str(self.author.id)
		if id not in self.users.keys():
			self.users[id] = {"gold":10, "items":[], "cheese":0}
			save_json("users.json", self.users)
		serv_id = str(self.server.id)
		if serv_id not in self.rng.keys():
			self.rng[serv_id] = {"questnumbers":[], "shopkeepnumbers":[], "iconquiznumbers":[], "audioquiznumbers":[], "scramblenumbers":[], "vacuumcd":16}
			save_json("rngfix.json", self.rng)
		try:
			self.inventory = self.users[str(author.id)]["items"]
		except KeyError:
			self.inventory = []

		#Items:
		self.linkens = (4600 in self.inventory)
		self.MKB = (4852 in self.inventory)
		self.shiva = (4850 in self.inventory)
		self.armlet = (2476 in self.inventory)
		self.midas = (2200 in self.inventory)
		self.aegis = (8000 in self.inventory)
		self.pirate_hat = (6500 in self.inventory)
		self.necronomicon = (4550 in self.inventory)
		self.aeon_disk = (3100 in self.inventory)

	def unique_int_randomizer(self, length, listkey):		#player.unique_int_randomizer used in par with the rngfix.json file to avoid repeating numbers(questions)
		serv_id = str(self.server.id)
		numlist = self.rng[serv_id][listkey]
		if len(numlist) > length*7/8:			#if amount of numbers surpass 7/8ths of the total amount delete a chunk of the numbers at the start
			del numlist[:round(length/7)]

		n = random.randint(0, length)		#starter number
		while n in numlist or n >= length:
			n = random.randint(0, length)
			for i in range(15):		#Probe through next 15 numbers, if still not found, rerandom
				if n not in numlist:		#get a number that isn't already used and append it to the list of numbers in use
					break
				n += 1
		#update the json file and return the valid number
		numlist.append(n)
		self.rng[serv_id][listkey] = numlist		#convert list back to string list
		save_json("rngfix.json", self.rng)
		return n

	def add_gold(self, newgold):		#add gold to users
		id = str(self.author.id)
		multiplier = 1 + 0.2*self.midas + 0.05*self.armlet
		newgold *= multiplier
		self.users[id]["gold"] = self.users[id]["gold"] + round(newgold)
		save_json("users.json", self.users)
		return round(newgold)

	def set_duration(self, duration):				#Set duration for quiz commands(30% more time if shiva is held)
		multiplier = 1 + 0.3*self.shiva - 0.1*self.armlet
		duration *= multiplier
		return round(duration)

	def set_lives(self, lives):				#Set amount of lives(+1 if the user has aegis)
		return lives + self.aegis

	def set_plunder(self, plunder):		#Increase gold if user has pirate hat(used for duel)
		return plunder + 10000*self.pirate_hat

	def set_necro(self, nquestions):		#Increase amount of questions if user has necronomicon(used for freeforall)
		return nquestions + self.necronomicon*10

	def clutched(self, ncorrectanswsinarow):		#linkens saves one and aeon disk halves the loss
		if self.linkens:
			output = ncorrectanswsinarow
			self.saves -= 1
		elif self.aeon_disk:
			output = round(ncorrectanswsinarow / 2)
		else:
			output = 0
		return output

class Quizes(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(brief = "A single DotA related question for a bit of gold.", aliases = ["q"])
	@commands.cooldown(1, 7, commands.BucketType.user)
	async def quiz(self, ctx):
		player = Player(ctx.author, ctx)
		questn = player.unique_int_randomizer(questlen, "questnumbers")			#Random number to give a random question
		questobj = questlist[questn]
		question = questobj.get_question()
		if questobj.questionType == 2:			#if the question comes with an image
			await ctx.send(f"**```{question[0]}```**", file=discord.File(f"./quizimages/{question[1]}"))
		else:											#for normal string questions
			await ctx.send(f"**```{question}```**")
		def check(m):
			return m.channel == player.channel and m.author == player.author		#checks if the reply came from the same person in the same channel
		try:
			msg = await self.bot.wait_for("message", check=check, timeout=player.set_duration(22))
		except asyncio.TimeoutError:		#If too late
			await ctx.send(f"**{quizdata.get_answ('L')}** The correct answer was ``{questobj.get_answer()}``")
		else:
			if questobj.check_answer(msg.content, player.MKB):
				g = player.add_gold(24)
				await ctx.send(f"**{quizdata.get_answ('R')}** you got ``{g}`` gold.")
			else:
				straddon = 'The correct answer was'
				if questobj.answerType != 1:
					straddon = 'One of the possible correct answer was'
				await ctx.send(f"**{quizdata.get_answ('W')}** {straddon} ``{questobj.get_answer()}``")

	@commands.command(brief = "Recognize hero names among scrambled letters.", aliases = ["shuffle", "mix"])
	@commands.cooldown(1, 8, commands.BucketType.user)
	async def scramble(self, ctx):
		player = Player(ctx.author, ctx)
		scramblen = player.unique_int_randomizer(scramblelen, "scramblenumbers")			#Random number to give a random question
		scrambleobj = scramblelist[scramblen]
		correctansw = scrambleobj.get_word()			#the correct answer
		await ctx.send(f"**``Unscramble this name:``**\n{scrambleobj.get_scramble()}")
		def check(m):
			return m.channel == player.channel and m.author == player.author		#checks if the reply came from the same person in the same channel
		try:
			msg = await self.bot.wait_for("message", check=check, timeout=player.set_duration(25))
		except asyncio.TimeoutError:		#If too late
			await ctx.send(f"**{quizdata.get_answ('L')}** The correct answer was ``{correctansw}``")
		else:
			if scrambleobj.check_answer(msg.content, player.MKB):
				g = player.add_gold(scrambleobj.value)
				await ctx.send(f"**{quizdata.get_answ('R')}** you got ``{g}`` gold.")
			else:
				await ctx.send(f"**{quizdata.get_answ('W')}** The correct answer was ``{correctansw}``")

	@commands.command(brief = "Endlessly sends DotA 2 ability icons to name.", aliases = ["icon"])
	@commands.cooldown(1, 50, commands.BucketType.user)
	async def iconquiz(self, ctx):
		player = Player(ctx.author, ctx)
		lives = player.set_lives(3)
		accumulated_g = 0
		ncorrectansws = 0
		ncorrectanswsinarow = 0
		while True:
			if lives < 0.4:		#ncorrectansws*(accumulated_g+ncorrectansws-1)
				g = player.add_gold(accumulated_g)		#((2a+d(n-1))/2)n a = accumulated_g d = 2  n = ncorrectansws
				await ctx.send(f"You ran out of lives, you got ``{ncorrectansws}`` correct answers and accumulated ``{g}`` gold.")
				break
			elif lives == 322:
				g = player.add_gold(accumulated_g)		#((2a+d(n-1))/2)n a = accumulated_g d = 2  n = ncorrectansws
				await ctx.send(f"You have stopped the iconquiz, you got ``{ncorrectansws}`` correct answers and accumulated ``{g}`` gold.")
				break
			iconn = player.unique_int_randomizer(iconquizlen, "iconquiznumbers")	#Random number to give a random icon
			iconobj = iconquizlist[iconn]
			question = iconobj.get_image()
			await ctx.send(f"**``Name the shown icon.``**", file=discord.File(f"./iconquizimages/{question}"))
			def check(m):
				return m.channel == player.channel and m.author == player.author		#checks if the reply came from the same person in the same channel
			try:
				msg = await self.bot.wait_for("message", check=check, timeout=player.set_duration(13))
			except asyncio.TimeoutError:			#If too late
				lives -= 1
				await ctx.send(f"**{quizdata.get_answ('L')}** The correct answer was ``{iconobj.get_answer()}``, ``{lives}`` lives remaining.")
				accumulated_g -= 10
				ncorrectanswsinarow = player.clutched(ncorrectanswsinarow)
				time.sleep(0.2)
			else:
				if strip_str(msg.content) == "skip":
					lives -= 0.5
					ncorrectanswsinarow = player.clutched(ncorrectanswsinarow)
					await ctx.send(f"The correct answer was ``{iconobj.get_answer()}``, you have ``{lives}`` lives remaining.")
				elif strip_str(msg.content) == "stop":
					lives = 322
				elif iconobj.check_answer(msg.content, player.MKB):
					await ctx.send(f"**{quizdata.get_answ('R')}**")
					accumulated_g += 20 + 5*ncorrectanswsinarow
					ncorrectansws += 1
					ncorrectanswsinarow += 1
				else:
					lives -= 1
					ncorrectanswsinarow = player.clutched(ncorrectanswsinarow)
					await ctx.send(f"**{quizdata.get_answ('W')}** The correct answer was ``{iconobj.get_answer()}``, ``{lives}`` lives remaining.")

	@commands.command(brief = "iconquiz as a multiple choice test.", aliases = ["easyicon"], hidden=True)
	@commands.cooldown(1, 50, commands.BucketType.user)
	async def easyiconquiz(self, ctx):
		player = Player(ctx.author, ctx)
		lives = player.set_lives(3)
		accumulated_g = 0
		ncorrectansws = 0
		ncorrectanswsinarow = 0
		while True:
			if lives < 0.4:
				g = player.add_gold(accumulated_g)
				await ctx.send(f"You ran out of lives, you got ``{ncorrectansws}`` correct answers and accumulated ``{g}`` gold.")
				break
			elif lives == 322:
				g = player.add_gold(accumulated_g)
				await ctx.send(f"You have stopped the iconquiz, you got ``{ncorrectansws}`` correct answers and accumulated ``{g}`` gold.")
				break
			iconn = player.unique_int_randomizer(iconquizlen, "iconquiznumbers")	#Random number to give a random icon
			question, answer = iconquizkeys[iconn], iconquizvalues[iconn]
			correctansw = find_correct_answer(answer)	#Find the correct answer to be displayed incase user gets it wrong
			iconimage = discord.File(f"./iconquizimages/{question}", filename=question)
			iconembed = discord.Embed(title="Name the displayed icon.", colour=0x9b59b6)
			iconembed.set_thumbnail(url=f"attachment://{question}")
			possibleansws = [correctansw]		#all the possible answers
			while len(possibleansws) < 8:		#adds random icon names
				possibleansws.append(random.choice(iconnames))
			shuffled = []		#shuffled list of random and correct names
			for icon in random.sample(possibleansws, 8):
				shuffled.append(icon)
			result = ""		#result to display with proper spacing and all
			for i in range(8):
				result += f"**{alphabet[i]})** {shuffled[i]}"
				if i%2:
					result += "\n"
				else:
					result += " **|		|** "
			iconembed.add_field(name="Possible answers:", value=result+"*Type in the letter you consider correct.*", inline=True)
			await ctx.send(file=iconimage, embed=iconembed)
			def check(m):
				return m.channel == player.channel and m.author == player.author		#checks if the reply came from the same person in the same channel
			try:
				msg = await self.bot.wait_for("message", check=check, timeout=player.set_duration(8))
			except asyncio.TimeoutError:			#If too late
				lives -= 1
				await ctx.send(f"**{quizdata.get_answ('L')}** The correct answer was ``{correctansw}``, ``{lives}`` lives remaining.")
				accumulated_g -= 10
				time.sleep(0.2)
			else:
				if strip_str(msg.content) == "skip":
					lives -= 0.5
					await ctx.send(f"The correct answer was ``{correctansw}``, you have ``{lives}`` lives remaining.")
				elif strip_str(msg.content) == "stop":
					lives = 322
				else:
					success = True
					singleletter = strip_str(msg.content).upper()
					try:
						letterindex = alphabet.index(singleletter)
					except ValueError:
						success = False
					if success:
						if shuffled[letterindex] == correctansw:
							await ctx.send(f"**{quizdata.get_answ('R')}**")
							accumulated_g += 8
							ncorrectansws += 1
						else:
							success = False
					if not success:
						lives -= 1
						await ctx.send(f"**{quizdata.get_answ('W')}** The correct answer was ``{correctansw}``, ``{lives}`` lives remaining.")

	@commands.command(brief = "Endlessly sends DotA2 items to be assembled.", aliases=["recipe"])
	@commands.cooldown(1, 50, commands.BucketType.user)
	async def shopquiz(self, ctx):
		player = Player(ctx.author, ctx)
		accumulated_g = 0			#gold that will be given to the user at the end
		lives = player.set_lives(3)		#tries they have for the shopkeeperquiz
		ncorrectansws = 0			#number of items they completed
		ncorrectanswsinarow = 0
		while True:					#while lives are more than 0.4 it keeps sending new items to build once the previous item is completed/skipped
			if lives <= 0.4:		#ends the shopquiz
				g = player.add_gold(accumulated_g)
				await ctx.send(f"**{player.author.display_name}** You're out of lives, You built ``{ncorrectansws}`` items and accumulated ``{g}`` gold during the Shopkeepers Quiz.")
				break
			elif lives == 322:		#if the quiz is stopped by order
				g = player.add_gold(accumulated_g)
				await ctx.send(f"**{player.author.display_name}** You built ``{ncorrectansws}`` items and accumulated ``{g}`` gold during the Shopkeepers Quiz.")
				break
			shopkeepn = player.unique_int_randomizer(shopkeeplen, "shopkeepnumbers")
			shopkeepobj = shopkeeplist[shopkeepn]
			itemimage, itemembed = shopkeepobj.create_embed()
			await ctx.send(file=itemimage, embed=itemembed)
			def check(m):
				return m.channel == player.channel and m.author == player.author
			try:
				msg = await self.bot.wait_for("message", check=check, timeout=player.set_duration(21))
			except asyncio.TimeoutError:					#If too late
				lives -= 1
				await ctx.send(f"**{quizdata.get_answ('L')}** This item can be built with ``{shopkeepobj.get_answer()}`` You have ``{lives}`` lives remaining.")
				accumulated_g -= 10
				ncorrectanswsinarow = player.clutched(ncorrectanswsinarow)
				time.sleep(0.2)
			else:
				if strip_str(msg.content) == "stop":		#changes lives number to 322 and stops the quiz
					lives = 322
					await ctx.send(f"This item can be built with ``{shopkeepobj.get_answer()}``")
				elif strip_str(msg.content) == "skip":		#skip a single item and lose 0.5 life for it
					lives -= 0.5
					ncorrectanswsinarow = player.clutched(ncorrectanswsinarow)
					await ctx.send(f"This item can be built with ``{shopkeepobj.get_answer()}``, you have ``{lives}`` lives remaining.")
				else:
					if shopkeepobj.check_answer(msg.content):
						await ctx.send(f"**{quizdata.get_answ('R')}**")
						accumulated_g += 30 + 8*ncorrectanswsinarow
						ncorrectansws, ncorrectanswsinarow = ncorrectansws + 1, ncorrectanswsinarow + 1
					else:
						lives -= 1
						ncorrectanswsinarow = player.clutched(ncorrectanswsinarow)
						await ctx.send(f"**{quizdata.get_answ('W')}**, This item can be built with ``{shopkeepobj.get_answer()}`` You have ``{lives}`` lives remaining.")

	@commands.command(brief = "Set of questions multiple people can answer.", aliases = ["ffa"], hidden=True)
	@commands.cooldown(1, 80, commands.BucketType.channel)
	async def freeforall(self, ctx):
		player = Player(ctx.author, ctx)
		usersdict = {player.author:0}			#dictionary that consists of all the participants and their points
		nquestions = player.set_necro(25)		#number of questions that will be asked
		ncorrectansws = 0			#number of correctly answered questions by everyone
		while True:
			if nquestions <= 0:				#stop the quiz
				prizepool = 56*(ncorrectansws*(len(usersdict)**2))
				sortedusersdict = {k: v for k, v in sorted(usersdict.items(), key=lambda item: item[1], reverse=True)}	#sorting users according to
				sortedkeys, sortedvalues = list(sortedusersdict.keys()), list(sortedusersdict.values())	#their points and getting the keys and values
				if sortedvalues[0] > 0:
					basestr = "Participant: 		          Points:	    	Prize:\n"		#base of the ending message
					if len(sortedusersdict) > 5:
						for i in range(0, 5):			#display the top 5 players
							userprize = round(prizepool * prizeperc[i])
							if sortedvalues[i] > 0:
								tempplayer = Player(sortedkeys[i], ctx)
								g = tempplayer.add_gold(userprize)
							else:
								break
							multiplier1 = 33 - len(sortedkeys[i].display_name)
							multiplier2 = 16 - len(str(sortedvalues[i]))
							basestr = basestr + f"{str(i + 1)}){sortedkeys[i].display_name}" + " "*multiplier1 + str(sortedvalues[i]) + " "*multiplier2 + f"{str(g)}gold\n"
					else:
						for i in range(0, len(sortedusersdict)):
							userprize = round(prizepool * prizeperc[i])
							if sortedvalues[i] > 0:
								tempplayer = Player(sortedkeys[i], ctx)
								g = tempplayer.add_gold(userprize)
							else:
								break
							multiplier1 = 33 - len(sortedkeys[i].display_name)
							multiplier2 = 16 - len(str(sortedvalues[i]))
							basestr = basestr + f"{str(i + 1)}){sortedkeys[i].display_name}" + " "*multiplier1 + str(sortedvalues[i]) + " "*multiplier2 + f"{str(g)}gold\n"
					await ctx.send(f"```{basestr}```")
				else:
					await ctx.send("**Nobody got a positive amount of points. :(**")

				break
			time.sleep(0.35)
			nquestions -= 1
			decider = random.randint(0, 1)
			if decider == 0:			#regular questions
				questn = player.unique_int_randomizer(questlen, "questnumbers")		#Random number to give a random question
				questobj = questlist[questn]
				question, answer = questobj.get_question(), questobj.get_answer()
				correctansw = find_correct_answer(answer)
				if type(question) == tuple:		#if the question comes with an image
					await ctx.send(f"**```{question[0]}```**", file=discord.File(f"./quizimages/{question[1]}"))
				else:										#for normal string questions
					await ctx.send(f"**```{question}```**")
				giventime = questobj.get_time()
				def check(m):
					return m.channel == player.channel and m.author != self.bot.user		#checks if the reply came from the same channel
				counter = 0				#counter to allow only 3 incorrect answers before moving on
				while True:
					if counter >= 3:		#stopping the current one question
						if type(answer) == list:
							await ctx.send(f"One of the possible answers was ``{correctansw}``")
						else:
							await ctx.send(f"The correct answer was ``{correctansw}``")
						break
					try:
						msg = await self.bot.wait_for("message", check=check, timeout=giventime+6)
					except asyncio.TimeoutError:			#If too late instantly moves to next question
						await ctx.send(f"**{quizdata.get_answ('L')}** The correct answer was ``{correctansw}``")
						break
					else:
						currentplayer = Player(msg.author, ctx)
						if currentplayer.compare_strings(msg.content, answer):		#If there is one correct answer
							await ctx.send(f"**{quizdata.get_answ('R')}**")
							if currentplayer.author in list(usersdict.keys()):		#if user is already listed in the dict increment the correct answers
								usersdict[currentplayer.author] += 1
							else:											#if not set the new user as a key and set 1 correct answer
								usersdict.update({currentplayer.author:1})
							ncorrectansws += 1
							break
						else:			#if there are multiple answers
							await ctx.send(f"**{quizdata.get_answ('W')}**")
							if currentplayer.author in list(usersdict.keys()):		#if user is already listed in the dict increment the correct answers
								usersdict[currentplayer.author] -= 1			#take a point away if answer is wrong
							counter += 1
			else:
				iconn = player.unique_int_randomizer(iconquizlen, "iconquiznumbers")	#Random number to give a random icon
				question, answer = iconquizkeys[iconn], iconquizvalues[iconn]
				correctansw = find_correct_answer(answer)	#Find the correct answer to be displayed incase user gets it wrong
				await ctx.send(f"**``Name the shown ability.``**", file=discord.File(f"./iconquizimages/{question}"))
				def check(m):
					return m.channel == player.channel and m.author != self.bot.user		#checks if the reply came from the same channel
				counter = 0				#counter to allow only 3 incorrect answers before moving on
				while True:
					if counter >= 3:		#stopping the current one question
						if type(answer) == list:
							await ctx.send(f"One of the possible answers was ``{correctansw}``")
						else:
							await ctx.send(f"The correct answer was ``{correctansw}``")
						break
					try:
						msg = await self.bot.wait_for("message", check=check, timeout=10)
					except asyncio.TimeoutError:			#If too late
						await ctx.send(f"**{quizdata.get_answ('L')}** The correct answer was ``{correctansw}``")
						break
					else:
						currentplayer = Player(msg.author, ctx)
						if currentplayer.compare_strings(msg.content, answer):
							await ctx.send(f"**{quizdata.get_answ('R')}**")
							if currentplayer.author in list(usersdict.keys()):		#if user is already listed in the dict increment the correct answers
								usersdict[currentplayer.author] += 1
							else:											#if not set the new user as a key and set 1 correct answer
								usersdict.update({currentplayer.author:1})
							ncorrectansws += 1
							break
						else:
							await ctx.send(f"**{quizdata.get_answ('W')}**")
							if currentplayer.author in list(usersdict.keys()):		#if user is already listed in the dict increment the correct answers
								usersdict[currentplayer.author] -= 1			#take a point away if answer is wrong
							counter += 1

	@commands.command(brief = "Plays DotA2 sound effects to recognize.", aliases = ["audio"], hidden=True)
	@commands.cooldown(1, 50, commands.BucketType.user)
	async def audioquiz(self, ctx):
		player = Player(ctx.author, ctx)
		timeout = time.time() + player.set_duration(38)						#timeout set
		accumulated_g = 0													#gold that will be given to the user at the end
		ncorrectansws = 0													#number of sounds they answered
		if player.author.voice is None:								#if user not in a vc
			await ctx.send("You must be in a visible voice channel to use this command.")
			self.audioquiz.reset_cooldown(ctx)
		else:
			voicechannel = await player.author.voice.channel.connect()
			await ctx.send(f"""You have base ``{player.set_duration(38)}`` seconds for the audioquiz each correct answer grants you 3 more seconds, answer which **item** or **spell** makes the played sound effect, don't forget to type in **replay** or **re** to replay the audio or **skip** entirely skip it.""")
			time.sleep(2)
			while True:
				if time.time() > timeout:			#stop the quiz, add accumulated gold to user.
					g = player.add_gold(ncorrectansws*(accumulated_g+(2*ncorrectansws)-2))		#((2a+d(n-1))/2)n a = 0 d = 4  n = ncorrectanswsers
					await ctx.send(f"**{player.author.display_name}** you got ``{ncorrectansws}`` correct answers and accumulated ``{g}`` gold during the audioquiz.")
					await ctx.voice_client.disconnect()
					break
				time.sleep(0.2)
				audion = player.unique_int_randomizer(audioquizlen, "audioquiznumbers")		#Random number to give a random audioion
				question, answer = audioquizkeys[audion], audioquizvalues[audion]
				correctansw = find_correct_answer(answer)	#find correct answer to display later
				duration = round(MP3(f"./soundquizaudio/{question}").info.length+3)   #duration of the audiofile in seconds
				source = await discord.FFmpegOpusAudio.from_probe(f"./soundquizaudio/{question}")	#convert audio to opus
				ctx.voice_client.stop()			#stop audio to make sure next sound can play
				ctx.voice_client.play(source)
				def check(m):
					return m.channel == player.channel and m.author == player.author		#checks if the reply came from the same person in the same channel
				while True:
					try:					#vvvv calc_time() takes strings as arguments so duration is converted to a string by multiplying "a"
						msg = await self.bot.wait_for("message", check=check, timeout=player.set_duration(calc_time("a"*8*duration, answer)))
					except asyncio.TimeoutError:			#If too late
						await ctx.send(f"**{quizdata.get_answ('L')}**, The correct answer was ``{correctansw}``.")
						accumulated_g -= 10
						break
					else:
						if strip_str(msg.content) == "skip":		#if user wants to move onto the next audioion
							accumulated_g -= 4
							if type(answer) == list:
								await ctx.send(f"One of the possible answers was ``{correctansw}``.")
							else:
								await ctx.send(f"The correct answer was ``{correctansw}``.")
							break
						elif strip_str(msg.content) == "stop" or strip_str(msg.content) == "stfu":		#if user stops the quiz
							timeout = 0
							break
						elif strip_str(msg.content) == "replay" or strip_str(msg.content) == "re":
							try:
								ctx.voice_client.stop()			#stop audio to make sure next sound can play
							except:
								pass
							source = await discord.FFmpegOpusAudio.from_probe(f"./soundquizaudio/{question}")	#convert audio to opus
							ctx.voice_client.play(source)
						elif player.compare_strings(msg.content, answer):	#If there is one correct answer
							await ctx.send(f"**{quizdata.get_answ('R')}**")
							timeout += 3							#add time before timeout for every correct answer
							accumulated_g += 23
							ncorrectansws += 1
							break
						else:
							accumulated_g -= 4
							if type(answer) == list:
								await ctx.send(f"**{quizdata.get_answ('W')}** One of the possible answers was ``{correctansw}``")
							else:
								await ctx.send(f"**{quizdata.get_answ('W')}** The correct answer was ``{correctansw}``.")
							break

	@commands.command(brief = "Rapid questions that give more gold but with a risk.")
	@commands.cooldown(1, 52, commands.BucketType.channel)
	async def blitz(self, ctx):
		player = Player(ctx.author, ctx)
		timeout = player.set_duration(50) #full time for blitz round
		accumulated_g = 0
		ncorrectansws = 0
		await ctx.send(f"""You have ``{timeout}`` seconds for the blitz, don't forget to type in **skip** if you don't know the answer to minimize the gold and time you lose.""")
		time.sleep(3.7)
		timeout += time.time()
		while True:
			time.sleep(0.2)
			if time.time() > timeout:			#stop the blitz, add accumulated gold to user.
				g = player.add_gold(ncorrectansws*(accumulated_g+(2*ncorrectansws)-2))		#((2a+d(n-1))/2)n a = 0 d = 4  n = ncorrectanswsers
				await ctx.send(f"**{player.author.display_name}** you got ``{ncorrectansws}`` correct answers and accumulated ``{g}`` gold during the blitz.")
				break
			questn = player.unique_int_randomizer(questlen, "questnumbers")		#Random number to give a random question
			questobj = questlist[questn]
			question = questobj.get_question()
			if questobj.questionType == 2:		#if the question comes with an image
				await ctx.send(f"**```{question[0]}```**", file=discord.File(f"./quizimages/{question[1]}"))
			else:										#for normal string questions
				await ctx.send(f"**```{question}```**")
			straddon = 'The correct answer was' #For incorrect answer
			if questobj.answerType != 1:
				straddon = 'One of the possible correct answer was'
			def check(m):
				return m.channel == player.channel and m.author == player.author		#checks if the reply came from the same person in the same channel
			try:
				msg = await self.bot.wait_for("message", check=check, timeout=player.set_duration(questobj.get_time()))
			except asyncio.TimeoutError:			#If too late
				await ctx.send(f"**{quizdata.get_answ('L')}** {straddon} ``{questobj.get_answer()}``")
				accumulated_g -= 21
			else:
				if strip_str(msg.content) == "skip":		#if user wants to move onto the next question
					accumulated_g -= 4
					await ctx.send(f"**{straddon} ``{questobj.get_answer()}``")
				elif questobj.check_answer(msg.content, player.MKB):		#If there is one correct answer
					accumulated_g += 18
					ncorrectansws += 1
				else:
					accumulated_g -= 12
					await ctx.send(f"**{quizdata.get_answ('W')}** {straddon} ``{questobj.get_answer()}``")

	@commands.command(brief = "Duel another user for gold.", hidden=True)
	@commands.cooldown(1, 45, commands.BucketType.channel)
	async def duel(self, ctx, opponent: discord.Member, wager:int):
		player1 = Player(ctx.author, ctx)
		maxwager = player1.set_plunder(10000)
		if str(opponent.id) not in player1.users.keys():
			await ctx.send("That user doesn't have any gold to duel.")
			self.duel.reset_cooldown(ctx)
		elif player1.author == opponent:
			await ctx.send("Why are you trying to duel yourself?")
			self.duel.reset_cooldown(ctx)
		elif wager < 300:
			await ctx.send("The minimum wager of a duel is 300 gold.")
			self.duel.reset_cooldown(ctx)
		elif wager > maxwager:
			await ctx.send(f"The maximum wager you can set is {maxwager} gold.")
			self.duel.reset_cooldown(ctx)
		elif player1.users[str(player1.author.id)]["gold"] < wager:
			await ctx.send("You don't have enough gold to start a duel.")
			self.duel.reset_cooldown(ctx)
		elif player1.users[str(opponent.id)]["gold"] < wager:
			await ctx.send("Your chosen opponent doesn't have enough gold to start a duel.")
			self.duel.reset_cooldown(ctx)
		else:
			await ctx.send(f"{opponent.mention} Do you wish to duel {player1.author.display_name} for {wager} gold? Write **Accept** in chat if you wish to duel or **Decline** if otherwise.")
			def check(m):
				return m.channel == player1.channel and m.author == opponent		#checks if the reply came from the same person in the same channel
			try:
				msg = await self.bot.wait_for("message", check=check, timeout=25)
			except asyncio.TimeoutError:	#If too late
				await ctx.send("The opponent didn't accept the duel.")
			else:
				if strip_str(msg.content) == "accept":
					player2 = Player(opponent, ctx)
					questionsasked = 0
					questionsanswered1 = 0
					questionsanswered2 = 0
					await ctx.send("The opponent has accepted the duel, ``15`` questions will be asked and the one to get the most amount of correct answers wins!")
					time.sleep(3.25)
					while True:
						time.sleep(0.75)
						if questionsasked == 15:
							if questionsanswered1 > questionsanswered2:
								winner = player1.author
								loser = opponent
								g_win = player1.add_gold(wager-200)
								g_lose = player2.add_gold(-wager)
							else:
								winner = opponent
								loser = player1.author
								g_win = player2.add_gold(wager-200)
								g_lose = player1.add_gold(-wager)
							await ctx.send(f"The winner is {winner.display_name}! {winner.display_name} you won ``{g_win}`` gold and {loser.display_name} lost ``{g_lose}``...")
							break

						questn = player1.unique_int_randomizer(questlen, "questnumbers")		#Random number to give a random question
						question, answer = questkeys[questn], questvalues[questn]
						correctansw = find_correct_answer(answer)	#Find the correct answer to be displayed incase user gets it wrong
						if type(question) == tuple:			#if the question comes with an image
							await ctx.send(f"**```{question[0]}```**", file=discord.File(f"./quizimages/{question[1]}"))
							questionsasked += 1
						else:						#for normal string questions
							await ctx.send(f"**```{question}```**")
							questionsasked += 1
						def check(m):
							return m.channel == player1.channel and (m.author == player1.author or opponent)		#checks if the reply came from the same person in the same channel
						try:
							msg = await self.bot.wait_for("message", check=check, timeout=20)
						except asyncio.TimeoutError:		#If too late
							await ctx.send(f"**{quizdata.get_answ('L')}** The correct answer was ``{correctansw}``")
						else:
							if msg.author == player1.author:
								if player1.compare_strings(msg.content, answer):		#If there is one correct answer
									await ctx.send(f"**{quizdata.get_answ('R')}**")
									questionsanswered1 += 1
								else:
									if type(answer) == list:
										await ctx.send(f"**{quizdata.get_answ('W')}** One of the corrects answer was ``{correctansw}``")
									else:
										await ctx.send(f"**{quizdata.get_answ('W')}** The correct answer was ``{correctansw}``")
									questionsanswered1 -= 1
							else:
								if player2.compare_strings(msg.content, answer):		#If there is one correct answer
									await ctx.send(f"**{quizdata.get_answ('R')}**")
									questionsanswered2 += 1
								else:
									if type(answer) == list:
										await ctx.send(f"**{quizdata.get_answ('W')}** One of the corrects answer was ``{correctansw}``")
									else:
										await ctx.send(f"**{quizdata.get_answ('W')}** The correct answer was ``{correctansw}``")
									questionsanswered2 -= 1

				else:
					await ctx.send("The opponent has declined the offer.")

	@commands.command(brief = "Endless mix of questions, items, icons and scrambles.", hidden=True)
	@commands.cooldown(1, 400, commands.BucketType.user)
	async def endless(self, ctx):
		player = Player(ctx.author, ctx)
		try:
			if 4200 in player.inventory:
				accumulated_g = 0		#accumulated gold during the quiz
				ncorrectansws = 0		#number of correct answers
				ncorrectanswsinarow = 0
				lives = player.set_lives(5)
				while True:			#keeps asking questions till it breaks
					if lives < 0.4:		#break the whole command if lives are 0 or 322(which means the command was stopped by user)
						g = player.add_gold(accumulated_g)
						await ctx.send(f"You ran out of lives and you accumulated ``{g}`` gold with ``{ncorrectansws}`` correct answers.")
						break
					if lives == 322:
						g = player.add_gold(accumulated_g)
						await ctx.send(f"You have stopped the endless quiz, you accumulated ``{g}`` gold with ``{ncorrectansws}`` correct answers.")
						break
					decider = random.randint(0, 3)
					if decider == 0:		#if random number is 0 the question will be quiz
							questn = player.unique_int_randomizer(questlen, "questnumbers")			#Random number to give a random question
							question, answer = questkeys[questn], questvalues[questn]
							correctansw = find_correct_answer(answer)		#obtaining the correct answer to display later
							if type(question) == tuple:		#if the question comes with an image
								await ctx.send(f"**```{question[0]}```**", file=discord.File(f"./quizimages/{question[1]}"))
							else:					#for normal string questions
								await ctx.send(f"**```{question}```**")
							def check(m):
								return m.channel == player.channel and m.author == player.author	#checks if the reply came from the same person in the same channel
							try:
								msg = await self.bot.wait_for("message", check=check, timeout=player.set_duration(16))
							except asyncio.TimeoutError:	#If too late
								lives -= 1
								await ctx.send(f"**{quizdata.get_answ('L')}**, the correct answer was ``{correctansw}``, ``{lives}`` lives left.")
								accumulated_g -= 15
								ncorrectanswsinarow = player.clutched(ncorrectanswsinarow)
								time.sleep(0.2)
							else:
								if strip_str(msg.content) == "skip":	#if user skips a question
									lives -= 0.5
									ncorrectanswsinarow = player.clutched(ncorrectanswsinarow)
									await ctx.send(f"The correct answer was ``{correctansw}``, you have ``{lives}`` remaining.")
								elif strip_str(msg.content) == "stop":	#if user stops the "endless" quiz
									lives = 322
								elif player.compare_strings(msg.content, answer):	#If there is only one correct answer
									accumulated_g += 18 + 5*ncorrectansws
									ncorrectansws, ncorrectanswsinarow = ncorrectansws + 1, ncorrectanswsinarow + 1
								else:
									lives -= 1
									ncorrectanswsinarow = player.clutched(ncorrectanswsinarow)
									if type(answer) == list:
										await ctx.send(f"**{quizdata.get_answ('W')}** One of the possible answer was ``{correctansw}``, ``{lives}`` lives remaining.")
									else:
										await ctx.send(f"**{quizdata.get_answ('W')}** The correct answer was ``{correctansw}``, ``{lives}`` lives remaining.")

					elif decider == 1:	#if random integer is 1 the question is a single shopquiz
						shopkeepn = player.unique_int_randomizer(shopkeeplen, "shopkeepnumbers")
						question, answer = shopkeepkeys[shopkeepn], shopkeepvalues[shopkeepn]
						correctansw = "``, ``".join(shopkeepvalues[shopkeepn])			#creates a highlighted string of correct items
						itemimage = discord.File(f"./shopkeepimages/{question}", filename=question)
						itemembed = discord.Embed(title="Assemble this item:", colour=0x9b59b6)
						itemembed.set_thumbnail(url=f"attachment://{question}")
						possibleansws = []		#all the possible answers
						for item in shopkeepvalues[shopkeepn]:	#starts with correct items
							if item != "Recipe":
								possibleansws.append(item)
						while len(possibleansws) < 11:		#adds random items
							possibleansws.append(random.choice(ingredients))
						shuffled = []		#shuffled list of random and correct items
						for item in random.sample(possibleansws, 11):
							shuffled.append(item)
						shuffled.append("Recipe")
						result = ""		#result to display with proper spacing and all
						for i in range(12):
							result += f"**{alphabet[i]})** {shuffled[i]}"
							if i%2:
								result += "\n"
							else:
								result += " **| |** "
						itemembed.add_field(name="Possible answers:", value=result+"*Type in the letters of the items you consider correct.*", inline=True)
						await ctx.send(file=itemimage, embed=itemembed)
						def check(m):
							return m.channel == player.channel and m.author == player.author
						try:
							msg = await self.bot.wait_for("message", check=check, timeout=player.set_duration(21))
						except asyncio.TimeoutError:					#If too late
							lives -= 1
							await ctx.send(f"**{quizdata.get_answ('L')}** This item can be built with ``{correctansw}`` You have ``{lives}`` lives remaining.")
							accumulated_g -= 10
							ncorrectanswsinarow = player.clutched(ncorrectanswsinarow)
							time.sleep(0.2)
						else:
							if strip_str(msg.content) == "stop":		#changes lives number to 322 and stops the quiz
								lives = 322
								await ctx.send(f"This item can be built with ``{correctansw}``")
							elif strip_str(msg.content) == "skip":		#skip a single item and lose 0.5 life for it
								lives -= 0.5
								ncorrectanswsinarow = player.clutched(ncorrectanswsinarow)
								await ctx.send(f"This item can be built with ``{correctansw}``, you have ``{lives}`` lives remaining.")
							else:
								success = True
								for letter in strip_str(msg.content).upper():
									try:
										letterindex = alphabet.index(letter)
										shopkeepvalues[shopkeepn].remove(shuffled[letterindex])
									except ValueError:
										success = False
										break
								if (len(shopkeepvalues[shopkeepn]) == 0) and success:
									accumulated_g += 34 + 8*ncorrectanswsinarow
									ncorrectansws, ncorrectanswsinarow = ncorrectansws + 1, ncorrectanswsinarow + 1
								else:
									lives -= 1
									ncorrectanswsinarow = player.clutched(ncorrectanswsinarow)
									await ctx.send(f"**{quizdata.get_answ('W')}**, This item can be built with ``{correctansw}`` You have ``{lives}`` lives remaining.")
					elif decider == 2:
						iconn = player.unique_int_randomizer(iconquizlen, "iconquiznumbers")		#Random number to give a random icon
						question, answer = iconquizkeys[iconn], iconquizvalues[iconn]
						correctansw = find_correct_answer(answer)		#Find the correct answer to be displayed incase user gets it wrong
						await ctx.send(f"**``Name the shown ability.``**", file=discord.File(f"./iconquizimages/{question}"))
						def check(m):
							return m.channel == player.channel and m.author == player.author	#checks if the reply came from the same person in the same channel
						try:
							msg = await self.bot.wait_for("message", check=check, timeout=player.set_duration(12))
						except asyncio.TimeoutError:	#If too late
							lives -= 1
							await ctx.send(f"**{quizdata.get_answ('L')}** The correct answer was ``{correctansw}``, ``{lives}`` lives remaining.")
							accumulated_g -= 15
							ncorrectanswsinarow = player.clutched(ncorrectanswsinarow)
							time.sleep(0.2)
						else:
							if strip_str(msg.content) == "skip":
								lives -= 0.5
								ncorrectanswsinarow = player.clutched(ncorrectanswsinarow)
								await ctx.send(f"The correct answer was ``{correctansw}``, you have ``{lives}`` lives remaining.")
							elif strip_str(msg.content) == "stop":
								lives = 322
							elif player.compare_strings(msg.content, answer):
								accumulated_g += 20 + 5*ncorrectanswsinarow
								ncorrectansws, ncorrectanswsinarow = ncorrectansws + 1, ncorrectanswsinarow + 1
							else:
								lives -= 1
								ncorrectanswsinarow = player.clutched(ncorrectanswsinarow)
								await ctx.send(f"**{quizdata.get_answ('W')}** The correct answer was ``{correctansw}``, ``{lives}`` lives remaining.")
					else:
						scramblen = player.unique_int_randomizer(scramblelen, "scramblenumbers")			#Random number to give a random question
						correctansw = scramblelist[scramblen]			#the correct answer
						scrambledworde = []			#empty list to .join() emojies onto
						charlist = list(correctansw.lower().replace("'", ""))			#converting string to list
						for char in random.sample(charlist, len(charlist)):		#shuffling the word list and looping through it
							scrambledworde.append(charemojies[char])		#picking up values of charemojies of the lowercase characters
						output = " ".join(scrambledworde)					#joining them to form a string of all emojies to output
						await ctx.send(f"**``Unscramble this word:``**\n{output}")
						def check(m):
							return m.channel == player.channel and m.author == player.author		#checks if the reply came from the same person in the same channel
						try:
							msg = await self.bot.wait_for("message", check=check, timeout=player.set_duration(20))
						except asyncio.TimeoutError:		#If too late
							lives -= 1
							await ctx.send(f"**{quizdata.get_answ('L')}** The correct answer was ``{correctansw}`` You have ``{lives}`` remaining.")
							ncorrectanswsinarow = player.clutched(ncorrectanswsinarow)
							time.sleep(0.2)
						else:
							if strip_str(msg.content) == "skip":	#if user skips a question
								lives -= 0.5
								ncorrectanswsinarow = player.clutched(ncorrectanswsinarow)
								await ctx.send(f"The correct answer was ``{correctansw}`` You have ``{lives}`` remaining.")
							elif strip_str(msg.content) == "stop":	#if user stops the "endless" quiz
								lives = 322
							elif player.compare_strings(msg.content, correctansw):
								accumulated_g += 80 + 6*ncorrectanswsinarow
								ncorrectansws += 1
								ncorrectanswsinarow += 1
							else:
								lives -= 1
								await ctx.send(f"**{quizdata.get_answ('W')}** The correct answer was ``{correctansw}`` You have ``{lives}`` remaining.")
								ncorrectanswsinarow = player.clutched(ncorrectanswsinarow)
			else:
				self.endless.reset_cooldown(ctx)
				await ctx.send("You don't have an **Aghanim's Scepter** to use Endless. Try 322 store to see all items.")
		except KeyError:
			pass

	@quiz.error
	async def quizerror(self, ctx, error):
		if isinstance(error, commands.CommandOnCooldown):
			users = open_json("users.json")
			if 5000 in users[str(ctx.message.author.id)]["items"]:
				if error.retry_after < 3:		#if user has octarine and the remaining time of the cooldown is Less
					await ctx.reinvoke()		#than the time octarine saves the user just bypasses the cooldownerror
					return
				else:
					await ctx.send("**Quiz** is on **cooldown** at the moment. Try again in a few seconds")
			else:
				await ctx.send("**Quiz** is on **cooldown** at the moment. You can buy an Octarine Core in the store to decrease command cooldowns.")

	@iconquiz.error
	async def iconquizerror(self, ctx, error):
		if isinstance(error, commands.CommandOnCooldown):
			users = open_json("users.json")
			if 5000 in users[str(ctx.message.author.id)]["items"]:
				if error.retry_after < 13:
					await ctx.reinvoke()
					return
				else:
					await ctx.send("**IconQuiz** is on **cooldown** at the moment.")
			else:
				await ctx.send("**IconQuiz** is on **cooldown** at the moment. You can buy an Octarine Core in the store to decrease command cooldowns.")

	@scramble.error
	async def scrambleerror(self, ctx, error):
		if isinstance(error, commands.CommandOnCooldown):
			users = open_json("users.json")
			if 5000 in users[str(ctx.message.author.id)]["items"]:
				if error.retry_after < 3:
					await ctx.reinvoke()
					return
				else:
					await ctx.send("**Scramble** is on **cooldown** at the moment.")
			else:
				await ctx.send("**Scramble** is on **cooldown** at the moment. You can buy an Octarine Core in the store to decrease command cooldowns.")

	@shopquiz.error
	async def shopquizerror(self, ctx, error):
		if isinstance(error, commands.CommandOnCooldown):
			users = open_json("users.json")
			if 5000 in users[str(ctx.message.author.id)]["items"]:
				if error.retry_after < 12.5:
					await ctx.reinvoke()
					return
				else:
					await ctx.send("**Shopkeepers quiz** is on **cooldown** at the moment.")
			else:
				await ctx.send("**Shopkeepers quiz** is on **cooldown** at the moment. You can buy an Octarine Core in the store to decrease command cooldowns.")

	@audioquiz.error
	async def audioquizerror(self, ctx, error):
		if isinstance(error, commands.CommandOnCooldown):
			await ctx.send("**Audioquiz** is currently on cooldown. You can purchase an Octarine Core to decrease command cooldowns.")

	@blitz.error
	async def blitzerror(self, ctx, error):
		if isinstance(error, commands.CommandOnCooldown):
			await ctx.send("**Blitz** is on being used in this channel at the moment, wait a bit or play on a different channel.")

	@duel.error
	async def duelerror(self, ctx, error):
		if isinstance(error, commands.CommandOnCooldown):
			await ctx.send("**Duel** is currently on cooldown in this channel, try another channel or wait a bit.")
		elif isinstance(error, commands.MissingRequiredArgument):
			await ctx.send("You need to specify who you're duelling and how much gold the wager is, like this: 322 duel @user gold")
			self.duel.reset_cooldown(ctx)
		elif isinstance(error, commands.BadArgument):
			await ctx.send("That user doesn't exist or isn't in this server, try duelling someone else.")
			self.duel.reset_cooldown(ctx)

	@freeforall.error
	async def freeforallerror(self, ctx, error):
		if isinstance(error, commands.CommandOnCooldown):
			await ctx.send("**Freeforall** is currently on cooldown in this channel, try another channel or wait a bit.")

	@endless.error
	async def endlesserror(self, ctx, error):
		if isinstance(error, commands.CommandOnCooldown):
			users = open_json("users.json")
			if 5000 in users[str(ctx.message.author.id)]["items"]:
				if error.retry_after < 100:
					await ctx.reinvoke()
					return
				else:
					await ctx.send("**Endless** is on **cooldown** at the moment.")
			else:
				await ctx.send("**Endless** is on **cooldown** at the moment. You can buy an Octarine Core in the store to decrease command cooldowns.")

	async def cog_command_error(self, ctx, error):
		#Errors to be ignored
		if isinstance(error, (commands.CommandOnCooldown, commands.MissingRequiredArgument, commands.BadArgument)):
			pass
		else:
			raise error

async def setup(bot):
	await bot.add_cog(Quizes(bot))
