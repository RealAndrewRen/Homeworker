import discord
from discord.ext import commands, tasks
import time
from datetime import datetime, timedelta
import os
import asyncio
from discord.ext.commands import MemberConverter
from keep_alive import keep_alive

cmd_prefix = "h?"    #prefix, can be changed later if we need it 
client = commands.Bot(command_prefix = cmd_prefix, help_command = None) 
questionList = []
blacklist = []
questionIDCounter = 0

#new question object for each question asked
class Question:
  def __init__(self, name, user, query):
    self.name = name
    self.user = user
    self.query = query


@client.event
async def on_ready(): #startup command
  await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="for h?help")) #set what the status of the bot is
  constructBlacklist()
  print("Bot is ready!")
  print("Ready")

class Question:
  def __init__(self, ID, question, member):
    self.ID = ID
    self.question = question
    self.member = member


@client.command() #basic ping command, should have for every bot
async def ping(ctx):
  await ctx.send(f'Pong! {round(client.latency*1000)}ms')

@client.command(aliases=['h'])    #basic help command, easily can edit if we need to
async def help(ctx):
  await ctx.send(f'```HELP PAGE\n\n {cmd_prefix}question or {cmd_prefix}q + [question you want to ask] - {cmd_prefix}q How do I venerate the plough?\nAdds your question to the question list which can be accessed by anyone with the bot across multiple servers. Anyone who wants to help can then directly reach out to you to provide assistance.\n\n {cmd_prefix}delquestion or {cmd_prefix}dq + [question you have asked] - ex. {cmd_prefix}dq How do I venerate the plough?\nRemoves the question you previously asked from the question list.\n\n {cmd_prefix}remind or {cmd_prefix}r + [time interval for the reminder] [the reminder, with quotation marks included] - ex. {cmd_prefix}r 8h "webassing ch. 12 eng #1 due"\nSets a reminder which will ping you at pre-defined intervals before the time you request.\n\n {cmd_prefix}listquestions or {cmd_prefix}lq\nLists all questions that have been asked as well as the contact info of the person who asked the question.\n\n {cmd_prefix}ping - checks ping \n\n {cmd_prefix}help or {cmd_prefix}h - shows this message\n\n```')


#Adds your question to the question list which can be accessed by anyone with the bot across multiple servers. Anyone who wants to help can then directly reach out to you to provide assistance.
@client.command(aliases=['q'])
async def question(ctx, *args):
  senderID = "{0.author}".format(ctx.message)
  print("{0.author}".format(ctx.message))
  if(isInBlacklist(senderID)):
    return 0
  query = " ".join(args[:])
  if(query == ""):
    await ctx.send("Please enter a question")
    return 0
  if(query == " "):
    await ctx.send("Please enter a question")
    return 0
  questionSearchIndex = listQuestionIndex(query)
  print(str(questionSearchIndex))
  senderID = "{0.author.name}#{0.author.discriminator}".format(ctx.message)
  if(questionSearchIndex>=0):
    if(getCompiledUser(questionList[questionSearchIndex])==senderID):
      await ctx.send("You have already asked that question")
      return 0
  else:
    questionList.append(compileQuestionString(query, senderID))
    await ctx.send("Your question '" + query + "' has been logged!")


#Removes the question you previously asked from the question list.
@client.command(aliases=["dq","qd"])
async def delquestion(ctx, *args):
  senderID = "{0.author}".format(ctx.message)
  if(isInBlacklist(senderID)):
    return 0
  delID = " ".join(args[:])
  questionSearchIndex = listIDIndex(delID)
  compiledData = questionList[questionSearchIndex]
  if(questionSearchIndex>=0):
    if(getCompiledUser(compiledData)==senderID):
      print(questionSearchIndex)
      questionList.pop(questionSearchIndex)
      msg = ("Your question '" + getCompiledQuestion(compiledData) + "' has been deleted").format(ctx.message)  
      await ctx.send(msg)

