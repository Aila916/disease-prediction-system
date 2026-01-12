from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)

# ---------------- DATABASE CONNECTION ----------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="password",        # change if you set one
        database="disease_db"
    )

# ---------------- HOME PAGE ----------------
@app.route("/")
def index():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT symptom_id, symptom_name FROM symptom ORDER BY symptom_name")
    symptoms = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("index.html", symptoms=symptoms)

# ---------------- PREDICT ----------------
@app.route("/predict", methods=["POST"])
def predict():
    selected_symptoms = request.form.getlist("symptoms")

    # ✅ REMOVE EMPTY VALUES
    selected_symptoms = [s for s in selected_symptoms if s.strip() != ""]

    # ✅ IF NOTHING SELECTED
    if not selected_symptoms:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT symptom_id, symptom_name FROM symptom ORDER BY symptom_name")
        symptoms = cursor.fetchall()
        cursor.close()
        db.close()

        return render_template(
            "index.html",
            symptoms=symptoms,
            error="Please select at least one symptom."
        )

    symptom_ids = [int(s) for s in selected_symptoms]

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    placeholders = ",".join(["%s"] * len(symptom_ids))

    query = f"""
        SELECT 
            d.disease_id,
            d.disease_name,
            d.description,
            COUNT(ds.symptom_id) AS matched_symptoms
        FROM disease d
        JOIN disease_symptom ds ON d.disease_id = ds.disease_id
        WHERE ds.symptom_id IN ({placeholders})
        GROUP BY d.disease_id
        ORDER BY matched_symptoms DESC
        LIMIT 5
    """

    cursor.execute(query, symptom_ids)
    diseases = cursor.fetchall()

    # ---------------- CALCULATE PERCENTAGE ----------------
    results = []
    for d in diseases:
        cursor.execute(
            "SELECT COUNT(*) AS total FROM disease_symptom WHERE disease_id = %s",
            (d["disease_id"],)
        )
        total_symptoms = cursor.fetchone()["total"]

        match_percentage = (d["matched_symptoms"] / total_symptoms) * 100

        results.append({
            "disease_name": d["disease_name"],
            "description": d["description"],
            "match_percentage": match_percentage
        })

    cursor.execute("SELECT symptom_id, symptom_name FROM symptom ORDER BY symptom_name")
    symptoms = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "index.html",
        symptoms=symptoms,
        results=results
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
