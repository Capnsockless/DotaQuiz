import discord
import os, json, asyncio
from discord.ext import commands
import quizdata

os.chdir(os.getcwd())

store_items, store_descriptions = quizdata.store_items, quizdata.store_descriptions
storekeys, storevalues = list(store_items.keys()), list(store_items.values())

jsondir = os.path.dirname(os.path.dirname(os.getcwd())) + "//jsonfiles"

def open_json(jsonfile):
	with open(jsondir + '//' + jsonfile, "r") as fp:
		return json.load(fp)	#openfunc for jsonfiles

def save_json(jsonfile, name):	#savefunc for jsonfiles
	with open(jsondir + '//' + jsonfile, "w") as fp:
		json.dump(name, fp)

def add_gold(user: discord.User, newgold: int):		#add gold to users
	users = open_json("users.json")
	id = str(user.id)
	if 2200 in users[id]["items"]:
		users[id]["gold"] = users[id]["gold"] + round(newgold*1.25)
		save_json("users.json", users)
		return round(newgold*1.25)
	else:
		users[id]["gold"] = users[id]["gold"] + round(newgold)
		save_json("users.json", users)
		return round(newgold)

def strip_str(text):        #function to remove punctuations spaces from string and make it lowercase
    punctuations = ''' !-;:'`"\,/_?'''
    text2 = ""
    for char in text:
       if char not in punctuations:
           text2 = text2 + char
    return text2.lower().replace("the", "")

def take_index(l1, l2):     #Function to find the index of items in a list that are available in another list
    indexi = []
    for index, item in enumerate(l1):
        if item in l2:
            indexi.append(index)
    return indexi

def helm_of_dominator(author, price):       #give discount if userhas helm of the dominator
    users = open_json("users.json")
    if 2350 in users[str(author.id)]["items"]:
        price *= 0.95
    return round(price)

