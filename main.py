import discord
from discord.ext import commands
from faq import fetch_gpt_answer_with_context
import glob, os
from discord.ui import Select, View
import openai
from discord import Embed
from poll import create_poll
from concurrent.futures import ThreadPoolExecutor
import asyncio
from asyncio import to_thread
from asyncio import Semaphore
import PyPDF2
from PyPDF2 import PdfReader
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
from pptx_generator import generate_pptx
import shutil
import whoosh
import random
import math
import scipy.stats as si
from scipy.stats import norm
from discord.ext import commands
import numpy as np


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
request_semaphore = Semaphore(1)

bot = commands.Bot(command_prefix='!', intents=intents, heartbeat_timeout=120.0)
openai.api_key = os.environ["OPENAI_API_KEY"]







def number_emoji(number):
    if 0 <= number <= 9:
        return f"{number}\u20E3"
    return str(number)

def get_pdf_list():
    pdf_files = glob.glob("pdfs/*.pdf")
    pdf_list = {}
    for i, pdf_file in enumerate(pdf_files):
        pdf_name = os.path.basename(pdf_file)[:-4]  # Remove '.pdf' from the file name
        pdf_list[number_emoji(i)] = pdf_name
    return pdf_list

pdf_list = get_pdf_list()

def create_pdf_description(pdf_list, start):
    pdf_items = list(pdf_list.items())
    pdf_description = "\n".join(f"{number_emoji(i % 10)} - {pdf}" for i, (emoji, pdf) in enumerate(pdf_items[start:start+10], start))
    return pdf_description

async def update_pdf_message(message, pdf_list, start):
    pdf_description = create_pdf_description(pdf_list, start)
    page_number = start // 10 + 1
    await message.edit(content=f"Page {page_number}\nSelect a PDF to download by reacting with the corresponding number:\n{pdf_description}")

async def send_embed(ctx, title, description, fields=None, thumbnail_url=None, author=None, footer=None):
    embed = Embed(title=title, description=description, color=0x3498db)
    
    if fields:
        for field in fields:
            embed.add_field(name=field["name"], value=field["value"], inline=field.get("inline", False))
            
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
        
    if author:
        embed.set_author(name=author.get("name", ""), icon_url=author.get("icon_url", ""))
        
    if footer:
        embed.set_footer(text=footer.get("text", ""), icon_url=footer.get("icon_url", ""))
        
    await ctx.send(embed=embed)