#lists all questions in the list
@client.command(aliases=["lq","ql"])
async def listquestions(ctx):
  questionCounter = 0
  senderID = "{0.author}".format(ctx.message)
  if(isInBlacklist(senderID)):
    return 0
  msg = f"```QUESTION LIST\nIf you see any questions that you can answer, please reach out to the person who asked it through a direct message!"
  for x in questionList:
    questionCounter += 1
    msg = msg + "\n\n" + str(getCompiledID(x)) + ". " + getCompiledQuestion(x)
  msg = msg + "```"
  msg = msg.format(ctx.message)
  await ctx.send(msg)

#iterates through the list to see if a question has already been asked, returns the index in the question list if it has and -1 if it is not in the list 
def listIDIndex(searchID):
    counter = 0
    for x in questionList:
      if getCompiledID(x)==searchID:
        return counter
      counter += 1
    return -1

def listQuestionIndex(query):
    counter = 0
    for x in questionList:
      if getCompiledQuestion(x)==query:
        return counter
      counter += 1
    return -1

#remind command
@client.command(case_insensitive = True, aliases = ["remind", "remindme", "remind_me", "r"])
@commands.bot_has_permissions(attach_files = True, embed_links = True)
async def reminder(ctx, time, *, reminder):
  senderID = "{0.author}".format(ctx.message)
  if(isInBlacklist(senderID)):
    return 0
  print(datetime.utcnow())
  print(reminder)
  user = ctx.message.author
  embed = discord.Embed(color=0x55a7f7, timestamp=datetime.utcnow())
  embed.set_footer(text="If you have any questions, suggestions or bug reports, please join our support Discord Server: link hidden", icon_url=f"{client.user.avatar_url}")
  seconds = 0
  if reminder is None:
    embed.add_field(name='Warning', value='Please specify what do you want me to remind you about.') # Error message
  if time.lower().endswith("d"):
    seconds += int(time[:-1]) * 60 * 60 * 24
    counter = f"{seconds // 60 // 60 // 24} days"
  if time.lower().endswith("h"):
    seconds += int(time[:-1]) * 60 * 60
    counter = f"{seconds // 60 // 60} hours"
  elif time.lower().endswith("m"):
    seconds += int(time[:-1]) * 60
    counter = f"{seconds // 60} minutes"
  elif time.lower().endswith("s"):
    seconds += int(time[:-1])
    counter = f"{seconds} seconds"
  if seconds == 0:
    embed.add_field(name='Warning', value='Please specify a proper duration, send `reminder_help` for more information.')
  elif seconds < 5:
    embed.add_field(name='Warning', value='You have specified a too short duration!\nMinimum duration is 5 seconds.')
  elif seconds > 7776000:
    embed.add_field(name='Warning', value='You have specified a too long duration!\nMaximum duration is 90 days.')
  else:
    await ctx.send(f"Alright, I will remind you about {reminder} in {counter}.")
    await ping1w(ctx, seconds, reminder)
    await ctx.send(f"Hi, you asked me to remind you about {reminder} {counter} ago." + " " + ctx.message.author.mention)
    await ctx.send(embed=embed)


@client.command(case_insensitive = True, aliases = ["aq", "qa"])
async def answerquestion(ctx, questionID, *, answer):
  questionIndex = listIDIndex(int(questionID))
  print(answer)
  compiledQuestion = questionList[questionIndex]
  member = await MemberConverter().convert(ctx, getCompiledUser(compiledQuestion))
  fmessage = "{0.author.name} tried to answer your question: `" + getCompiledQuestion(compiledQuestion) + "` by saying:\n\n`" + answer + "`\n\ndoes this answer your question?"
  await member.send(fmessage.format(ctx.message))
  await ctx.send("Thanks for submitting an answer!".format(ctx.message))
  return 0


#all methods below here are short spam methods that just support the methods above

#if the reminder time period is longer than one week the bot will ping one week before the reminder
async def ping1w(ctx, seconds, reminder):
  if(seconds>604800):
    await asyncio.sleep(seconds-604800)
    await ctx.send(f"Hi, this is your one week reminder about {reminder}." + " " + ctx.message.author.mention)
    await asyncio.sleep(345600)
    seconds = 259200
  await ping3d(ctx, seconds, reminder)

