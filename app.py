# ==============================
# 🩸 Smart Blood Donor System (FINAL FIXED)
# ==============================

import streamlit as st
import pandas as pd
import math
import bcrypt
import time
import requests
from pymongo import MongoClient
from geopy.geocoders import Nominatim
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

st.set_page_config(page_title="Blood Donor App", layout="wide")

# ==============================
# 👑 UI
# ==============================
st.markdown("""
<style>
.stApp { background-color: #0f172a; color: #e5e7eb; }
h1, h2, h3, label { color: #facc15 !important; }
.card { background: #1e293b; padding: 20px; border-radius: 15px; margin-bottom: 20px; }
.stButton>button { background-color: #facc15; color: black; border-radius: 8px; padding: 10px 18px; font-weight: bold; }
.stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
background-color: #1e293b !important; color: white !important; border-radius: 8px; }
section[data-testid="stSidebar"] { background-color: #020617; color: white; }
</style>
""", unsafe_allow_html=True)

# ==============================
# 🔗 MONGO
# ==============================
use_mongo = True
try:
    client = MongoClient("mongodb+srv://pravalikapalle08_db:24rh1a1245@cluster0.dr2lfw7.mongodb.net/?appName=Cluster0", serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client["blood_app"]
    users_collection = db["users"]
    st.sidebar.success("✅ MongoDB Connected")
except:
    use_mongo = False
    st.sidebar.error("❌ MongoDB Error")

# ==============================
# SESSION
# ==============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ==============================
# 📍 LOCATION
# ==============================
geolocator = Nominatim(user_agent="blood_app")

@st.cache_data
def get_coordinates(city):
    try:
        loc = geolocator.geocode(city + ", India", timeout=5)
        if loc:
            return (loc.latitude, loc.longitude)
    except:
        return None
    return None

def get_real_distance(origin, destination):
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{origin[1]},{origin[0]};{destination[1]},{destination[0]}?overview=false"
        response = requests.get(url).json()

        if response["code"] == "Ok":
            return response["routes"][0]["distance"] / 1000
    except:
        pass
    return 9999

# ==============================
# 🔐 LOGIN
# ==============================
def login_page():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not use_mongo:
            st.error("MongoDB not connected")
            return

        user = users_collection.find_one({"username": username})
        if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
            st.session_state.logged_in = True
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# 📝 SIGNUP
# ==============================
def signup_page():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.title("📝 Sign Up")

    username = st.text_input("Create Username")
    password = st.text_input("Create Password", type="password")

    if st.button("Register"):
        if not use_mongo:
            st.error("MongoDB not connected")
            return

        if users_collection.find_one({"username": username}):
            st.error("User exists")
        else:
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            users_collection.insert_one({
                "username": username,
                "password": hashed.decode()
            })
            st.success("Account created")

    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# 📝 REGISTER DONOR
# ==============================
def register_donor():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.title("📝 Register Donor")

    name = st.text_input("Name")
    age = st.number_input("Age", 18, 100)
    blood = st.selectbox("Blood Group", ["O+","A+","B+","AB+","O-","A-","B-","AB-"])
    city = st.text_input("City")

    available = st.selectbox("Available", [1, 0])
    last_donation_days = st.number_input("Last Donation Days", 0, 5000)

    email = st.text_input("Email")
    phone = st.text_input("Phone")

    if st.button("Submit"):
        df = pd.read_csv("DATASET.CSV")

        new = pd.DataFrame([{
            "name": name,
            "age": age,
            "blood_group": blood,
            "city": city.title(),
            "available": available,
            "last_donation_days": last_donation_days,
            "email": email,
            "phone": phone
        }])

        df = pd.concat([df, new], ignore_index=True)
        df.to_csv("DATASET.CSV", index=False)

        st.success("Donor Added")

    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# 📊 DASHBOARD
# ==============================
def dashboard():
    st.title("🩸 Blood Donor Dashboard")

    df = pd.read_csv("DATASET.CSV").dropna()
    st.dataframe(df)

    col1, col2 = st.columns(2)
    col1.bar_chart(df['available'].value_counts())
    col2.bar_chart(df['blood_group'].value_counts())

    # ML
    le_bg = LabelEncoder()
    le_city = LabelEncoder()

    df['bg'] = le_bg.fit_transform(df['blood_group'])
    df['city_enc'] = le_city.fit_transform(df['city'])

    X = df[['age','bg','city_enc','last_donation_days']]
    y = df['available']

    X_train, X_test, y_train, y_test = train_test_split(X, y)

    lr = LogisticRegression(max_iter=3000)
    rf = RandomForestClassifier()

    lr.fit(X_train, y_train)
    rf.fit(X_train, y_train)

    # ✅ ONLY MODIFIED PART (WHITE COLOR)
    st.subheader("Model Accuracy")

    lr_acc = accuracy_score(y_test, lr.predict(X_test)) * 100
    rf_acc = accuracy_score(y_test, rf.predict(X_test)) * 100

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="card">
            <h3>Logistic Regression</h3>
            <h2 style="color:white;">{lr_acc:.2f}%</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="card">
            <h3>Random Forest</h3>
            <h2 style="color:white;">{rf_acc:.2f}%</h2>
        </div>
        """, unsafe_allow_html=True)

    # ================= FIND DONOR =================
    st.subheader("🔍 Find Donor")

    bg = st.selectbox("Blood Group", df['blood_group'].unique())
    city = st.text_input("Enter City")

    if st.button("Search Donor"):
        with st.spinner("Finding best donors..."):

            res = df[df['blood_group'] == bg].copy()

            user_coords = get_coordinates(city)

            if not user_coords:
                st.error("Invalid city")
            else:
                distances = []

                for _, r in res.iterrows():
                    donor_coords = get_coordinates(r['city'])

                    if donor_coords:
                        d = get_real_distance(user_coords, donor_coords)
                    else:
                        d = 9999

                    distances.append(d)

                res['Distance'] = distances
                res = res.sort_values(by="Distance")

                st.success("Donors Found")
                st.dataframe(res)

# ==============================
# NAVIGATION
# ==============================
if not st.session_state.logged_in:
    menu = st.sidebar.selectbox("Menu", ["Login", "Sign Up"])
    if menu == "Login":
        login_page()
    else:
        signup_page()
else:
    menu = st.sidebar.selectbox("Menu", ["Home", "Register", "Logout"])
    if menu == "Home":
        dashboard()
    elif menu == "Register":
        register_donor()
    else:
        st.session_state.logged_in = False
        st.rerun()