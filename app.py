
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3, os, re, math
from datetime import datetime

app = Flask(__name__)
app.secret_key = "smart-foundry-demo"
DB = "foundry.db"
UPLOAD_DIR = os.path.join("static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, cost REAL, carbon REAL, silicon REAL, manganese REAL, iron REAL
    );
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT, pattern TEXT, quantity INTEGER, weight REAL,
        material TEXT, status TEXT, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS maintenance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        machine TEXT, record TEXT, created_at TEXT
    );
    """)
    if conn.execute("SELECT COUNT(*) FROM materials").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO materials(name,cost,carbon,silicon,manganese,iron) VALUES(?,?,?,?,?,?)",
            [
                ("Pig Iron", 52, 3.8, 1.2, 0.5, 94.5),
                ("Return Scrap", 42, 3.2, 1.5, 0.6, 94.7),
                ("Steel Scrap", 38, 0.15, 0.2, 0.7, 98.95),
                ("Carbon Additive", 75, 95.0, 0, 0, 5.0),
                ("FeSi", 110, 0, 72, 0, 28),
                ("FeMn", 95, 0, 0, 70, 30),
            ]
        )
    conn.commit()
    conn.close()

def charge_recommendation(total_kg, target_c=3.4, target_si=2.1, target_mn=0.6):
    """
    Lightweight prototype optimizer.
    It searches practical percentages for the three metallic inputs and then
    estimates small alloy additions to move the composition toward the target.
    Replace this function with PuLP/SciPy optimization and real foundry data
    for the final implementation.
    """
    best = None
    materials = {
        "Pig Iron": {"cost":52, "c":3.8, "si":1.2, "mn":0.5},
        "Return Scrap": {"cost":42, "c":3.2, "si":1.5, "mn":0.6},
        "Steel Scrap": {"cost":38, "c":0.15, "si":0.2, "mn":0.7},
    }
    for pig_pct in range(0, 81, 5):
        for return_pct in range(0, 101-pig_pct, 5):
            steel_pct = 100 - pig_pct - return_pct
            c = (pig_pct*3.8 + return_pct*3.2 + steel_pct*0.15)/100
            si = (pig_pct*1.2 + return_pct*1.5 + steel_pct*0.2)/100
            mn = (pig_pct*0.5 + return_pct*0.6 + steel_pct*0.7)/100
            # Simple alloy additions, expressed as percentage of final batch.
            fesi = max(0, (target_si-si)/72*100)
            femn = max(0, (target_mn-mn)/70*100)
            carbon = max(0, (target_c-c)/95*100)
            total_pct = pig_pct + return_pct + steel_pct + fesi + femn + carbon
            if total_pct > 105:
                continue
            cost = (
                (pig_pct/100)*total_kg*52 +
                (return_pct/100)*total_kg*42 +
                (steel_pct/100)*total_kg*38 +
                (fesi/100)*total_kg*110 +
                (femn/100)*total_kg*95 +
                (carbon/100)*total_kg*75
            )
            score = abs(c+carbon/100*95-target_c) + abs(si+fesi/100*72-target_si) + abs(mn+femn/100*70-target_mn)
            score += cost/100000
            if best is None or score < best["score"]:
                best = dict(score=score, cost=cost, pig=pig_pct, ret=return_pct,
                            steel=steel_pct, fesi=fesi, femn=femn, carbon=carbon,
                            c=c+carbon/100*95, si=si+fesi/100*72, mn=mn+femn/100*70)
    return best

def maintenance_analysis(record):
    text = record.lower()
    rules = {
        "Bearing / lubrication": ["bearing", "lubrication", "grease", "oil"],
        "Electrical": ["motor", "wiring", "electrical", "sensor", "voltage"],
        "Temperature / furnace": ["temperature", "overheat", "furnace", "thermocouple"],
        "Hydraulic": ["hydraulic", "pressure", "pump", "leak"],
        "Vibration": ["vibration", "noise", "alignment"],
    }
    found = [name for name, words in rules.items() if any(w in text for w in words)]
    if not found:
        found = ["General inspection"]
    action = "Inspect the affected equipment and review previous maintenance records."
    if "Bearing / lubrication" in found:
        action = "Check bearing condition, lubrication interval and alignment; schedule preventive service."
    elif "Temperature / furnace" in found:
        action = "Check temperature sensors, furnace condition and calibration history."
    elif "Electrical" in found:
        action = "Inspect wiring, sensors, motor condition and electrical connections."
    return found, action

init_db()

@app.route("/")
def dashboard():
    conn = db()
    orders = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 8").fetchall()
    maintenance = conn.execute("SELECT * FROM maintenance ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()
    return render_template("dashboard.html", orders=orders, maintenance=maintenance)

@app.route("/patterns", methods=["GET","POST"])
def patterns():
    result = None
    if request.method == "POST":
        image = request.files.get("image")
        if image and image.filename:
            safe = re.sub(r"[^A-Za-z0-9_.-]", "_", image.filename)
            path = os.path.join(UPLOAD_DIR, safe)
            image.save(path)
            # Hook for YOLO/OpenCV:
            # model = YOLO("models/pattern_detector.pt")
            # detections = model(path)
            # For the prototype, ask for/accept batch details below.
            result = {"image": url_for("static", filename=f"uploads/{safe}")}
        quantity = int(request.form.get("quantity") or 1)
        weight = float(request.form.get("weight") or 0)
        material = request.form.get("material") or "Cast Iron"
        total = quantity * weight
        result = result or {}
        result.update(quantity=quantity, weight=weight, material=material, total=total)
    return render_template("patterns.html", result=result)

@app.route("/charge", methods=["GET","POST"])
def charge():
    recommendation = None
    if request.method == "POST":
        total = float(request.form.get("total_kg") or 0)
        c = float(request.form.get("carbon") or 3.4)
        si = float(request.form.get("silicon") or 2.1)
        mn = float(request.form.get("manganese") or 0.6)
        if total > 0:
            recommendation = charge_recommendation(total, c, si, mn)
    return render_template("charge.html", recommendation=recommendation)

@app.route("/maintenance", methods=["GET","POST"])
def maintenance():
    analysis = None
    if request.method == "POST":
        machine = request.form.get("machine","")
        record = request.form.get("record","")
        conn = db()
        conn.execute("INSERT INTO maintenance(machine,record,created_at) VALUES(?,?,?)",
                     (machine,record,datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit(); conn.close()
        faults, action = maintenance_analysis(record)
        analysis = {"faults": faults, "action": action}
    return render_template("maintenance.html", analysis=analysis)

@app.route("/quotation", methods=["GET","POST"])
def quotation():
    result = None
    if request.method == "POST":
        qty = int(request.form.get("quantity") or 0)
        weight = float(request.form.get("weight") or 0)
        cycle = float(request.form.get("cycle_hours") or 0)
        material_rate = float(request.form.get("material_rate") or 0)
        labour = float(request.form.get("labour") or 0)
        overhead = float(request.form.get("overhead") or 0)
        total_weight = qty * weight
        material_cost = total_weight * material_rate
        production_cost = material_cost + labour + overhead
        result = {
            "total_weight": total_weight,
            "material_cost": material_cost,
            "production_cost": production_cost,
            "lead_time_hours": qty * cycle
        }
    return render_template("quotation.html", result=result)

@app.route("/simulation", methods=["GET","POST"])
def simulation():
    result = None
    if request.method == "POST":
        batch = float(request.form.get("batch") or 0)
        furnace_capacity = float(request.form.get("capacity") or 0)
        charge_count = math.ceil(batch/furnace_capacity) if furnace_capacity else 0
        utilization = (batch/(charge_count*furnace_capacity)*100) if charge_count and furnace_capacity else 0
        result = {"batch":batch, "capacity":furnace_capacity,
                  "charge_count":charge_count, "utilization":utilization}
    return render_template("simulation.html", result=result)

@app.route("/orders", methods=["GET","POST"])
def orders():
    if request.method == "POST":
        data = (
            request.form.get("customer",""),
            request.form.get("pattern",""),
            int(request.form.get("quantity") or 0),
            float(request.form.get("weight") or 0),
            request.form.get("material",""),
            "Planned",
            datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        conn=db()
        conn.execute("""INSERT INTO orders
            (customer,pattern,quantity,weight,material,status,created_at)
            VALUES(?,?,?,?,?,?,?)""", data)
        conn.commit(); conn.close()
        flash("Casting order added.")
        return redirect(url_for("orders"))
    conn=db()
    rows=conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("orders.html", orders=rows)

if __name__ == "__main__":
    app.run(debug=True)
