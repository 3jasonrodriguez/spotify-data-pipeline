# test_api.py
from dotenv import load_dotenv
load_dotenv()
import re
import json
import anthropic
from agent.system_prompt import get_system_prompt
from agent.mcp_server import execute_sql

client = anthropic.Anthropic()
#Define tools that can be executed to the API
TOOLS = [
    {
        "name": "execute_sql",
        "description": "Execute a SQL query against the Spotify analytics postgres database.",
        "input_schema": {
            "type": "object",
            "properties":{
                "query": {
                    "type":"string",
                    "description":"The SQL SELECT query to execute in Postgres"
                }
            },
            "required":["query"]
        }
    }
]
#Holds the conversation in messages
messages = [
        {"role": "user", "content": "Who are my top 5 most played artists?"}
    ]
#Prompt will use the user context given
#The TOOLS info will be passed to Claude to show what tools are available
response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    system=get_system_prompt("Jason"),
    tools=TOOLS,
    messages=messages
)
#Grab the tool use block in the response with the generated query
tool_use = next(b for b in response.content if b.type=="tool_use")
produced_query = tool_use.input.get('query')

#MCP server executes the queryand returns the postgres result
query_result = execute_sql(produced_query)

#Append the response to the initial user's question
messages.append({"role": "assistant", "content": response.content})
#Append the query's result from postgres to messages
messages.append({
    "role": "user",
    "content": [{
        "type": "tool_result",
        "tool_use_id": tool_use.id,
        "content": query_result
    }]
})
#Get final response of answers with suggested chart type
final_response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    system=get_system_prompt("Jason"),
    tools=TOOLS,
    messages=messages
)
final_text = final_response.content[0].text
#Search for a chart recommended
match = re.search(r'<chart>(.*?)</chart>', final_text, re.DOTALL)
#Clean text short response only - excludes the chart tagged block
clean_text = re.sub(r'<chart>.*?</chart>', '', final_text, flags=re.DOTALL).strip()
#If a chart response is found, grab the contents within the tags and turn into a dict
if match:
    chart_spec = json.loads(match.group(1).strip())
print(chart_spec)