class PDFSelect(Select):
    def __init__(self, pdf_list):
        options = []
        for i, pdf in enumerate(pdf_list.values()):
            options.append(discord.SelectOption(label=pdf, value=str(i)))
        super().__init__(custom_id="pdf_select", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        index = int(self.values[0])
        pdf_name = list(pdf_list.values())[index]
        pdf_path = f'pdfs/{pdf_name}.pdf'

        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                pdf_file = discord.File(f, f'{pdf_name}.pdf')
                await interaction.response.send_message(f"Here is the {pdf_name} PDF you requested:", file=pdf_file, ephemeral=True)
        else:
            await interaction.response.send_message(f"Sorry, I could not find a PDF for '{pdf_name}'.", ephemeral=True)

@bot.event
async def on_ready():
    await load_manager_reminder_extension()
    await load_onboarding_extension()
    print(f'{bot.user.name} is connected to Discord!')

user_conversations = {}

def update_conversation_history(user_id, message):
    if user_id not in user_conversations:
        user_conversations[user_id] = []

    user_conversations[user_id].append(message)
    return user_conversations[user_id]

@bot.command()
async def faq(ctx, *, question):
    if not question:
        await ctx.send("Please provide a question after the !faq command.")
        return

    user_id = ctx.author.id
    update_conversation_history(user_id, question)
    conversation_history = "\n".join(user_conversations[user_id])

    context = (
        "You are a helpful all around company assistant that is set up as a Discord Bot that is an employee of Skyhawks Sports Academy Oregon."
        "Skyhawks Sports Academy is referred to in short as Skyhawks. We have a sister brand named Supertots."
        "Our company motto is teaching life skills through sports. You are an expert at building sports curriculum and coaching. You are an expert at providing helpful coaching tips, ideas, games, drills and other activities that our staff might find useful to run our sports camps."
        "We run summer camps June 20th - August 25th. Camps are Monday-Friday, 9-12pm for half day camps and 9-3pm for full day camps."
        "Skyhawks is the country's leader in providing a safe, fun, and skill-based sports experience for kids between the ages of 4 and 14."
        "Leadership team consists of: Mike Alarcon - Franchise Owner, Josh Kaiel - Franchise Owner, Tom Neri - Area Manager, Evan Ransom - Area Manager Sean MacPherson - Area Manager"
        "Company email address is: oregon@skyhawks.com."
        "Company phone number is: 503-894-6113"
        "Company website is Skyhawks.com"
        "You are a fan of all sports and have a strong passion for sports."
        "We are currently expanding into the after school enrichment market"
    )

    full_context = f"{conversation_history}\n{context}"
  
    await ctx.send("Please wait, fetching an answer from GPT-4...this may take a while.")

    async with ctx.typing():
        async with request_semaphore:
            answer = await fetch_gpt_answer_with_context(question, full_context)
        update_conversation_history(user_id, answer)

    if answer:
        await send_embed(ctx, "FAQ Answer", answer)
    else:
        await ctx.send('Sorry, I could not find an answer for that question.')


@bot.command(name='upload')
async def upload_pdf(ctx):
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if attachment.filename.endswith('.pdf'):
            file_path = f'pdfs/{attachment.filename}'
            await attachment.save(file_path)
            add_document_to_index(file_path)  # Add this line to index the uploaded PDF
            global pdf_list
            pdf_list = get_pdf_list()
            await ctx.send('PDF uploaded and indexed successfully.')
        else:
            await ctx.send('Invalid file type. Please upload a PDF file.')
    else:
        await ctx.send('No file attached. Please attach a PDF file to your message.')


@bot.command()
async def pdf(ctx):
    view = View()
    view.add_item(PDFSelect(pdf_list))
    await ctx.send("Select a PDF to download from the dropdown menu:", view=view)

async def load_manager_reminder_extension():
  await bot.load_extension("manager_reminder")

async def load_onboarding_extension():
  await bot.load_extension("onboarding")

# code_help command
@bot.command()
async def code_help(ctx, *, question):
    if not question:
        await ctx.send("Please provide a question after the !code_help command.")
        return

    user_id = ctx.author.id
    update_conversation_history(user_id, question)
    conversation_history = "\n".join(user_conversations[user_id])

    context = (
    "You are a world-class software engineer. You are particularly good at fixing bugs in code."
"Go line-by-line and do a detailed inspection of my code looking for bugs. If you see a bug, identify it. Explain what the bug is and provide a fix."
"Respond as a well-formatted markdown file that is organized into sections."
"Make sure to use code blocks."
"Inspect this code:"
    )

    full_context = f"{conversation_history}\n{context}"

    async with ctx.typing():
      async with request_semaphore:
        answer = await fetch_gpt_answer_with_context(question, full_context)
        update_conversation_history(user_id, answer)

    if answer:
        await send_embed(ctx, "Bug-fix Answer", answer)
    else:
        await ctx.send('Sorry, I could not find an answer for that question.')

@bot.command()
async def code_implement(ctx, *, question):
    if not question:
        await ctx.send("Please provide a question after the !faq command.")
        return

    user_id = ctx.author.id
    update_conversation_history(user_id, question)
    conversation_history = "\n".join(user_conversations[user_id])

    context = (
    "You are a world-class software engineer. You are particularly skilled at updating code to meet specific requests."
    "I need code that does the following:"
    "Generate the code for me."
    "Respond as a markdown code block."
    )

    full_context = f"{conversation_history}\n{context}"

    async with ctx.typing():
      async with request_semaphore:
        answer = await fetch_gpt_answer_with_context(question, full_context)
        update_conversation_history(user_id, answer)

    if answer:
        await send_embed(ctx, "Implementation Answer", answer)
    else:
        await ctx.send('Sorry, I could not find an answer for that question.')

@bot.command()
async def poll_help(ctx):
    embed = discord.Embed(
        title="Poll Help",
        description=(
            "To create a poll, use the `!poll` command followed by the poll title and options separated by spaces. "
            "Enclose multi-word options in double quotes. For example:\n"
            "`!poll \"Favorite Color\" Red \"Light Blue\" Green`\n\n"
            "To participate in a poll, select an option from the dropdown menu. "
            "To view the poll results, click the 'View Poll Results' button."
        ),
        color=0x3498db,
    )
    await ctx.send(embed=embed)
  
async def send_gpt_answer(ctx, user_id, question, full_context):
    # Send an initial message to inform the user that their request is being processed
    await ctx.send("Please wait, fetching an answer from GPT-4...")

    async with ctx.typing():
      async with request_semaphore:
        answer = await fetch_gpt_answer_with_context(question, full_context)
        update_conversation_history(user_id, answer)

    if answer:
        await send_embed(ctx, "FAQ Answer", answer)
    else:
        await ctx.send('Sorry, I could not find an answer for that question.')

@bot.command(name='search')
async def search(ctx, *, query):
    if not query:
        await ctx.send("Please provide a query after the !search command.")
        return

    await ctx.send("Searching indexed PDFs...")
    async with ctx.typing():
        results = search_index(query)

    if results:
        result_str = "\n".join([f"{i+1}. {title} (score: {score:.2f})" for i, (title, score) in enumerate(results)])
        await send_embed(ctx, "Search Results", result_str)
    else:
        await ctx.send("No results found.")


def create_search_index():
    schema = Schema(title=TEXT(stored=True), content=TEXT)
    if not os.path.exists("indexdir"):
        os.mkdir("indexdir")
    return create_in("indexdir", schema)

def add_document_to_index(file_path):
    if not os.path.exists("indexdir"):
        os.mkdir("indexdir")
        index = create_search_index()
    else:
        try:
            index = open_dir("indexdir")
        except whoosh.index.EmptyIndexError:  
            index = create_search_index()

    with open(file_path, "rb") as file:
        pdf = PdfReader(file)  # Replace PdfFileReader with PdfReader
        content = ""
        for page in range(len(pdf.pages)):  # Replace pdf.numPages with len(pdf.pages)
            content += pdf.pages[page].extract_text()  # Replace pdf.getPage(page).extractText() with pdf.pages[page].extract_text()
    writer = index.writer()
    writer.add_document(title=os.path.basename(file_path), content=content)
    writer.commit()

def search_index(query):
    index = open_dir("indexdir")
    with index.searcher() as searcher:
        parser = QueryParser("content", index.schema)
        parsed_query = parser.parse(query)
        results = searcher.search(parsed_query, limit=None)
        return [(r['title'], r.score) for r in results]

def index_files():
    for pdf_file in glob.glob("pdfs/*.pdf"):
        add_document_to_index(pdf_file)

@bot.command(name='pdfchat')
async def pdfchat(ctx, *, query):
    if not query:
        await ctx.send("Please provide a query after the !pdfchat command.")
        return

    await ctx.send("Searching indexed PDFs and generating a response...")
    async with ctx.typing():
        search_results = search_qa_index(query)
        if search_results:
            top_results = search_results[:3]
            answer = await generate_gpt4_answer(query, top_results)
            await ctx.send(answer)
        else:
            await ctx.send("No results found.")

@bot.command()
async def ppt(ctx, *, prompt: str = ""):
    if not prompt:
        await ctx.send("Please provide a prompt after the !ppt command.")
        return

    try:
        # Generate the text using GPT-4
        context = (
            "You are an AI language model designed to generate PowerPoint presentations based on the user's input. "
            "Your goal is to create informative and engaging slides that communicate the main ideas effectively. "
            "For each slide, focus on one key point or topic and use concise, clear language. "
            "Consider using bullet points, short phrases, or sentences to make the content easy to read and understand. "
            "You may also suggest visual elements like charts, graphs, or images if they help illustrate the point more effectively. "
            "\nExample Input: Create a PowerPoint presentation on the benefits of exercise."
            "\nExample Output: [Slide 1: Benefits of Exercise, "
            "Slide 2: Improves Cardiovascular Health, "
            "Slide 3: Strengthens Muscles and Bones, "
            "Slide 4: Boosts Mood and Mental Health, "
            "Slide 5: Aids in Weight Management, "
            "Slide 6: Enhances Sleep Quality]."
            "\nNow, based on the user's input, generate a list of slide titles and content for a PowerPoint presentation:"
        )


        await ctx.send("Please wait, fetching an answer from GPT-4 and generating a PowerPoint slide...this may take a while.")
        async with ctx.typing():
            generated_text = await fetch_gpt_answer_with_context(prompt, context)

            # Generate the PowerPoint presentation
            pptx_filename = generate_pptx(generated_text)

        # Send the generated PowerPoint file to the user
        with open(pptx_filename, "rb") as file:
            await ctx.send("Here is your generated PowerPoint presentation:", file=discord.File(file, "generated_presentation.pptx"))
    except Exception as e:
        await ctx.send(f"An error occurred while generating the PowerPoint presentation: {str(e)}")


class PollView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Select(placeholder="Choose an option", options=options, custom_id="poll_select"))

    async def on_select(self, interaction, select: discord.ui.Select):
        await interaction.response.send_message(f"You selected {select.values[0]}", ephemeral=True)

@bot.command()
async def poll(ctx, title: str, *options: str):
    if not options or len(options) < 2:
        await ctx.send("Please provide at least two options for the poll.")
        return

    if len(options) > 25:
        await ctx.send("Please provide no more than 25 options for the poll.")
        return

    select_options = [discord.SelectOption(label=option) for option in options]
    view = PollView(select_options)
    embed = discord.Embed(title=title, description="Select an option from the dropdown menu")
    await ctx.send(embed=embed, view=view)


# os.makedirs("indexdir", exist_ok=True)
# os.makedirs("qa_indexdir", exist_ok=True)
# index_files()
# index_qa_files()
bot.run(os.environ["DISCORD_TOKEN"])

