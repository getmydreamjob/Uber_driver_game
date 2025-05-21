# app.py
import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import uuid

# ─── HELPERS ────────────────────────────────────────────────────
def haversine(a, b):
    """Return distance in KM between points a/b."""
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * 6371 * math.asin(math.sqrt(h))

# ─── SESSION STATE SETUP ────────────────────────────────────────
if "users" not in st.session_state:
    st.session_state.users = {}  # email → {password, role}
if "packages" not in st.session_state:
    st.session_state.packages = []  # list of package dicts
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# ─── AUTHENTICATION ─────────────────────────────────────────────
if st.session_state.current_user is None:
    st.title("📦 Package Roadie")
    mode = st.sidebar.selectbox("Mode", ["Login", "Register"])
    email = st.sidebar.text_input("Email")
    pwd   = st.sidebar.text_input("Password", type="password")
    role  = st.sidebar.selectbox("Role", ["Client", "Driver"])
    if mode == "Register" and st.sidebar.button("Register"):
        if email in st.session_state.users:
            st.sidebar.error("User already exists")
        else:
            st.session_state.users[email] = {"password": pwd, "role": role}
            st.sidebar.success("Registered! Switch to Login.")
    if mode == "Login" and st.sidebar.button("Login"):
        u = st.session_state.users.get(email)
        if u and u["password"] == pwd and u["role"] == role:
            st.session_state.current_user = {"email": email, "role": role}
            st.experimental_rerun()  # safe on Streamlit>=1.20.0
        else:
            st.sidebar.error("Invalid credentials")
    st.stop()

# ─── LOGGED-IN LAYOUT ────────────────────────────────────────────
user = st.session_state.current_user
st.sidebar.write(f"👤 {user['email']} ({user['role']})")
if st.sidebar.button("Logout"):
    st.session_state.current_user = None
    st.experimental_rerun()

st.title(f"Welcome, {user['role']}!")

# ─── CLIENT VIEW ────────────────────────────────────────────────
if user["role"] == "Client":
    st.header("📮 Create a Package Request")
    with st.form("new_pkg"):
        p_lat = st.number_input("Pickup Latitude", format="%.5f")
        p_lng = st.number_input("Pickup Longitude", format="%.5f")
        d_lat = st.number_input("Drop-off Latitude", format="%.5f")
        d_lng = st.number_input("Drop-off Longitude", format="%.5f")
        submitted = st.form_submit_button("Submit Request")
    if submitted:
        dist = haversine((p_lat, p_lng), (d_lat, d_lng))
        time_min = dist / 40 * 60  # assume 40 km/h
        price = round(5 + 2 * dist + 0.5 * time_min, 2)
        pkg = {
            "id": uuid.uuid4().hex[:8],
            "client": user["email"],
            "driver": None,
            "pickup": (p_lat, p_lng),
            "dropoff": (d_lat, d_lng),
            "distance": dist,
            "eta_min": time_min,
            "price": price,
            "status": "pending",
        }
        st.session_state.packages.append(pkg)
        st.success(f"Request {pkg['id']} created: ${price}, {dist:.2f} km, {time_min:.0f} min")

    st.subheader("Your Requests")
    cols = ["id","status","price","distance","eta_min"]
    data = [
        {k: (f"{v:.2f}" if isinstance(v,(float,)) else v) for k,v in 
         {**{c: p[c] for c in cols}}.items()}
        for p in st.session_state.packages
        if p["client"] == user["email"]
    ]
    st.table(data)

    st.subheader("Map of Your Packages")
    m = folium.Map(location=(p_lat or 40.7580, p_lng or -73.9855), zoom_start=12)
    for p in st.session_state.packages:
        if p["client"] == user["email"]:
            folium.Marker(
                location=p["pickup"],
                popup=(f"ID:{p['id']}💲{p['price']}"),
                icon=folium.Icon(color="blue", icon="package", prefix="fa"),
            ).add_to(m)
            folium.Marker(
                location=p["dropoff"],
                icon=folium.Icon(color="gray", icon="flag", prefix="fa"),
            ).add_to(m)
    st_folium(m, width=700, height=400)

# ─── DRIVER VIEW ────────────────────────────────────────────────
else:
    st.subheader("🚚 Pending Packages")
    pending = [p for p in st.session_state.packages if p["status"] == "pending"]
    for p in pending:
        cols = st.columns([1,1,1,1,2])
        cols[0].write(p["id"])
        cols[1].write(f"${p['price']}")
        cols[2].write(f"{p['distance']:.1f} km")
        cols[3].write(f"{p['eta_min']:.0f} min")
        if cols[4].button(f"Accept {p['id']}"):
            p["status"] = "accepted"
            p["driver"] = user["email"]
            st.success(f"Assigned {p['id']} to you.")
            st.experimental_rerun()

    st.subheader("📍 Map of Pending")
    m = folium.Map(location=(40.7580, -73.9855), zoom_start=12)
    for p in pending:
        folium.Marker(
            location=p["pickup"],
            popup=(
                f"ID:{p['id']}<br>"
                f"💲{p['price']} • {p['distance']:.1f} km • {p['eta_min']:.0f} min"
            ),
            icon=folium.Icon(color="green", icon="truck", prefix="fa"),
        ).add_to(m)
    st_folium(m, width=700, height=400)

    st.subheader("🚚 Your Assigned")
    assigned = [p for p in st.session_state.packages 
                if p.get("driver")==user["email"]]
    st.table([
        {
            "id": p["id"],
            "status": p["status"],
            "price": f"${p['price']}",
            "dist_km": f"{p['distance']:.2f}",
            "eta_min": f"{p['eta_min']:.0f}"
        }
        for p in assigned
    ])
