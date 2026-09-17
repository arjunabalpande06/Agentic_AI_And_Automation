import os
from openai import OpenAI
from IPython.display import Markdown, display
from dotenv import load_dotenv
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_BASE_URL"] = "https://api.groq.com/openai/v1"

os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "true"

openai_client = OpenAI(api_key=openai_api_key, base_url="https://api.groq.com/openai/v1")
print("Groq client successfully configured via OpenAI interface.")
print(openai_api_key[:5])

def print_markdown(text):
    try:
        get_ipython()
        display(Markdown(text))
    except NameError:
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode('ascii','replace').decode('ascii'))

from agents import Agent
fact_checker_instructions = """
Context:
You are a fact-checker who verifies the accuracy of statements.

Instructions:
When given a statement, carefully analyze its factual accuracy using your knowledge.

Input:
You will receive a statement that requires fact-checking.

Output:
Respond with:
1. A verdict prefix: either "✅ TRUE:" or "❌ FALSE:"
2. A brief, one-sentence explanation justifying your conclusion
"""
# Create a new agent called "Fact Checker"
fact_checker_agent = Agent(name = "Fact Checker",   # Name of the agent
                           instructions = fact_checker_instructions, # The rules and behavior for the agent
                           model = "llama-3.3-70b-versatile") # The AI model (LLM) to use

# Print a confirmation message that the agent was created
print(f"Agent '{fact_checker_agent.name}' created successfully!")
from agents import Runner

import asyncio

async def main():
    # A statement we want the Fact Checker agent to verify
    statement = "The Great Wall of China is visible from space with the naked eye."

    # Display the statement we're going to check (in markdown format for nicer formatting)
    print_markdown(f"Asking the Fact Checker to verify: '{statement}'")

    # Run the Fact Checker agent on the input statement
    # 'await' is used because running the agent is an asynchronous operation (it might take time)
    response = await Runner.run(
        starting_agent = fact_checker_agent,  # The agent we created earlier
        input = statement                 # The statement we want it to fact-check
    )

    # Display the agent's response
    print_markdown("\n🤖 Agent's Response:\n")
    print_markdown(response.final_output)    # Shows the final verdict and explanation

if __name__ == "__main__":
    asyncio.run(main())