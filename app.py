# app.py
import streamlit as st
import random
import math

import folium
from streamlit_folium import st_folium

# ─── CONFIG ─────────────────────────────────────────────────────────────
START_LAT, START_LNG = 40.7580, -73.9855  # Times Square
SPEED_KMH = 30  # for fare calc

# ─── HELPERS ────────────────────────────────────────────────────────────
def haversine(a, b):
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * 6371 * math.asin(math.sqrt(h))

def rand_point(center, radius_m=2000):
    # random point within radius (meters)
    r = radius_m/1000/111  # approx degrees
    theta = random.random()*2*math.pi
    dy = r*math.sin(theta)
    dx = r*math.cos(theta)/math.cos(math.radians(center[0]))
    return (center[0] + dy, center[1] + dx)

# ─── STATE INIT ─────────────────────────────────────────────────────────
for var, val in {
    "loc": (START_LAT, START_LNG),
    "earnings": 0.0,
    "trips": 0,
    "pick": None,
    "drop": None,
    "route": None,
    "fare": 0.0,
}.items():
    if var not in st.session_state:
        st.session_state[var] = val

# ─── SIDEBAR / RESET ────────────────────────────────────────────────────
st.sidebar.header("Shift Controls")
if st.sidebar.button("🚦 Start New Shift"):
    st.session_state.loc = (START_LAT, START_LNG)
    st.session_state.earnings = 0.0
    st.session_state.trips = 0
    st.session_state.pick = None
    st.session_state.drop = None
    st.session_state.route = None
    st.session_state.fare = 0.0

st.sidebar.markdown("---")
st.sidebar.write(f"**Earnings:** ${st.session_state.earnings:.2f}")
st.sidebar.write(f"**Trips Completed:** {st.session_state.trips}")

# ─── NEW TRIP REQUEST ───────────────────────────────────────────────────
if st.session_state.route is None and st.session_state.pick is None:
    # generate pickup/drop
    p = rand_point(st.session_state.loc)
    d = rand_point(p)
    st.session_state.pick, st.session_state.drop = p, d

    st.sidebar.markdown("### 🚗 New Trip Request")
    st.sidebar.write(f"- **Pickup:** {p[0]:.5f}, {p[1]:.5f}")
    st.sidebar.write(f"- **Drop-off:** {d[0]:.5f}, {d[1]:.5f}")

    c1, c2 = st.sidebar.columns(2)
    if c2.button("Decline"):
        st.session_state.pick = None
        st.session_state.drop = None
    if c1.button("Accept"):
        # compute distance & fare
        dist_km = haversine(st.session_state.loc, p) + haversine(p, d)
        time_min = dist_km / SPEED_KMH * 60
        fare = 2.50 + 1.50 * dist_km + 0.25 * time_min
        st.session_state.fare = round(fare, 2)
        # route as straight-line segments
        st.session_state.route = [
            st.session_state.loc,
            st.session_state.pick,
            st.session_state.drop,
        ]

# ─── SHOW ROUTE & COMPLETE ──────────────────────────────────────────────
if st.session_state.route:
    m = folium.Map(location=st.session_state.loc, zoom_start=14)
    folium.PolyLine(st.session_state.route, weight=5).add_to(m)
    # markers
    folium.Marker(
        location=st.session_state.loc, icon=folium.Icon(icon="car", prefix="fa")
    ).add_to(m)
    folium.Marker(
        location=st.session_state.pick, icon=folium.Icon(icon="user", prefix="fa")
    ).add_to(m)
    folium.Marker(
        location=st.session_state.drop, icon=folium.Icon(icon="flag", prefix="fa")
    ).add_to(m)

    st_folium(m, width=700, height=500)

    if st.sidebar.button("✅ Complete Trip"):
        st.session_state.earnings += st.session_state.fare
        st.session_state.trips += 1
        st.session_state.loc = st.session_state.drop
        st.session_state.pick = None
        st.session_state.drop = None
        st.session_state.route = None
        st.session_state.fare = 0.0

else:
    # just show current location
    m = folium.Map(location=st.session_state.loc, zoom_start=14)
    folium.Marker(
        location=st.session_state.loc, icon=folium.Icon(icon="car", prefix="fa")
    ).add_to(m)
    st_folium(m, width=700, height=500)
