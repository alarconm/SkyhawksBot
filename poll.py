import discord
from discord.ui import Select, View, Button

class PollSelect(Select):
    def __init__(self, poll_options, results_button, poll_message):
        self.results_button = results_button
        self.poll_message = poll_message
        options = [discord.SelectOption(label=option, value=option) for option in poll_options]
        super().__init__(custom_id="poll_select", options=options, min_values=1, max_values=1, placeholder="Select your vote")

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        selected_option = self.values[0]

        if user_id in self.results_button.voters:
            await interaction.response.send_message("You have already voted in this poll.", ephemeral=True)
        else:
            self.results_button.vote_counts[selected_option] += 1
            self.results_button.voters.add(user_id)
            await interaction.response.send_message(f"You selected: {selected_option}", ephemeral=True)

            # Update the poll message with the new results
            results = "\n".join(f"{option}: {self.results_button.vote_counts[option]} votes" for option in self.results_button.poll_options)
            await self.poll_message.edit(content=f"**Poll Results:**\n\n{results}")

class PollResultsButton(Button):
    def __init__(self, poll_options):
        self.poll_options = poll_options
        self.vote_counts = {option: 0 for option in poll_options}
        self.voters = set()
        super().__init__(label="View Poll Results", custom_id="poll_results", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        results = "\n".join(f"{option}: {self.vote_counts[option]} votes" for option in self.poll_options)
        await interaction.response.send_message(f"**Poll Results:**\n\n{results}", ephemeral=True)

class PollButton(Button):
    def __init__(self, label, results_button, poll_message):
        self.results_button = results_button
        self.poll_message = poll_message
        super().__init__(label=label, custom_id=f"poll_option_{label}", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        selected_option = self.label

        if user_id in self.results_button.voters:
            await interaction.response.send_message("You have already voted in this poll.", ephemeral=True)
        else:
            self.results_button.vote_counts[selected_option] += 1
            self.results_button.voters.add(user_id)
            await interaction.response.send_message(f"You selected: {selected_option}", ephemeral=True)

            # Update the poll message with the new results
            results = "\n".join(f"{option}: {self.results_button.vote_counts[option]} votes" for option in self.results_button.poll_options)
            await self.poll_message.edit(content=f"**Poll Results:**\n\n{results}")



async def create_poll(ctx, title, poll_options):
    poll_view = View()
    results_button = PollResultsButton(poll_options)

    for option in poll_options:
        poll_button = PollButton(option, results_button, None)
        poll_view.add_item(poll_button)

    poll_view.add_item(results_button)
    poll_message = await ctx.send(f"**{title}**\n\nSelect your vote from the buttons below:", view=poll_view)

    for item in poll_view.children:
        if isinstance(item, PollButton):
            item.poll_message = poll_message