#if the reminder time period is longer than three days the bot will ping three days before the reminder
async def ping3d(ctx, seconds, reminder):
  if(seconds>259200):
    await asyncio.sleep(seconds-259200)
    await ctx.send(f"Hi, this is your three day reminder about {reminder}." + " " + ctx.message.author.mention)
    await asyncio.sleep(86400)
    seconds = 172800
  await ping2d(ctx, seconds, reminder)

#if the reminder time period is longer than two days the bot will ping two days before the reminder
async def ping2d(ctx, seconds, reminder):
  if(seconds>172800):
    await asyncio.sleep(seconds - 172800)
    await ctx.send(f"Hi, this is your two day reminder about {reminder}." + " " + ctx.message.author.mention)
    await asyncio.sleep(86400)
    seconds = 86400
  await ping1d(ctx, seconds, reminder)

#if the reminder time period is longer than one day the bot will ping one day before the reminder
async def ping1d(ctx, seconds, reminder):
  if(seconds>86400):
    await asyncio.sleep(seconds - 86400)
    await ctx.send(f"Hi, this is your one day reminder about {reminder}." + " " + ctx.message.author.mention)
    await asyncio.sleep(64800)
    seconds = 21600
  await ping6h(ctx, seconds, reminder)

#if the reminder time period is longer than six hours the bot will ping six hours before the reminder
async def ping6h(ctx, seconds, reminder):
  if(seconds>21600):
    await asyncio.sleep(seconds - 21600)
    await ctx.send(f"Hi, this is your six hour reminder about {reminder}." + " " + ctx.message.author.mention)
    await asyncio.sleep(18000)
    seconds = 3600
  await ping1h(ctx, seconds, reminder)

#if the reminder time period is longer than one hour the bot will ping one hour before the reminder
async def ping1h(ctx, seconds, reminder):
  if(seconds>3600):
    print(seconds)
    await asyncio.sleep(seconds - 3600)
    await ctx.send(f"Hi, this is your one hour reminder about {reminder}." + " " + ctx.message.author.mention)
    seconds = 300
  await ping5m(ctx, seconds, reminder)

#if the reminder time period is longer than five minutes the bot will ping five minutes before the reminder
async def ping5m(ctx, seconds, reminder):
  if(seconds>300):
    print("5m: " + str(seconds))
    await asyncio.sleep(seconds-300)
    print("sleep done, 5m: " + str(seconds-300))
    await ctx.send(f"Hi, this is your five minute reminder about {reminder}." + " " + ctx.message.author.mention)
    await asyncio.sleep(300)
  else:
    await asyncio.sleep(seconds)

#compiles a string to be stored in the question array given the question string and user data
def compileQuestionString(questionString, userString):
  global questionIDCounter
  questionIDCounter += 1
  return (questionString + "|" + userString + "|" + str(getNextQuestionID()))


def getNextQuestionID():
  if(len(questionList)==0):
    return 1
  for x in range(1, len(questionList)+1):
    for y in range(0, len(questionList)):
      compiledData = questionList[y]
      if str(getCompiledID(compiledData))==str(x):
        break
      elif ((getCompiledID(compiledData)!=x)and(y==len(questionList)-1)):
        return x
    if(x==len(questionList)):
      return x+1

#returns the question part of the compiled question string
def getCompiledQuestion(compiledQuestionString):
  delimiter = compiledQuestionString.find('|')
  return compiledQuestionString[:delimiter]

#returns the user data part of the compiled question string
def getCompiledUser(compiledQuestionString):
  delimiter = compiledQuestionString.find('|')+1
  compiledQuestionString = compiledQuestionString[delimiter:]
  delimiter = compiledQuestionString.find('|')
  return compiledQuestionString[:delimiter]

#returns the ID part of the compiled question string
def getCompiledID(compiledQuestionString):
  delimiter = compiledQuestionString.find('|')+1
  compiledQuestionString = compiledQuestionString[delimiter:]
  delimiter = compiledQuestionString.find('|')+1
  return compiledQuestionString[delimiter:]

def constructBlacklist():
  f = open("blacklist.txt", "r")
  for x in blacklist:
    l = f.nextline()
    if(l!=""):
      blacklist.append(l)

def isInBlacklist(user):
  for x in blacklist:
    if(x==user):
      return true

keep_alive()
token = os.environ.get("DISCORD_BOT_SECRET")
client.run(token)