class Store(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief = "See what items are available.", aliases = ["shop"])
    async def store(self, ctx):
        artifacts = ""
        for item in store_items:        #concatenates all the names and prices together to form a list of store items
            multiplier = 23 - len(item)
            multiplier2 = 9 - len(str(store_items[item]))
            artifacts = artifacts + item + (multiplier * " ") + str(store_items[item]) + (multiplier2 * " ") + store_descriptions[item] + " \n"
        await ctx.send(f"``` Item:               Price:    Description: \n{artifacts}```")

    @commands.command(brief = "Buy an item from the store.")
    async def buy(self, ctx, *, purchase):
        users = open_json("users.json")
        id = str(ctx.author.id)
        if id not in users.keys():
            await ctx.send("""You haven't got any gold yet, try "322 help" and use Quiz commands to earn some.""")
            return
        purchasestr = strip_str(purchase)
        user_items = users[id]["items"]
        user_gold = users[id]["gold"]
        if purchasestr not in [strip_str(x) for x in storekeys]:    #store validation
            await ctx.send("That item doesn't exist.")
        elif purchasestr == "cheese":
            price = helm_of_dominator(ctx.author, 20000)
            if user_gold < price:
                await ctx.send("You don't have enough gold to purchase cheese yet, it costs ``20000`` gold.")
            else:
                users[id]["cheese"] = users[id]["cheese"] + 1
                users[id]["gold"] = users[id]["gold"] - price
                await ctx.send("You have purchased a cheese!")
                save_json("users.json", users)
        else:                   #list of user items is stored as the item prices in json file
            itemindex = [strip_str(x) for x in storekeys].index(purchasestr)        #get the index of the item being purchased
            price = helm_of_dominator(ctx.author, storevalues[itemindex])
            if storevalues[itemindex] in user_items:            #if item is already bought
                await ctx.send("You already have that item.")
            elif price > user_gold:             #if item is too expensive
                await ctx.send(f"You don't have enough gold, this item costs {storevalues[itemindex]} gold.")
            else:               #item being purchased
                user_items.append(storevalues[itemindex])       #new item price is appended to users item list
                users[id]["items"] = user_items        #update the list back as a string of a list
                users[id]["gold"] = users[id]["gold"] - price      #take away gold
                await ctx.send("You have purchased the item.")
                save_json("users.json", users)

    @commands.command(brief = "Sell an item from your inventory.")
    async def sell(self, ctx, *, sale):
        users = open_json("users.json")
        id = str(ctx.author.id)
        if id not in users.keys():
            await ctx.send("""You haven't got any gold yet, try "322 help" and use Quiz commands to earn some.""")
            return
        soldstr = strip_str(sale)             #stripped item to be sold
        user_items = users[id]["items"]           #user inventory
        strippeditems = [strip_str(x) for x in storekeys]       #list of stripped store items
        if soldstr == "cheese":
            if users[id]["cheese"] <= 0:
                await ctx.send("You don't have any cheese to sell.")
            else:
                users[id]["gold"] = users[id]["gold"] + 15000
                users[id]["cheese"] = users[id]["cheese"] - 1
                await ctx.send(f"You have sold the cheese for ``15000`` gold.")
                save_json("users.json", users)
        elif soldstr in strippeditems:          #if item exists
            itemindex = strippeditems.index(soldstr)        #gets index to get item's cost
            itemcost = storevalues[itemindex]
            if itemcost in user_items:          #if item is inside user inventory
                user_items.remove(itemcost)     #remove the item from inventory, add half the gold in
                users[id]["items"] = user_items
                users[id]["gold"] = users[id]["gold"] + int(itemcost/2)
                await ctx.send(f"You sold the item for {int(itemcost/2)} gold.")
                save_json("users.json", users)
            else:                     #if item exists but isn't in the inventory
                await ctx.send("You don't have that item in your inventory in order to sell it.")
        else:                 #if item doesn't exist at all
            await ctx.send("That item doesn't exist in the store.")

    @commands.command(brief = "Check how much gold and cheese you own.")
    async def gold(self, ctx):
        users = open_json("users.json")
        id = str(ctx.author.id)
        if id in users.keys():
            authorgold = users[id]["gold"]
            authorcheese = users[id]["cheese"]
            await ctx.send(f"**{ctx.author.display_name}** you currently have **``{authorgold}``** gold and ``{authorcheese}`` cheese.")
        else:
            await ctx.send("""You haven't got any gold yet, try "322 help" and use Quiz commands to earn some.""")


    @commands.command(brief = "Check your inventory.", aliases = ["inv"])
    async def inventory(self, ctx):         #check inventory
        users = open_json("users.json")
        id = str(ctx.author.id)
        if id not in users.keys():
            await ctx.send("""You haven't got an inventory yet, try "322 help" and use Quiz commands to earn gold and buy items!""")
            return
        str_itemlist = users[id]["items"]         #get list of items the user has(they're integers)
        if len(str_itemlist) == 0:              #if inventory is empty
            await ctx.send("Your inventory is empty, try 322 buy to purchase items.")
        else:
            indexes = take_index(storevalues, str_itemlist)         #take the indexes the available items inside the list of all store items
            inventory = [storekeys[i] for i in indexes]     #create the actual list of strings of available inventory items
            items_listed = "``, ``".join(inventory)         #create a string to be put into the message
            await ctx.send(f"You have ``{items_listed}`` in your inventory.")


    @commands.command(brief = "Give someone cheese.", aliases = ["give"])
    async def givecheese(self, ctx, reciever: discord.Member, amount:int):
        users = open_json("users.json")
        giver = str(ctx.author.id)          #obtain ids of the cheese giver and reciever
        reciever = str(reciever.id)
        if giver == reciever:
            await ctx.send("Nice try.")
        elif amount <= 0:
            await ctx.send("That amount won't work.")
        elif giver not in users.keys():
            await ctx.send("You haven't got any cheese yet.")
        elif users[giver]["cheese"] < amount:
            await ctx.send("You haven't got that much cheese.")
        elif reciever not in users.keys():
            await ctx.send("That user doesn't have an inventory yet.")
        else:
            users[giver]["cheese"] = users[giver]["cheese"] - amount
            users[reciever]["cheese"] = users[reciever]["cheese"] + amount
            await ctx.send(f"You have successfully transferred {amount} cheese!")
            save_json("users.json", users)

    @commands.command(brief = "Delete your stats.")
    async def clearstats(self, ctx):
        users = open_json("users.json")
        await ctx.send('Are you sure you want to **CLEAR ALL** your gold and your entire inventory? Type "Confirm" to finalize')
        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author		#checks if the reply came from the same person in the same channel
        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:		#If too late
            await ctx.send("Stat clear **cancelled.**")
        else:
            if msg.content == "Confirm":
                id = str(ctx.author.id)
                if id in users.keys():
                    users.pop(id)
                    save_json("users.json", users)
                    await ctx.send("Your stats have been **successfully deleted.**")
                else:
                    await ctx.send("There was nothing to clear.")
            else:
                await ctx.send("Stat clear has been **cancelled.**")

    @buy.error
    async def buyerror(self, ctx, error):
        if isinstance (error, commands.MissingRequiredArgument):
            await ctx.send("""You need to specify what item you're purchasing, try "322 store" to see available items.""")

    @sell.error
    async def sellerror(self, ctx, error):
        if isinstance (error, commands.MissingRequiredArgument):
            await ctx.send("""You need to specify what item you're selling, try "322 inventory" to see what you have.""")

    @givecheese.error
    async def givecheeseerror(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You need to specify who you're giving to and how much cheese you're transfering, like so: 322 givecheese @user 1")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("That user doesn't exist or isn't in this server.")


    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            pass
        else:
            raise error

async def setup(bot):
    await bot.add_cog(Store(bot))
