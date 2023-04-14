from discord.ext import commands

class Onboarding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        welcome_channel = guild.get_channel(969694127254016000)  # Replace with your welcome channel ID
        await welcome_channel.send(f"Welcome {member.mention}! Please check the #rules channel and introduce yourself!")

async def setup(bot):
    await bot.add_cog(Onboarding(bot))
