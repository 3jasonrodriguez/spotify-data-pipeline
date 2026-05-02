import sqlfluff
from etl.utils.logger import get_logger
logger = get_logger(__name__)

def validate_sql(query: str) -> dict:
    result = sqlfluff.lint(query, dialect="ansi")
    violations = [
        {
            "code": v.get("code"),
            "description": v.get("description"),
            "line": v.get("start_line_no")
        }
        for v in result
    ]
    if violations:
        for v in violations:
            logger.warning(f"SQL violation [{v['code']}] line {v['line']}: {v['description']}")
        return {"valid": False, "violations": violations}
    return {"valid": True, "violations": []}

if __name__ == "__main__":
    test_query = """
    SELECT artist_name COUNT(play_key) as play_count
    FROM jason.fact_play_event
    """
    result = sqlfluff.lint(test_query, dialect="ansi")
    print(f"Raw result: {result}")
    print(f"Type: {type(result)}")
    print(f"Length: {len(result)}")