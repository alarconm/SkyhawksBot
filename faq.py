import openai
import os

# Set up OpenAI API
openai.api_key = os.environ["OPENAI_API_KEY"]

async def fetch_gpt_answer(prompt, n=1):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=500,
        n=n,
        stop=None,
        temperature=0.7,
    )
    answers = [choice.text.strip() for choice in response.choices]
    return answers if n > 1 else answers[0]

async def fetch_answer_with_context(question):
    context = (
        "Skyhawks Sports Academy Oregon is the franchise company of MM&MK Corp"
        "Leadership team consists of: Mike Alarcon - Franchise Owner, Josh Kaiel - Franchise Owner, Tom Neri - Area Manager, Evan Ransom - Area Manager"
        "Company email address is: oregon@skyhawks.com"
        "Company phone number is: 503-894-6113"
        "Paydays are every other Friday, and the upcoming paydays are: "
        "April 14th, 2023; April 28th, 2023, and so on."
    )

    prompt = f"Given the following context: '{context}', answer the question: '{question}'"
    answer = await fetch_gpt_answer(prompt)
    return answer
