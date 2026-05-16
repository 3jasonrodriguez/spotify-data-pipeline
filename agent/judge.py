import anthropic
import json
import re
from dotenv import load_dotenv
from etl.utils.logger import get_logger
from etl.utils.connections import get_postgres_conn
from agent.judge_context import JUDGE_CONTEXT
logger = get_logger(__name__)
load_dotenv()
client = anthropic.Anthropic()

JUDGE_SQL_PROMPT = f"""
You are a PostgreSQL expert evaluating LLM-generated SQL...
You will serve to evaluate SQL before it is run on a Postgres database.
The database holds Spotify streaming data for users with users having their own schema using their first name. Each schema and is modeled with a fact table and dimensional tables.
The prior LLM call to produce this SQL outputs the statement, a natural language response to explain the analysis, and provides a little insight along with the results from the potential query.

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
-You will provide a score from 1-5 with 5 being the highest and indicating excellently formed, performant SQL. 1 would indicate the inverse, meaning the SQL does not align with the schema, doesn't answer the question, etc. 3 would represent that the SQL answers the question and is a valid answer but maybe could be written with better form or performant qualities but is still acceptable.
-You will provide a reasoning to provide feedback to the SQL and why it was scored the way it was scored with possible fixes to the SQL statement and how it can be better.
-You will provide short description flags for quick understanding of why the query was bad (e.g. incorrect columns, assumptions not stated, assumptions not followed, incorrect schema, ill-formed SQL )

Scoring:
-You will only approve the SQL if it is 3 or greater.
-The spectrum is a compilation of relevance, form, expected performance, compliance with SQL database principles and best practices.
-There are multiple ways to write SQL for a question - we want working and well-formed.
-Don't be too hard as this will be too much of a bottleneck.
-A lower score should be provided if it will likely continously loop over the data infinitely.
-There should not be unnecessary operations in the SQL (e.g. too many subqueries where they are not needed, try to display extra columns that provide value to the question)

Return ONLY a valid JSON object with no other text, preamble, or markdown code blocks.
Do not wrap in ```json``` tags.
Example JSON output:
{{
    "passed": True/False,
    "score": 1-5,
    "reasoning": "explanation",
    "flags": ["assumption not disclosed", ...]
}}

"""

#Used for writing the verdict to Postgres for feedback analysis
def log_eval(question: str, generated_sql: str, verdict: dict, user_scope: str = None):
    try:
        with get_postgres_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO public.llm_eval_log 
                    (question, generated_sql, passed, score, reasoning, flags, user_scope)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    question,
                    generated_sql,
                    verdict.get("passed"),
                    verdict.get("score"),
                    verdict.get("reasoning"),
                    verdict.get("flags"),
                    user_scope
                ))
            conn.commit()
    except Exception as e:
        logger.error(f"Error in evaluate(): {e}")

#LLM call to perform the evaluation of the SQL
def evaluate_sql(question: str, generated_sql: str, nl_response: str, user_scope: str = None) -> dict:
    try:
        messages = [{
            "role": "user",
            "content": f"""
            Question: {question}
            Generated SQL: {generated_sql}
            Natural Language Response: {nl_response}
            User Scope: {user_scope}
            Return your verdict as JSON only, no other text.
            """
        }]
        #Give the LLM the prompt and create the message
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=JUDGE_SQL_PROMPT,
            messages=messages
        )
        raw_text = response.content[0].text.strip()
        #strip markdown code blocks produced from LLM response if present
        if raw_text.startswith("```"):
            raw_text = re.sub(r'```json|```', '', raw_text).strip()
        verdict = json.loads(raw_text)
        # write to postgres
        log_eval(question, generated_sql, verdict, user_scope)
        return verdict

    except Exception as e:
        logger.error(f"Error in evaluate(): {e}")
        return {"passed": True, "score": None, "reasoning": "Eval failed", "flags": []}
    
