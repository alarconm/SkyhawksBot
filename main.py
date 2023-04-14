import discord
from discord.ext import commands
import os
from faq import fetch_answer_with_context

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    await load_manager_reminder_extension()
    await load_onboarding_extension()
    print(f'{bot.user.name} is connected to Discord!')

@bot.command()
async def faq(ctx, *, question):
    answer = await fetch_answer_with_context(question)
    if question is None:
        await ctx.send("Please provide a question after the !faq command.")
        return
    if answer:
        await ctx.send(answer)
    else:
        await ctx.send('Sorry, I could not find an answer for that question.')

async def load_manager_reminder_extension():
    await bot.load_extension("manager_reminder")

async def load_onboarding_extension():
    await bot.load_extension("onboarding")

# Run the bot with your DISCORD_TOKEN
bot.run(os.environ["DISCORD_TOKEN"])
