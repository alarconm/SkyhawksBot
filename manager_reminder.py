from discord.ext import tasks, commands
from datetime import datetime
import pytz

class ManagerReminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.send_daily_reminder.start()

    @tasks.loop(minutes=1)
    async def send_daily_reminder(self):
        print("Checking if it's time to send the reminder...")
        
        # Get the current time in UTC
        current_time = datetime.now(pytz.utc)
        
        # Convert the current time to Pacific Time
        pacific = pytz.timezone('US/Pacific')
        current_time_pacific = current_time.astimezone(pacific)

        if current_time_pacific.weekday() < 5 and current_time_pacific.hour == 17 and current_time_pacific.minute == 0:
            print("Sending the reminder...")
            reminder_channel = self.bot.get_channel(1095028295931801600)  # Replace with your reminder channel ID
            manager1 = await self.bot.fetch_user(969723496433340437)  # Replace with your first manager's ID
            manager2 = await self.bot.fetch_user(969704735953260604)  # Replace with your second manager's ID
            await reminder_channel.send(f"{manager1.mention} {manager2.mention} - Reminder to enter payroll notes for the day.")

    @send_daily_reminder.before_loop
    async def before_send_daily_reminder(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(ManagerReminder(bot))