JUDGE_DISCOVERY_PROMPT = f"""
You are a data analyst and quality reviewer evaluating AI-generated insights 
about Spotify listening data.

## Your Role
- Evaluate whether the insight is genuinely interesting or surprising
- Check if the follow-up question is relevant and would lead to more discovery
- Verify the chart spec is appropriate for the data being described. The data produced from your discovery should align with the data
- Ensure the insight is specific and data-driven, not generic
- Determine if the insight can actually be answered using the Spotify database and not additional external data sources.

## Chart Spec Validation
- Verify that the chart_spec x and y fields actually exist as column names in the data returned
- Verify that the chart_type is appropriate for the shape of the data
- If the chart_spec references columns that don't exist in the query results, flag it and fail the evaluation
- The raw_data fields and chart_spec must be consistent — a mismatch should result in a score of 2 or lower

Flag examples for chart mismatches:
- "chart_spec references column 'hour' but data only contains 'period_type', 'total_plays'"
- "chart_type is 'line' but data has no temporal or sequential column"


## Scoring
- 5: Genuinely surprising, specific, actionable insight
- 4: Interesting and relevant, minor improvements possible
- 3: Acceptable but somewhat generic or obvious
- 1-2: Generic, obvious, or not data-driven

Only approve scores of 2 and above.

## Database Schema
{JUDGE_CONTEXT}

Return ONLY a valid JSON verdict:
{{
    "passed": true/false,
    "score": 1-5,
    "reasoning": "explanation",
    "flags": ["generic insight", "irrelevant follow-up", ...]
}}
"""
#Used for writing the verdict to Postgres for feedback analysis
def discovery_eval_log(insight_text: str, follow_up_question: str, user_scope: str, verdict: dict):
    try:
        with get_postgres_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO public.discovery_eval_log 
                    (insight_text, follow_up_question, user_scope, passed, score, reasoning, flags)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    insight_text,
                    follow_up_question,
                    user_scope,
                    verdict.get("passed"),
                    verdict.get("score"),
                    verdict.get("reasoning"),
                    verdict.get("flags")
                ))
            conn.commit()
    except Exception as e:
        logger.error(f"Error in evaluate(): {e}")

#Judge whether a discovery meets the criteria, is valid, and interesting
def evaluate_discovery(insight_text: str, follow_up_question: str, chart_spec: dict, user_scope: str, query_result: str) -> dict:
    try:
        messages = [{
            "role": "user",
            "content": f"""
            User Scope: {user_scope}
            Insight Text: {insight_text}
            Follow up question: {follow_up_question}
            Chart Spec: {chart_spec}
            Query result: {query_result}
            Return your verdict as JSON only, no other text.
            """
        }]
        #Give the LLM the prompt and create the message
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=JUDGE_DISCOVERY_PROMPT,
            messages=messages
        )
        raw_text = response.content[0].text.strip()
        #strip markdown code blocks produced from LLM response if present
        if raw_text.startswith("```"):
            raw_text = re.sub(r'```json|```', '', raw_text).strip()
        verdict = json.loads(raw_text)
        # write to postgres
        discovery_eval_log(insight_text, follow_up_question, user_scope, verdict)
        return verdict
    except Exception as e:
        logger.error(f"Error in evaluate(): {e}")
        return {"passed": True, "score": None, "reasoning": "Eval failed", "flags": []}

#Log the approved discovery to postgres
def log_discovery(user_scope: str, insight_text: str, follow_up_question: str, chart_spec: dict, generated_sql: str, raw_data: dict ):
    try:
        with get_postgres_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO public.discoveries
                    (user_scope, insight_text, follow_up_question, chart_spec, generated_sql, raw_data)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    user_scope,
                    insight_text,
                    follow_up_question,
                    json.dumps(chart_spec) if chart_spec else None,
                    generated_sql,
                    raw_data if raw_data else None
                    
                ))
            conn.commit()
    except Exception as e:
        logger.error(f"Error logging discovery: {e}")