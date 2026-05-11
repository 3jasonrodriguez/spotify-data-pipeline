import re
import json
import anthropic
from agent.system_prompt import get_system_prompt
from agent.judge import evaluate_sql, evaluate_discovery, log_discovery
from agent.db_tools import execute_sql
from etl.utils.logger import get_logger 
from agent.discoveries_prompt import get_discoveries_prompt
from etl.utils.connections import get_postgres_conn
from dotenv import load_dotenv
load_dotenv()
logger = get_logger(__name__)
#Define tools available for Claude to use
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

def parse_json_response(text: str) -> dict:
    """Extract JSON from LLM response regardless of surrounding text or markdown."""
    raw = re.sub(r'```json|```', '', text).strip()
    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    raise ValueError("No JSON found in LLM response")


def get_cached_sql(question: str, user_scope: str) -> dict | None:
    try:
        with get_postgres_conn() as conn:
            with conn.cursor() as cursor:
                # extract keywords from question
                keywords = question.split()
                # build ILIKE pattern from first few meaningful words
                pattern = f"%{' '.join(keywords[:4])}%"
                
                cursor.execute("""
                    SELECT generated_sql, score, question
                    FROM public.llm_eval_log
                    WHERE passed = true
                    AND score >= 4
                    AND user_scope = %s
                    AND question ILIKE %s
                    ORDER BY score DESC, evaluated_at DESC
                    LIMIT 1
                """, (user_scope, pattern))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "generated_sql": row[0],
                        "score": row[1],
                        "question": row[2]
                    }
                return None
    except Exception as e:
        logger.error(f"Error fetching cached SQL: {e}")
        return None

client = anthropic.Anthropic()
#Function for prompting analysis questions
def ask(question: str, user_scope: str) -> dict:
    try:
        chart_spec = None
        produced_query = None
        query_result = None
        # before building messages, check for prior answer to a question for a hint at the sql to execute
        cached = get_cached_sql(question, user_scope)
        if cached:
            enhanced_question = f"""{question}

        Hint: A similar question was previously answered successfully with this SQL (score {cached['score']}/5):
        {cached['generated_sql']}

        Use this as a starting point if appropriate."""
        else:
            enhanced_question = question

        messages = [{"role": "user", "content": enhanced_question}]
        # agentic loop - keeps going until LLM says end_turn
        while True:
            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1024,
                system=get_system_prompt(user_scope),
                tools=TOOLS,
                messages=messages
            )
            if response.stop_reason == "tool_use":
                tool_use = next(b for b in response.content if b.type == "tool_use")
                produced_query = tool_use.input.get('query')
                query_result = execute_sql(produced_query)

                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": query_result
                    }]
                })

            elif response.stop_reason == "end_turn":
                final_text = next(b.text for b in response.content if hasattr(b, "text"))
                
                # parse response type first
                type_match = re.search(r'<response_type>(.*?)</response_type>', final_text, re.DOTALL)
                response_type = type_match.group(1).strip() if type_match else "data"
                clean_text = re.sub(r'<response_type>.*?</response_type>', '', final_text, flags=re.DOTALL).strip()
                clean_text = re.sub(r'<chart>.*?</chart>', '', clean_text, flags=re.DOTALL).strip()
                #parse for chart
                match = re.search(r'<chart>(.*?)</chart>', final_text, re.DOTALL)
                if match:
                    chart_spec = parse_json_response(match.group(1))
                    # validate chart spec columns match raw data
                    if chart_spec and query_result:
                        import json
                        raw_data = json.loads(query_result)
                        if raw_data:
                            actual_columns = list(raw_data[0].keys())
                            x_col = chart_spec.get('x')
                            y_col = chart_spec.get('y')
                            if x_col not in actual_columns or y_col not in actual_columns:
                                logger.warning(f"Chart spec mismatch — x:{x_col} y:{y_col} not in {actual_columns}")
                                #discard invalid chart spec
                                chart_spec = None  
                # only judge if it's a data response
                if response_type == "data":
                    verdict = evaluate_sql(question, produced_query, clean_text, user_scope)
                else:
                    verdict = {"passed": True, "score": None, "reasoning": "Non-data response", "flags": []}
                
                break

    except Exception as e:
        logger.error(f"Error in ask(): {e}")
        return {"raw_data": None, "natural_language_response": f"Error: {str(e)}", "chart_spec": None}

    return {"raw_data": query_result, "natural_language_response": clean_text, "chart_spec": chart_spec, "generated_sql": produced_query, "verdict": verdict, "response_type":response_type}

def discover(user_scope: str) -> dict:
    logger.info(f"Starting discovery generation for scope: {user_scope}")
    try:
        insight_text = None
        follow_up_question = None
        chart_spec = None
        messages = [{
            "role": "user",
            "content": f"Generate one interesting insight about the Spotify data for scope: {user_scope}"
        }]
        # agentic loop - keeps going until LLM says end_turn
        while True:
            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=2048,
                system=get_discoveries_prompt(user_scope),
                tools=TOOLS, # not sure I need this
                messages=messages
            )
            if response.stop_reason == "tool_use":
                tool_use = next(b for b in response.content if b.type == "tool_use")
                produced_query = tool_use.input.get('query')
                query_result = execute_sql(produced_query)

                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": query_result
                    }]
                })
            elif response.stop_reason == "end_turn":
                final_text = next(b.text for b in response.content if hasattr(b, "text"))
                parsed = parse_json_response(final_text)
                insight_text = parsed.get("insight_text")
                follow_up_question = parsed.get("follow_up_question")
                chart_spec = parsed.get("chart_spec")
                
                logger.info(f"Discovery generated for {user_scope}: {insight_text[:100] if insight_text else 'None'}...")
                
                # chart spec validation
                if chart_spec and query_result:
                    ...
                    logger.info(f"Chart spec valid: {chart_spec.get('chart_type')} x={chart_spec.get('x')} y={chart_spec.get('y')}")
                
                verdict = evaluate_discovery(insight_text, follow_up_question, chart_spec, user_scope)
                logger.info(f"Judge verdict for {user_scope}: passed={verdict.get('passed')} score={verdict.get('score')}")
                
                if verdict.get("passed"):
                    log_discovery(user_scope, insight_text, follow_up_question, chart_spec, produced_query, query_result)
                    logger.info(f"Discovery written to postgres for {user_scope}")
                else:
                    logger.warning(f"Discovery failed judge for {user_scope}: {verdict.get('flags')}")
                break
    except Exception as e:
        logger.error(f"Error in discover() for {user_scope}: {e}")
        return {"insight_text": None, "follow_up_question": None, "chart_spec": None, "user_scope": None}
    return {"insight_text": insight_text, "follow_up_question": follow_up_question, "chart_spec": chart_spec, "user_scope":user_scope}
