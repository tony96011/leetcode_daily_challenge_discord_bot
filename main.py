import discord
from discord.ext import commands, tasks
import requests
import time
from datetime import datetime, timedelta, timezone
import json
import pytz

bot = commands.Bot(command_prefix='.', intents=discord.Intents.all())
taipei_tz = pytz.timezone('Asia/Taipei')

BASE_URL = "https://alfa-leetcode-api.onrender.com"

def get_recent_24h_ac_submissions(submission_list):
    current_utc_time = datetime.now(timezone.utc)
    midnight_utc = current_utc_time.replace(hour=0, minute=0, second=0, microsecond=0)
    one_day_ago = midnight_utc - timedelta(days=1)

    recent_submissions = []
    for submission in submission_list:
        submission_time = int(submission.get('timestamp', 0))
        submission_time_utc = datetime.utcfromtimestamp(submission_time).replace(tzinfo=timezone.utc)
        
        if one_day_ago <= submission_time_utc <= current_utc_time:
            recent_submissions.append({
                'title': submission.get('title'),
                'statusDisplay': submission.get('statusDisplay'),
                'timestamp': submission_time_utc.strftime('%Y-%m-%d %H:%M:%S')
            })
    return recent_submissions

def extract_daily_problem_info(daily_problem):
    problem_info = {
        "questionLink": daily_problem["questionLink"],
        "date": daily_problem["date"],
        "questionTitle": daily_problem["questionTitle"],
        "difficulty": daily_problem["difficulty"],
    }
    return problem_info

def get_profile(username):
    url = f"{BASE_URL}/{username}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get profile for {username}: {response.status_code}")
        return None

def get_accepted_submissions(username):
    url = f"{BASE_URL}/{username}/acSubmission"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get accepted submissions for {username}: {response.status_code}")
        return None

def get_daily_problem():
    url = f"{BASE_URL}/daily"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get daily problem: {response.status_code}")
        return None

def main(usernames, channel):
    daily_problem = get_daily_problem()
    if daily_problem:
        problem_info = extract_daily_problem_info(daily_problem)
        print(problem_info)
    else:
        print("No daily problem data available.")
        
    for username in usernames:
        profile = get_profile(username)
        if profile:
            print(f"Profile for {username}: {json.dumps(profile, indent=4)}")
        
            submissions = get_accepted_submissions(username)
            submission_list = submissions.get('submission', [])
        
            recent_ac_submissions = get_recent_24h_ac_submissions(submission_list)
            print(f"Recent 24-hour submissions for {username}: {recent_ac_submissions}")
            flag = False
            for ac_submission in recent_ac_submissions:
                if(ac_submission['title'] == problem_info['questionTitle']):
                    flag = True
                    return f"{username} finished daily challenge"
            if (not flag):
                return f"{username} not yet finish"
        

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    check_daily_challenge.start()

async def on_message(message):
    if message.author == bot.user:
        return
    if message.content == "hello":
        await message.channel.send("Hello!")

@tasks.loop(time=time(hour=9, tzinfo=taipei_tz))
async def check_daily_challenge():
    usernames = ["Your_user_name"]
    channel = bot.get_channel("Your_channel_ID")
    string = main(usernames, channel)
    await channel.send(string)

with open('token.txt', 'r') as file:
    token = file.read()
    
bot.run(token)
