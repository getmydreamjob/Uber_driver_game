import streamlit as st
import time
import random
import math

import folium
from streamlit_folium import st_folium

# ─── CONFIG ──────────────────────────────────────────────────────────────────────
START_LAT, START_LNG = 40.7580, -73.9855  # Times Square, NYC
SPEED_KMH = 30  # simulated speed for time calculation
INTERP_STEPS = 50  # points per leg for animation

# ─── UTILITY FUNCTIONS ───────────────────────────────────────────────────────────
def haversine(a, b):
    """Calculate distance in km between two (lat, lng) points."""
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * 6371 * math.asin(math.sqrt(h))

def interpolate(a, b, n):
    """Return n+1 equally spaced points between a and b."""
    return [
        (
            a[0] + (b[0] - a[0]) * i / n,
            a[1] + (b[1] - a[1]) * i / n
        )
        for i in range(n + 1)
    ]

def rand_point(center, radius_m=2000):
    """Random point within radius_m meters of center (lat, lng)."""
    # approximate: 1° lat ~111km
    r = radius_m / 1000 / 111  # in degrees
    theta = random.random() * 2 * math.pi
    dx = r * math.cos(theta)
    dy = r * math.sin(theta) / math.cos(math.radians(center[0]))
    return center[0] + dy, center[1] + dx

# ─── SESSION STATE SETUP ────────────────────────────────────────────────────────
if "loc" not in st.session_state:
    st.session_state.loc = (START_LAT, START_LNG)
    st.session_state.earnings = 0.0
    st.session_state.trips = 0
    st.session_state.pick = None
    st.session_state.drop = None
    st.session_state.route = None
    st.session_state.idx = 0
    st.session_state.fare = 0.0

# ─── SIDEBAR CONTROLS ────────────────────────────────────────────────────────────
st.sidebar.header("⏱ Shift Controls")
if st.sidebar.button("🚦 Start New Shift"):
    for key in ["loc","earnings","trips","pick","drop","route","idx","fare"]:
        st.session_state[key] = None if key in ("pick","drop","route") else 0.0 if key=="earnings" else 0
    st.session_state.loc = (START_LAT, START_LNG)
    st.experimental_rerun()

st.sidebar.markdown("---")
st.sidebar.write(f"**Earnings:** ${st.session_state.earnings:.2f}")
st.sidebar.write(f"**Trips Completed:** {st.session_state.trips}")

# ─── NEW TRIP REQUEST ────────────────────────────────────────────────────────────
if st.session_state.pick is None:
    # generate pickup & drop
    pick = rand_point(st.session_state.loc)
    drop = rand_point(pick)
    st.session_state.pick, st.session_state.drop = pick, drop

    # show request
    st.sidebar.markdown("### 🚗 New Trip Request")
    st.sidebar.write(f"- **Pickup:** {pick[0]:.5f}, {pick[1]:.5f}")
    st.sidebar.write(f"- **Drop-off:** {drop[0]:.5f}, {drop[1]:.5f}")

    c1, c2 = st.sidebar.columns(2)
    if c2.button("Decline"):
        st.session_state.pick = st.session_state.drop = None
        st.experimental_rerun()
    if c1.button("Accept"):
        # compute distances
        d1 = haversine(st.session_state.loc, pick)
        d2 = haversine(pick, drop)
        dist = d1 + d2
        # simulate time
        time_min = dist / SPEED_KMH * 60
        # fare calc
        st.session_state.fare = round(2.50 + 1.50 * dist + 0.25 * time_min, 2)
        # build route = interpolate loc→pick then pick→drop
        route1 = interpolate(st.session_state.loc, pick, INTERP_STEPS)
        route2 = interpolate(pick, drop, INTERP_STEPS)
        st.session_state.route = route1 + route2
        st.session_state.idx = 0
        st.experimental_rerun()

# ─── RENDER & ANIMATE ────────────────────────────────────────────────────────────
m = folium.Map(location=st.session_state.loc, zoom_start=14)

if st.session_state.route:
    # draw full route
    folium.PolyLine(st.session_state.route, weight=5).add_to(m)
    # place car at current step
    pos = st.session_state.route[st.session_state.idx]
    folium.Marker(location=pos, icon=folium.Icon(icon="car", prefix="fa")).add_to(m)

    st_folium(m, width=700, height=500)

    # step forward
    time.sleep(0.2)
    st.session_state.idx += 1
    if st.session_state.idx >= len(st.session_state.route):
        # trip done
        st.sidebar.success(f"✅ Trip complete! +${st.session_state.fare:.2f}")
        st.session_state.earnings += st.session_state.fare
        st.session_state.trips += 1
        st.session_state.loc = st.session_state.drop
        st.session_state.pick = st.session_state.drop = st.session_state.route = None
        st.session_state.idx = 0
    st.experimental_rerun()

else:
    # just show car at loc
    folium.Marker(location=st.session_state.loc, icon=folium.Icon(icon="car", prefix="fa")).add_to(m)
    st_folium(m, width=700, height=500)
