import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import json
import pytz
from datetime import datetime, time
from leetcode_fn import get_user_daily_status, extract_daily_problem_info, get_daily_problem

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

taipei_tz = pytz.timezone('Asia/Taipei')
utc_tz = pytz.timezone('US/Pacific')

class LeetCodeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='/', intents=intents)
        
        self.user_data_file = 'user_data.json'

    async def setup_hook(self):
        self.check_daily_challenge_scheduled_tasks.start()

    def load_user_data(self):
        if not os.path.exists(self.user_data_file):
            return {}
        with open(self.user_data_file, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}

    def save_user_data(self, data):
        with open(self.user_data_file, 'w') as file:
            json.dump(data, file, indent=4)

    @commands.command(name='add_user')
    async def add_user(self, ctx, *usernames: str):
        user_data = self.load_user_data()
        added_users = []
        existing_users = []

        for username in usernames:
            if username in user_data:
                existing_users.append(username)
            else:
                user_data[username] = {'daily_completed': False}
                added_users.append(username)
        self.save_user_data(user_data)

        if added_users:
            await ctx.send(f'Users added: {", ".join(added_users)}.')
        if existing_users:
            await ctx.send(f'Users already exist: {", ".join(existing_users)}.')

    @commands.command(name='delete_user')
    async def delete_user(self, ctx, *usernames: str):
        user_data = self.load_user_data()
        deleted_users = []
        non_existent_users = []

        for username in usernames:
            if username in user_data:
                del user_data[username]
                deleted_users.append(username)
            else:
                non_existent_users.append(username)

        self.save_user_data(user_data)

        if deleted_users:
            await ctx.send(f'Users deleted: {", ".join(deleted_users)}.')
        if non_existent_users:
            await ctx.send(f'Users not found: {", ".join(non_existent_users)}.')

    @commands.command(name='usage')
    async def usage_print(self, ctx):
        usage_message = """
**LeetCode Daily Checker Bot Usage**
>
> This message is generated by OPENAI - GPT o1-preview
>

Here are the commands you can use with this bot:

- **`/add_user <username1> <username2> ...`**
  - Add one or more LeetCode usernames to the tracking list. The bot will monitor these users for daily challenge completion.
- **`/delete_user <username1> <username2> ...`**
  - Remove one or more LeetCode usernames from the tracking list.
- **`/check`**
  - Manually trigger the bot to check the daily challenge status of all tracked users and display the results.
- **`/usage`**
  - Display this help message with information about all available commands.

**Scheduled Checks**
- The bot automatically checks the daily challenge status of all tracked users at **11:50 PM Pacific Time (UTC-8)** every day and posts the results in this channel.

**Notes**
- Ensure you provide the correct LeetCode usernames when adding users.
"""
        await ctx.send(usage_message)

    @commands.command(name='check')
    async def check_daily_challenge(self, ctx):
        user_data = self.load_user_data()
        daily_problem = get_daily_problem()

        if not daily_problem:
            await ctx.send("No daily problem data available.")
            return

        daily_problem_info = extract_daily_problem_info(daily_problem)
        print(f"Daily problem info: {daily_problem_info}")

        finish_daily = []
        unfinish_daily = []
        await ctx.send(f"Daily problem: {daily_problem_info['questionTitle']} - Difficulty: {daily_problem_info['difficulty']}")
        print("Finished sending problem info")

        for username in user_data.keys():
            user_data[username]['daily_completed'] = get_user_daily_status(username, daily_problem_info)
            if user_data[username]['daily_completed']:
                finish_daily.append(username)
            else:
                unfinish_daily.append(username)

        await ctx.send(f'Users who finished the daily challenge: {", ".join(finish_daily)}.')
        await ctx.send(f'Users who have not finished the daily challenge: {", ".join(unfinish_daily)}.')

        self.save_user_data(user_data)

    @tasks.loop(time=time(hour=23, minute=55, tzinfo=utc_tz))
    async def check_daily_challenge_scheduled_tasks(self):
        user_data = self.load_user_data()
        daily_problem = get_daily_problem()
        if not daily_problem:
            print("No daily problem data available.")
            return

        daily_problem_info = extract_daily_problem_info(daily_problem)
        print(f"Daily problem info: {daily_problem_info}")

        channel = self.get_channel(CHANNEL_ID)
        finish_daily = []
        unfinish_daily = []
        if channel:
            await channel.send(f"{daily_problem_info['date']}\nDaily problem: {daily_problem_info['questionTitle']} - Difficulty: {daily_problem_info['difficulty']}")
            print("Finished sending problem info")

            for username in user_data.keys():
                user_data[username]['daily_completed'] = get_user_daily_status(username, daily_problem_info)
                if user_data[username]['daily_completed']:
                    finish_daily.append(username)
                else:
                    unfinish_daily.append(username)

            await channel.send(f'Users who finished the daily challenge: {", ".join(finish_daily)}\nUsers who have not finished the daily challenge: {", ".join(unfinish_daily)}')

        self.save_user_data(user_data)

    @check_daily_challenge_scheduled_tasks.before_loop
    async def before_check_daily_challenge_scheduled_tasks(self):
        await self.wait_until_ready()
        print("Starting the scheduled daily challenge check.")

    async def on_ready(self):
        print(f'{self.user.name} is online and ready!')

if __name__ == "__main__":
    leetcode_bot = LeetCodeBot()
    leetcode_bot.run(TOKEN)
