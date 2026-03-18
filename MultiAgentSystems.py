#Import necessary libraries

import os
import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain_core.tools import Tool
from langchain_experimental.utilities import PythonREPL
#load virtual env

load_dotenv()

#Connect to MCP Server

MCP=MultiServerMCPClient({
    "my-sql server":{
        "command":"cmd",
        "transport":"stdio",
        "args":[
            "/c",
            f"set MYSQL_USER={os.getenv("MYSQL_USER")}& "
            f"set MYSQL_DATABASE={os.getenv("MYSQL_DATABASE")}& "
            f"set MYSQL_PASSWORD={os.getenv("MYSQL_PASSWORD")}&"
            f"npx -y @marcelo-ochoa/server-mysql mysql://localhost:3306/{os.getenv("MYSQL_DATABASE")}"
        ]
    }
})

#Build Repl_tool
plot_tool=Tool(name="plot_tool",func=PythonREPL().run,description="A Python shell. Use this to execute python commands to create plots and charts with matplotlib.")


# Build Agent
#List down the tools
async def dbagent():
    print("\nConnecting to MCP Server\n")
    sql_tools = await MCP.get_tools()

    #Connect to LLM
    print("\nConnecting to LLM\n")
    model=ChatOllama(model="llama3.2:3b",temperature=0)

    #Initiate Agent
    sql_Agent=create_agent(model=model,tools=sql_tools,system_prompt="You are a SQL expert. Follow these steps EXACTLY:\n"
        "1. Use the tools to find the table schema.\n"
        "2. Generate a valid SQL query.\n"
        "3. EXECUTE the query using the provided tools. Do not guess results.\n"
        "4. Once you have the data, summarize it in plain English.")
    
    plot_Agent=create_agent(model=model,tools=[plot_tool],system_prompt="You are Data Visualizer. Use plot_tool to plot the charts." \
                                            "Always save the file as file named 'Chart.png' and tell the user file is ready")

    print("\nConnecting to Agent\n")
    Chat =await sql_Agent.ainvoke({"messages":[("user","What is sum of Totalprice in orders table?")]})
    print("\nConnected to Agent Successfully, Querying Database\n")
    print("\n--Response--\n")
    query_results=Chat["messages"][-1].content
    print(query_results)

    plot=await plot_Agent.ainvoke({"messages":[("user","Use the data given by {query_results}.\n "
                                                f"and plot chart using matplotlib and save it in exclusive path {os.getenv("CHART_SAVE_APTH")}")]})

    print(plot["messages"][-1].content)
    print("Chart Saved Successfully..!!")


if __name__=="__main__":
    asyncio.run(dbagent())