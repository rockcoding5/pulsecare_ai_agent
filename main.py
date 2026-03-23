import os
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = Flask(__name__)

# -------------------------------
# 🔧 Config
# -------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
API_KEY = os.getenv("GEMINI_API_KEY")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
genai_client = genai.Client(api_key=API_KEY)


# -------------------------------
# 🧠 Utility: Format SQL
# -------------------------------
def format_sql(sql_query):
    return sql_query.replace("\n", "\n")


# -------------------------------
# 🧠 NL → SQL Generator
# -------------------------------
def generate_sql(user_query):
    prompt = f"""
    You are a PostgreSQL expert.

    Table: health_anomalies
    Columns:
    description, severity, device_source, detected_at

    RULES:
    - Only SELECT queries
    - Do NOT modify data
    - LIMIT 10
    - NEVER use SELECT *
    - severity values: 'Critical', 'Medium', 'Low'

    Convert this natural language query into SQL:
    "{user_query}"

    Return only SQL.
    """

    response = genai_client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt
    )

    return response.text.strip()


# -------------------------------
# 🔹 NL → SQL Execution
# -------------------------------
def run_nl_query(user_query):
    sql_query = generate_sql(user_query)

    if not sql_query.lower().startswith("select"):
        return {"error": "Invalid SQL generated", "sql": sql_query}

    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            rows = [dict(row._mapping) for row in result]

        return {
            "agent": "PulseCare AI Agent",
            "mode": "nl-to-sql",
            "sql": format_sql(sql_query),
            "count": len(rows),
            "results": rows,
            "insight": f"{len(rows)} anomaly record(s) retrieved using NL → SQL."
        }

    except Exception as e:
        return {"error": str(e), "sql": sql_query}


@app.route('/nl-query', methods=['POST'])
def nl_query():
    user_query = request.json.get("query", "")
    return jsonify(run_nl_query(user_query))


# -------------------------------
# 🔹 Semantic Vector Search
# -------------------------------
def run_semantic_query(user_query):
    query = text("""
        SELECT description, severity, device_source, detected_at,
               1 - (finding_vector <=> embedding('text-embedding-005', :q)::vector) AS score
        FROM health_anomalies
        WHERE 1 - (finding_vector <=> embedding('text-embedding-005', :q)::vector) > 0.6
        ORDER BY score DESC
        LIMIT 5;
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"q": user_query})

        rows = [
            {
                "description": r[0],
                "severity": r[1],
                "device": r[2],
                "time": str(r[3]),
                "score": round(r[4], 2)
            }
            for r in result
        ]

    return {
        "agent": "PulseCare AI Agent",
        "mode": "semantic",
        "count": len(rows),
        "results": rows,
        "insight": f"{len(rows)} results using vector similarity."
    }


@app.route('/semantic-query', methods=['POST'])
def semantic_query():
    user_query = request.json.get("query", "")
    return jsonify(run_semantic_query(user_query))


# -------------------------------
# 🔥 AlloyDB Native AI (MAIN)
# -------------------------------
def run_alloydb_ai_query(user_query):
    print(f"🔥 [PulseCare] Received query: {user_query}")

    query = text("""
        SELECT description, severity, device_source, detected_at,
               1 - (finding_vector <=> embedding('text-embedding-005', :q)::vector) AS score
        FROM health_anomalies
        WHERE finding_vector IS NOT NULL
          AND 1 - (finding_vector <=> embedding('text-embedding-005', :q)::vector) > 0.5
          AND ai.if(
                prompt => 'Does this anomaly: "' || description ||
                          '" match the user query: "' || :q || '"?',
                model_id => 'gemini-3-flash-preview'
              ) = 'true'
        ORDER BY score DESC
        LIMIT 5;
    """)

    print("🔥 [PulseCare] Executing AlloyDB AI query...")

    with engine.connect() as conn:
        result = conn.execute(query, {"q": user_query})

        rows = [
            {
                "description": r[0],
                "severity": r[1],
                "device": r[2],
                "time": str(r[3]),
                "score": round(r[4], 2)
            }
            for r in result
        ]

    print(f"🔥 [PulseCare] Retrieved {len(rows)} results from AlloyDB")

    return {
        "agent": "PulseCare AI Agent",
        "mode": "alloydb-native-ai",
        "count": len(rows),
        "results": rows,
        "insight": "Results generated using vector similarity + LLM reasoning inside AlloyDB"
    }


# -------------------------------
# 🔥 MAIN ROUTE
# -------------------------------
@app.route('/ask', methods=['GET', 'POST'])
def ask():
    if request.method == 'GET':
        return jsonify({
            "message": "Use POST with JSON body",
            "example": {"query": "heart problems during sleep"}
        })

    user_query = request.json.get("query", "")

    if not user_query:
        return jsonify({"error": "Query is required"}), 400

    # 🔥 ALWAYS use AlloyDB AI here (no routing)
    return jsonify(run_alloydb_ai_query(user_query))


# -------------------------------
# 🔹 Root
# -------------------------------
@app.route('/')
def home():
    return jsonify({
        "agent": "PulseCare AI Agent",
        "status": "running 🚀",
        "main_demo": "/ask",
        "modes": {
            "/ask": "AlloyDB Native AI (Recommended)",
            "/nl-query": "NL → SQL",
            "/semantic-query": "Vector Search"
        },
        "example_queries": [
            "Show all critical anomalies",
            "List anomalies for patient 101",
            "heart problems during sleep"
        ]
    })


# -------------------------------
# 🚀 Run
# -------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
