import anthropic
import json
from dotenv import load_dotenv
from etl.utils.logger import get_logger
from agent.judge_context import JUDGE_CONTEXT
logger = get_logger(__name__)
load_dotenv()
client = anthropic.Anthropic()

JUDGE_SYSTEM_PROMPT = f"""
You are a PostgreSQL expert evaluating LLM-generated SQL...
You will serve to evaluate SQL before it is run on a Postgres database.
The database holds Spotify streaming data for users and is modeled with a fact table and dimensional tables.
The prior LLM call to produce this SQL outputs the statement, and a natural language response to explain the analysis and provide a little insight along with the results from the potential query.

## Database Schema
{JUDGE_CONTEXT}

Roles:
-judging SQL to see if it aligns with the schema, is correct, and not totally irrelevant to the question or database
-seeing if the SQL generated is performant to streamline the execution
-determine if the natural language response also provided with the SQL is relevant, accurate, complimentary, and a good contextual fit for the question and answer.
-check if assumptions were stated and followed
-look to see if the result looks reasonable and not empty or full of random irrelevant text
-verify the table names, schema names, and column names are valid and applicable to the answer.
-evaluate the joins and conditional statements
-review the data types used

Inputs:
-the original question asked by the user
-the generated SQL
-the natural language response explaining the analysis of the question prompted.

Outputs:
-You will give a pass/fail boolean to determine if the SQL passes your evaluation and correctlys answers the question
-You will provide a score from 1-5 with 5 being the highest and indicating excellently formed, performant SQL. 1 would indicate the inverse, meaning the SQL does not align with the schema, doesn't answer the question, etc.
-You will provide a reasoning to provide feedback to the SQL and why it was scored the way it was scored with possible fixes to the SQL statement and how it can be better.
-You will provide short description flags for quick understanding of why the query was bad (e.g. incorrect columns, assumptions not stated, assumptions not followed, incorrect schema, ill-formed SQL )

Scoring:
-You will only approve the SQL if it is scored 4 or 5.
-The spectrum is a compilation of relevance, form, expected performance, compliance with SQL database principles and best practices.
-There are multiple ways to write SQL for a question - we want working and well-formed.
-Don't be too hard as this will be too much of a bottleneck.
-A lower score should be provided if it will likely continously loop over the data infinitely.
-There should not be unnecessary operations in the SQL (e.g. too many subqueries where they are not needed, try to display extra columns that provide value to the question)
-
Example JSON output:
{
    "passed": True/False,
    "score": 1-5,
    "reasoning": "explanation",
    "flags": ["assumption not disclosed", "possible wrong filter", ...]
}

"""
def evaluate(question: str, generated_sql: str, nl_response: str) -> dict:
    try:
        messages = [{
            "role": "user",
            "content": f"""
            Question: {question}
            Generated SQL: {generated_sql}
            Natural Language Response: {nl_response}
            Return your verdict as JSON only, no other text.
            """
        }]

        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=JUDGE_SYSTEM_PROMPT,
            messages=messages
        )

        verdict = json.loads(response.content[0].text)
        
        # write to postgres
        log_eval(question, generated_sql, verdict)
        
        return verdict

    except Exception as e:
        logger.error(f"Error in evaluate(): {e}")
        return {"passed": True, "score": None, "reasoning": "Eval failed", "flags": []}