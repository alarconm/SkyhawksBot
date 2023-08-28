import asyncio
import requests
from requests.exceptions import ConnectionError
from concurrent.futures import ThreadPoolExecutor
import os
from pptx_generator import generate_pptx
# from pdfchat import search_qa_index, index_qa_files


executor = ThreadPoolExecutor()

async def fetch_gpt_answer(full_context, n=1, max_retries=5, backoff_factor=3):
    api_key = os.environ["OPENAI_API_KEY"]
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {
        "model": "gpt-4",
        "messages": full_context,
        "max_tokens": 500,
        "n": n,
        "stop": None,
        "temperature": 0.7,
    }
    url = "https://api.openai.com/v1/chat/completions"

    for i in range(max_retries):
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: requests.post(url, headers=headers, json=data)
            )
            response.raise_for_status()
            response_data = response.json()
            answers = [choice['message']['content'].strip() for choice in response_data['choices']]  # Update this line
            return answers if n > 1 else answers[0]
        except ConnectionError as e:
            if i < max_retries - 1:
                wait_time = backoff_factor * (2 ** i)
                print(f"ConnectionError: Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                raise e

async def fetch_gpt_answer_with_context(question, context):
    messages = [{"role": "system", "content": context},
                {"role": "user", "content": question}]
    answer = await fetch_gpt_answer(messages)
    return answer

