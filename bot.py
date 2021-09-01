import discord
import requests
import json
from datetime import date
import math
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from os import environ
load_dotenv(".env")

client = discord.Client()
TOKEN = environ.get("DISCORD_TOKEN")
def get_user_point(username):
    response=requests.get("https://codefun.vn/api/users/" + username)
    json_data = json.loads(response.text)
    mes="User " + json_data["data"]["username"] + " aka. " + json_data["data"]["name"] + " has " + str(json_data["data"]["score"]) + " points, ranked " + str(json_data["data"]["rank"])
    return mes
def alias(a):
    codefun,realname=a.split()
    with open('aliases.json', 'r+') as file:
        file_data=json.load(file)
        file_data[realname]=codefun
        file.seek(0)
        json.dump(file_data, file, indent=4)
def processname(a):
    with open('aliases.json', 'r') as file:
        file_data=json.load(file)
        try:
            if file_data[a]=="": return a
            return file_data[a]
        except KeyError:
            return a
# def get_user_past_point(username):
def startcrawl(username,rq):
    data = {
        "contract" : rq,
        "victim" : username,
        "time" : date.today().strftime("%d/%m/%Y")
    }
    with open('contract.json', 'r+') as file:
        file_data=json.load(file)
        file_data.append(data)
        file.seek(0)
        json.dump(file_data, file, indent=4)
    
    with open('crawldata.json', 'r+') as file:
        file_data=json.load(file)
        i=0
        time=0
        try:
            file_data[username]
        except KeyError:
            file_data[username] = {
                "Submissions" : [

                ]
            }
        
        try:
            time=file_data[username]["Submissions"][0]["time"]
        except IndexError:
            time=0
        response=requests.get("https://codefun.vn/api/users/{}/stats?".format(username))
        json_data = json.loads(response.text)
        for subs in json_data["data"]:
            if subs["submitTime"] <= time:
                break
            if subs["score"]==subs["maxScore"]:
                data = {
                    "subid" : subs["submissionId"],
                    "code" : subs["problem"]["code"],
                    "time" : subs["submitTime"]
                }
                file_data[username]["Submissions"].append(data)
        file.seek(0)
        json.dump(file_data, file, indent=4)
def AC(username,rq):
    a="""```\n"""
    a=a+username+" ACed problems:\n"
    startcrawl(username,rq)
    with open('crawldata.json', 'r+') as file:
        file_data=json.load(file)
        for subs in file_data[username]["Submissions"]:
            thoidiem=subs["time"]
            a=a+str(subs["code"])+"\n"
    a=a+"```"
    return a
def drawgraph(a,rq):

    p=a[:2]
    userlist=a[2:].split()
    starttime=500000000000
    endtime=0
    precision=0
    prefix=""
    
    # Calculate precision
    if p.startswith('d'): 
        precision=int(p[1:])*24*60*60
        prefix="d"
    elif p.startswith('h'): 
        prefix="h"
        precision=int(p[1:])*60*60
    elif p.startswith('w'): 
        prefix="w"
        precision=int(p[1:])*7*24*60*60
    tit="Correct Submissions of: "

    # Calculate start&end time
    for user in userlist:
        tit=tit+user+" "
        user=processname(user)
        startcrawl(user,rq)
        with open("crawldata.json",'r') as file:
            json_data=json.load(file)
            starttime=min(starttime,json_data[user]["Submissions"][-1]["time"])
            endtime=max(endtime,json_data[user]["Submissions"][0]["time"])
    
    # x-axis
    name=[]
    for i in range(1,math.floor((endtime-starttime)/precision)+2):
        name.append(prefix+str(i*int(p[1:])))
    
    plt.title(tit)
    plt.xlabel('Time')
    plt.ylabel('Subs')

    for users in userlist:
        user=processname(users)
        intervals=[0]*(math.floor((endtime-starttime)/precision)+1)
        with open("crawldata.json",'r') as file:
            for subs in json_data[user]["Submissions"]:
                pos=math.floor((subs["time"]-starttime)/precision)
                intervals[pos]+=1

        plt.plot(name,intervals,label=users)
    
    plt.legend(loc="upper left")
    plt.savefig('plot.png')
    plt.close()
@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith(':hello'):
        await message.channel.send('Hello!')
    elif message.content.startswith(":gp"):
        username=message.content[4:]
        username=processname(username)
        await message.channel.send(get_user_point(username))
    elif message.content.startswith(":ph"):
        username=message.content[4:]
        drawgraph(username,message.author.name)
        await message.channel.send(file=discord.File('plot.png'))
    elif message.content.startswith(":ac"):
        username=message.content[4:]
        username=processname(username)
        try: await message.channel.send(AC(username,message.author.name))
        except discord.errors.HTTPException: await message.channel.send("This user has ACed so much that it seems impossible for me to display the list")
    elif message.content.startswith(":sc"):
        username=message.content[4:]
        username=processname(username)
        startcrawl(username,message.author.name)
        await message.channel.send("The Codefun account "+username+" has been added to the queue")
    elif message.content.startswith(":al"):
        username=message.content[4:]
        codefun,realname=username.split()
        alias(username)
        await message.channel.send(codefun + " may now be refered to as " + realname)
    elif message.content.startswith(":h") or message.content.startswith(":help"):
        h="""Hello, these are what you can do with me:
            1. Send help with ':help' or simply ':h'
            2. Say hello with ':hello'
            3. Use your high-ranked Codefun account to rekt somebody in a keyboard fight with ':gp' 
            5. Start a crawl session with ':sc'
            4. Crawl and make a plot of somebody's past AC with ':ph + [precision] + user1 + user2 + ...'
                Precision options:
                    h   hour
                    d   day
                    w   week
                + precision multiplier
                Note: The precision multiplier must be smaller than 10, and obviously bigger than 0
                For example: ':ph w2 BDOG_1 BDOG_2'
            6. Crawl and display somebody's AC history with ':ac'
            7. Define aliases using '.al [codefun account] [alias]"""
        await message.channel.send(h)

client.run(TOKEN)