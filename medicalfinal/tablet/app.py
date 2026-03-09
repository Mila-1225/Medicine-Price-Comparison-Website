from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
from pathlib import Path
from datetime import datetime
import math

DATA_PATH = Path(__file__).parent / "data.json"

app = Flask(__name__)
app.secret_key = "medicine-comparison-secret-key-change-in-production"


def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers using Haversine formula"""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float('inf')
    
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distance = R * c
    return distance


@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    user_lat = request.args.get("lat", type=float)
    user_lon = request.args.get("lon", type=float)
    radius = request.args.get("radius", 10, type=float)  # Default 10 km
    
    data = load_data()
    medicines = data.get("medicines", [])

    if query:
        q = query.lower()
        filtered = []
        for med in medicines:
            name = (med.get("name") or "").lower()
            brand = (med.get("brand") or "").lower()
            generic_name = (med.get("generic_name") or "").lower()
            composition = (med.get("composition") or "").lower()
            if q in name or q in brand or q in generic_name or q in composition:
                filtered.append(med)
        medicines = filtered
    else:
        medicines = sorted(
            medicines,
            key=lambda m: (m.get("name") or "").lower(),
        )[:20]

    return render_template("index.html", medicines=medicines, query=query)


@app.route("/medicine/<int:medicine_id>")
def medicine_detail(medicine_id):
    user_lat = request.args.get("lat", type=float)
    user_lon = request.args.get("lon", type=float)
    radius = request.args.get("radius", 10, type=float)
    
    data = load_data()
    medicines = data.get("medicines", [])
    stores = data.get("stores", [])
    store_medicines = data.get("store_medicines", [])

    # Find selected medicine
    medicine = next((m for m in medicines if m.get("medicine_id") == medicine_id), None)
    if medicine is None:
        return "Medicine not found", 404

    # Build stores lookup (only approved)
    stores_by_id = {
        s["store_id"]: s
        for s in stores
        if s.get("status", "APPROVED") == "APPROVED"
    }

    # Build list of store prices for this medicine
    store_prices = []
    for sm in store_medicines:
        if sm.get("medicine_id") != medicine_id:
            continue
        store = stores_by_id.get(sm.get("store_id"))
        if not store:
            continue
        
        # Calculate distance if user location provided
        distance = None
        if user_lat and user_lon:
            store_lat = store.get("latitude")
            store_lon = store.get("longitude")
            if store_lat and store_lon:
                distance = calculate_distance(user_lat, user_lon, store_lat, store_lon)
        
        # Skip if outside radius
        if distance is not None and radius and distance > radius:
            continue
        
        record = {
            "store_medicine_id": sm.get("store_medicine_id"),
            "price": sm.get("price"),
            "discount_percent": sm.get("discount_percent", 0.0),
            "final_price": sm.get("final_price"),
            "availability": sm.get("availability", "IN_STOCK"),
            "last_updated_at": sm.get("last_updated_at", ""),
            "store_id": store.get("store_id"),
            "store_name": store.get("name"),
            "address": store.get("address"),
            "city": store.get("city"),
            "pincode": store.get("pincode"),
            "distance": round(distance, 2) if distance else None,
        }
        store_prices.append(record)

    store_prices.sort(key=lambda r: r["final_price"])

    min_price = max_price = avg_price = None
    if store_prices:
        prices = [row["final_price"] for row in store_prices]
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)

    # Find alternative medicines with same composition and dosage
    alternatives = [
        m
        for m in medicines
        if m.get("composition") == medicine.get("composition")
        and m.get("dosage") == medicine.get("dosage")
        and m.get("medicine_id") != medicine_id
    ]

    # For each alternative, find cheapest store price
    alternative_recommendations = []
    for alt in alternatives:
        alt_store_records = []
        for sm in store_medicines:
            if sm.get("medicine_id") != alt.get("medicine_id"):
                continue
            store = stores_by_id.get(sm.get("store_id"))
            if not store:
                continue
            alt_store_records.append(
                {
                    "final_price": sm.get("final_price"),
                    "store_name": store.get("name"),
                    "city": store.get("city"),
                }
            )
        if alt_store_records:
            alt_store_records.sort(key=lambda r: r["final_price"])
            cheapest = alt_store_records[0]
            alternative_recommendations.append(
                {
                    "medicine": alt,
                    "cheapest_price": cheapest["final_price"],
                    "store_name": cheapest["store_name"],
                    "city": cheapest["city"],
                }
            )

    return render_template(
        "medicine_detail.html",
        medicine=medicine,
        store_prices=store_prices,
        min_price=min_price,
        max_price=max_price,
        avg_price=avg_price,
        alternative_recommendations=alternative_recommendations,
    )


# ============ Authentication Routes ============

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        data = load_data()
        users = data.get("users", [])
        
        user = next((u for u in users if u.get("username") == username and u.get("password") == password), None)
        
        if user:
            session["user_id"] = user.get("user_id")
            session["username"] = user.get("username")
            session["role"] = user.get("role")
            session["store_id"] = user.get("store_id")
            
            if user.get("role") == "ADMIN":
                return redirect(url_for("admin_dashboard"))
            elif user.get("role") == "STORE_OWNER":
                return redirect(url_for("store_dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")
    
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ============ Store Owner Routes ============

@app.route("/store/dashboard")
def store_dashboard():
    if session.get("role") != "STORE_OWNER":
        return redirect(url_for("login"))
    
    store_id = session.get("store_id")
    data = load_data()
    
    store = next((s for s in data.get("stores", []) if s.get("store_id") == store_id), None)
    if not store:
        return "Store not found", 404
    
    # Get medicines for this store
    store_medicines = [sm for sm in data.get("store_medicines", []) if sm.get("store_id") == store_id]
    medicines_by_id = {m["medicine_id"]: m for m in data.get("medicines", [])}
    
    inventory = []
    for sm in store_medicines:
        med = medicines_by_id.get(sm.get("medicine_id"))
        if med:
            inventory.append({
                "store_medicine_id": sm.get("store_medicine_id"),
                "medicine": med,
                "price": sm.get("price"),
                "discount_percent": sm.get("discount_percent"),
                "final_price": sm.get("final_price"),
                "availability": sm.get("availability"),
            })
    
    return render_template("store_dashboard.html", store=store, inventory=inventory, medicines=data.get("medicines", []))


@app.route("/store/add_medicine", methods=["POST"])
def store_add_medicine():
    if session.get("role") != "STORE_OWNER":
        return redirect(url_for("login"))

    try:
        store_id = session.get("store_id")

        medicine_id = int(request.form.get("medicine_id"))
        price = float(request.form.get("price"))
        discount = float(request.form.get("discount") or 0)
        availability = request.form.get("availability") or "IN_STOCK"

        final_price = round(price * (1 - discount / 100.0), 2)

        data = load_data()

        if "store_medicines" not in data:
            data["store_medicines"] = []

        # Prevent duplicates
        for sm in data["store_medicines"]:
            if sm["store_id"] == store_id and sm["medicine_id"] == medicine_id:
                return redirect(url_for("store_dashboard"))

        new_id = max([sm.get("store_medicine_id", 0) for sm in data["store_medicines"]], default=0) + 1

        data["store_medicines"].append({
            "store_medicine_id": new_id,
            "store_id": store_id,
            "medicine_id": medicine_id,
            "price": price,
            "discount_percent": discount,
            "final_price": final_price,
            "availability": availability,
            "last_updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        save_data(data)

    except Exception as e:
        print("ADD MEDICINE ERROR:", e)

    return redirect(url_for("store_dashboard"))


@app.route("/store/update_medicine", methods=["POST"])
def store_update_medicine():
    if session.get("role") != "STORE_OWNER":
        return redirect(url_for("login"))
    
    store_id = session.get("store_id")
    store_medicine_id = request.form.get("store_medicine_id", type=int)
    price = request.form.get("price", type=float)
    discount = request.form.get("discount", 0, type=float)
    availability = request.form.get("availability", "IN_STOCK")
    
    data = load_data()
    store_medicines = data.get("store_medicines", [])
    
    for sm in store_medicines:
        if sm.get("store_medicine_id") == store_medicine_id and sm.get("store_id") == store_id:
            sm["price"] = price
            sm["discount_percent"] = discount
            sm["final_price"] = round(price * (1 - discount / 100.0), 2)
            sm["availability"] = availability
            sm["last_updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
    
    data["store_medicines"] = store_medicines
    save_data(data)
    
    return redirect(url_for("store_dashboard"))


@app.route("/store/delete_medicine/<int:store_medicine_id>")
def store_delete_medicine(store_medicine_id):
    if session.get("role") != "STORE_OWNER":
        return redirect(url_for("login"))
    
    store_id = session.get("store_id")
    data = load_data()
    store_medicines = data.get("store_medicines", [])
    
    data["store_medicines"] = [sm for sm in store_medicines if not (sm.get("store_medicine_id") == store_medicine_id and sm.get("store_id") == store_id)]
    save_data(data)
    
    return redirect(url_for("store_dashboard"))


# ============ Admin Routes ============

@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "ADMIN":
        return redirect(url_for("login"))
    
    data = load_data()
    stores = data.get("stores", [])
    medicines = data.get("medicines", [])
    users = data.get("users", [])
    
    pending_stores = [s for s in stores if s.get("status") == "PENDING"]
    approved_stores = [s for s in stores if s.get("status") == "APPROVED"]
    
    return render_template("admin_dashboard.html", 
                         pending_stores=pending_stores,
                         approved_stores=approved_stores,
                         medicines=medicines,
                         users=users)


@app.route("/admin/approve_store/<int:store_id>")
def admin_approve_store(store_id):
    if session.get("role") != "ADMIN":
        return redirect(url_for("login"))
    
    data = load_data()
    stores = data.get("stores", [])
    
    for store in stores:
        if store.get("store_id") == store_id:
            store["status"] = "APPROVED"
            break
    
    data["stores"] = stores
    save_data(data)
    
    return redirect(url_for("admin_dashboard"))



@app.route("/map")
def store_map():
    data = load_data()
    stores = [
        s for s in data.get("stores", [])
        if s.get("status") == "APPROVED"
        and s.get("latitude") is not None
        and s.get("longitude") is not None
    ]
    return render_template("store_map.html", stores=stores)

@app.route("/register-store", methods=["GET", "POST"])
def register_store():
    if request.method == "POST":
        if request.form["password"] != request.form["confirm_password"]:
            return "Passwords do not match", 400

        data = load_data()

        store_id = max([s.get("store_id", 0) for s in data["stores"]], default=0) + 1
        user_id = max([u.get("user_id", 0) for u in data["users"]], default=0) + 1

        store = {
            "store_id": store_id,
            "name": request.form["store_name"],
            "address": request.form["address"],
            "city": request.form["city"],
            "pincode": request.form["pincode"],
            "latitude": float(request.form["latitude"]),
            "longitude": float(request.form["longitude"]),
            "status": "PENDING"
        }

        user = {
            "user_id": user_id,
            "username": request.form["username"],
            "password": request.form["password"],
            "role": "STORE_OWNER",
            "store_id": store_id
        }

        data["stores"].append(store)
        data["users"].append(user)

        save_data(data)

        return redirect(url_for("login"))

    return render_template("register_store.html")



@app.route("/admin/reject_store/<int:store_id>")
def admin_reject_store(store_id):
    if session.get("role") != "ADMIN":
        return redirect(url_for("login"))
    
    data = load_data()
    stores = data.get("stores", [])
    
    for store in stores:
        if store.get("store_id") == store_id:
            store["status"] = "REJECTED"
            break
    
    data["stores"] = stores
    save_data(data)
    
    return redirect(url_for("admin_dashboard"))




@app.route("/medicals-map")
def medicals_map():
    data = load_data()

    stores = []
    store_medicines = data.get("store_medicines", [])

    for store in data["stores"]:
        if store.get("status") != "APPROVED":
            continue

        prices = [
            sm["final_price"]
            for sm in store_medicines
            if sm["store_id"] == store["store_id"]
            and sm.get("availability") == "IN_STOCK"
        ]

        store["cheapest_price"] = min(prices) if prices else None
        stores.append(store)

    return render_template("medicals_map.html", stores=stores)


@app.route("/store/<int:store_id>/medicines")
def store_medicine_prices(store_id):
    data = load_data()

    store = next(s for s in data["stores"] if s["store_id"] == store_id)

    medicines = []
    med_lookup = {m["medicine_id"]: m for m in data["medicines"]}

    for sm in data["store_medicines"]:
        if sm["store_id"] == store_id:
            med = med_lookup.get(sm["medicine_id"])
            if med:
                medicines.append({
                    "name": med["name"],
                    "price": sm["final_price"],
                    "availability": sm["availability"]
                })

    return render_template(
        "store_medicines.html",
        store=store,
        medicines=medicines
    )


# ============ Admin: Add Medicine ============

@app.route("/admin/add-medicine", methods=["GET", "POST"])
def admin_add_medicine():
    if session.get("role") != "ADMIN":
        return redirect(url_for("login"))

    if request.method == "POST":
        data = load_data()
        medicines = data.get("medicines", [])

        new_id = max([m.get("medicine_id", 0) for m in medicines], default=0) + 1

        medicine = {
            "medicine_id": new_id,
            "name": request.form.get("name"),
            "brand": request.form.get("brand"),
            "generic_name": request.form.get("generic_name"),
            "composition": request.form.get("composition"),
            "dosage": request.form.get("dosage"),
            "category": request.form.get("category")
        }

        medicines.append(medicine)
        data["medicines"] = medicines
        save_data(data)

        return redirect(url_for("admin_dashboard"))

    return render_template("admin_add_medicine.html")


if __name__ == "__main__":
    app.run(debug=True)
