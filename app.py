from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3, os
from datetime import datetime

BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB=os.path.join(BASE,"database","pocket_smart.db")
FRONT=os.path.join(BASE,"frontend")

app=Flask(__name__, static_folder=FRONT)
CORS(app)

def db():
    con=sqlite3.connect(DB)
    con.row_factory=sqlite3.Row
    return con

def init_db():
    con=db()
    con.execute('''CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        note TEXT,
        date TEXT NOT NULL
    )''')
    con.execute('''CREATE TABLE IF NOT EXISTS settings(
        id INTEGER PRIMARY KEY CHECK(id=1),
        monthly_income REAL DEFAULT 0,
        monthly_budget REAL DEFAULT 0
    )''')
    con.execute("INSERT OR IGNORE INTO settings(id,monthly_income,monthly_budget) VALUES(1,0,0)")
    con.commit(); con.close()

@app.route("/")
def home(): return send_from_directory(FRONT,"index.html")

@app.route("/<path:path>")
def static_files(path): return send_from_directory(FRONT,path)

@app.route("/api/transactions", methods=["GET"])
def transactions():
    con=db()
    rows=con.execute("SELECT * FROM transactions ORDER BY date DESC,id DESC").fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/transactions", methods=["POST"])
def add_transaction():
    data=request.get_json()
    try: amount=float(data["amount"])
    except: return jsonify({"error":"Invalid amount"}),400
    if amount<=0: return jsonify({"error":"Amount must be positive"}),400
    typ=data.get("type","expense")
    if typ not in ("income","expense"): return jsonify({"error":"Invalid type"}),400
    con=db()
    con.execute("INSERT INTO transactions(type,category,amount,note,date) VALUES(?,?,?,?,?)",
                (typ,data.get("category","Other"),amount,data.get("note",""),data.get("date") or datetime.now().strftime("%Y-%m-%d")))
    con.commit(); con.close()
    return jsonify({"message":"Transaction added"})

@app.route("/api/transactions/<int:tid>", methods=["DELETE"])
def delete_transaction(tid):
    con=db(); con.execute("DELETE FROM transactions WHERE id=?",(tid,)); con.commit(); con.close()
    return jsonify({"message":"Deleted"})

@app.route("/api/settings", methods=["GET","POST"])
def settings():
    con=db()
    if request.method=="POST":
        data=request.get_json()
        income=float(data.get("monthly_income",0))
        budget=float(data.get("monthly_budget",0))
        con.execute("UPDATE settings SET monthly_income=?,monthly_budget=? WHERE id=1",(income,budget))
        con.commit()
    row=con.execute("SELECT * FROM settings WHERE id=1").fetchone()
    con.close()
    return jsonify(dict(row))

@app.route("/api/dashboard")
def dashboard():
    con=db()
    income=con.execute("SELECT COALESCE(SUM(amount),0) n FROM transactions WHERE type='income'").fetchone()["n"]
    expense=con.execute("SELECT COALESCE(SUM(amount),0) n FROM transactions WHERE type='expense'").fetchone()["n"]
    cats=con.execute("SELECT category,SUM(amount) total FROM transactions WHERE type='expense' GROUP BY category ORDER BY total DESC").fetchall()
    s=con.execute("SELECT * FROM settings WHERE id=1").fetchone()
    con.close()
    remaining=income-expense
    budget=float(s["monthly_budget"])
    recommendations=[]
    if expense>income and income>0: recommendations.append("Your recorded expenses are higher than your income. Review non-essential spending.")
    if budget>0 and expense>budget: recommendations.append(f"You have exceeded your budget by ₹{expense-budget:.2f}.")
    if cats:
        top=cats[0]
        if expense>0 and top["total"]/expense>=0.35:
            recommendations.append(f"{top['category']} is your largest spending category. Consider setting a lower limit for it.")
    if remaining>0: recommendations.append(f"Your current recorded balance is ₹{remaining:.2f}. Consider allocating part of it toward savings.")
    if not recommendations: recommendations.append("Add a few transactions to receive personalized spending insights.")
    return jsonify({
        "income":income,"expense":expense,"balance":remaining,"budget":budget,
        "categories":[dict(x) for x in cats],
        "recommendations":recommendations
    })

init_db()
if __name__=="__main__":
    app.run(debug=True)
