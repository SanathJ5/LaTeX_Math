from flask import Flask, render_template, request, jsonify
from latex_processor import transform_latex
import sqlite3

app = Flask(__name__)

# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect("history.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        latex TEXT,
        output TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/run", methods=["POST"])
def run():

    data = request.json

    latex = data.get("latex", "")
    language = data.get("language", "PYTHON")
    single_var = data.get("single_var", False)

    output = transform_latex(
        latex,
        convert_to=language,
        single_var=single_var
    )

    # -------- save to history --------
    conn = sqlite3.connect("history.db")
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO history (latex, output) VALUES (?, ?)",
        (latex, output)
    )

    conn.commit()
    conn.close()
    # ---------------------------------

    return jsonify({"output": output})


@app.route("/history")
def history():

    conn = sqlite3.connect("history.db")
    cur = conn.cursor()

    rows = cur.execute(
        "SELECT latex,output FROM history ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template("history.html", rows=rows)


if __name__ == "__main__":
    app.run(debug=True)