# Tavily Code

#pip show langchain
#pip show langchain-core
#pip show langchain-community
#pip show langchain-tavily
#pip show tavily-pythonpip lis

from tavily import TavilyClient
from langchain_core.tools import Tool

client = TavilyClient(api_key="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")

def search_web(query: str):
    return client.search(query=query, max_results=3)

tavily_tool = Tool(
    name="Tavily Search",
    func=search_web,
    description="Search the web for current information."
)

print(tavily_tool.invoke("Who is leo messi?"))