# ==============================
# 🩸 Smart Blood Donor System
# ==============================

import streamlit as st
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

st.set_page_config(page_title="Blood Donor App", layout="centered")

# ==============================
# SESSION STATE
# ==============================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ==============================
# LOGIN PAGE
# ==============================

def login_page():
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "1234":
            st.session_state.logged_in = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials")

# ==============================
# REGISTER PAGE
# ==============================

def register_page():
    st.title("📝 Register as Donor")

    name = st.text_input("Name")
    age = st.number_input("Age", min_value=1, max_value=100)
    blood_group = st.selectbox("Blood Group", ["O+","A+","B+","AB+","O-","A-","B-","AB-"])
    city = st.text_input("City")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")

    if st.button("Register"):

        if age <= 18:
            st.error("❌ Age must be greater than 18")

        elif name.strip() == "" or city.strip() == "" or email.strip() == "" or phone.strip() == "":
            st.warning("⚠️ Please fill all fields")

        else:
            new_data = pd.DataFrame([{
                "name": name,
                "age": age,
                "blood_group": blood_group,
                "city": city,
                "available": 1,
                "last_donation_days": 0,
                "email": email,
                "phone": phone
            }])

            df = pd.read_csv("DATASET.CSV")
            df = pd.concat([df, new_data], ignore_index=True)
            df.to_csv("DATASET.csv", index=False)

            st.success("✅ Registered Successfully!")

# ==============================
# DASHBOARD
# ==============================

def dashboard():

    df = pd.read_csv("DATASET.csv")
    st.dataframe(df)
    df = df.dropna()

    # Encoding
    le_bg = LabelEncoder()
    le_city = LabelEncoder()

    df['blood_group_encoded'] = le_bg.fit_transform(df['blood_group'])
    df['city_encoded'] = le_city.fit_transform(df['city'])

    X = df[['age', 'blood_group_encoded', 'city_encoded', 'last_donation_days']]
    y = df['available']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Models
    lr = LogisticRegression(max_iter=1000)
    rf = RandomForestClassifier()

    lr.fit(X_train, y_train)
    rf.fit(X_train, y_train)

    lr_acc = accuracy_score(y_test, lr.predict(X_test))
    rf_acc = accuracy_score(y_test, rf.predict(X_test))

    # Compatibility
    def is_compatible(donor_bg, patient_bg):
        compatibility = {
            "O-": ["O-", "O+", "A+", "A-", "B+", "B-", "AB+", "AB-"],
            "O+": ["O+", "A+", "B+", "AB+"],
            "A-": ["A-", "A+", "AB-", "AB+"],
            "A+": ["A+", "AB+"],
            "B-": ["B-", "B+", "AB-", "AB+"],
            "B+": ["B+", "AB+"],
            "AB-": ["AB-", "AB+"],
            "AB+": ["AB+"]
        }
        return patient_bg in compatibility.get(donor_bg, [])

    # UI
    st.title("🩸 Blood Donor Recommendation System")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Availability")
        counts = df['available'].value_counts().sort_index()
        counts.index = ["Not Available", "Available"]
        st.bar_chart(counts)

    with col2:
        st.subheader("Blood Groups")
        st.bar_chart(df['blood_group'].value_counts())

    st.subheader("Model Accuracy")
    c1, c2 = st.columns(2)
    c1.metric("Logistic Regression", f"{lr_acc:.2f}")
    c2.metric("Random Forest", f"{rf_acc:.2f}")

    st.subheader("Find Donors")

    age = st.number_input("Age", 1, 100)
    blood_group = st.selectbox("Blood Group", df['blood_group'].unique())
    city = st.selectbox("City", df['city'].unique())

    if st.button("Search"):

        compatible = df[df['blood_group'].apply(
            lambda x: is_compatible(x, blood_group)
        )]

        if compatible.empty:
            st.error("❌ No donors found")
        else:
            # Encode selected city
            selected_city_encoded = le_city.transform([city])[0]

            results = []

            for _, row in compatible.iterrows():

                # Calculate "distance"
                distance = abs(row['city_encoded'] - selected_city_encoded)

                input_data = pd.DataFrame([{
                    'age': row['age'],
                    'blood_group_encoded': row['blood_group_encoded'],
                    'city_encoded': row['city_encoded'],
                    'last_donation_days': row['last_donation_days']
                }])

                prob = rf.predict_proba(input_data)[0][1]

                results.append([
                    row['name'],
                    row['age'],
                    row['blood_group'],
                    row['city'],
                    row.get('email', 'N/A'),
                    row.get('phone', 'N/A'),
                    round(prob, 2),
                    distance,
                    "Yes" if row['available'] == 1 else "No"
                ])

            result_df = pd.DataFrame(results, columns=[
                "Name", "Age", "Blood Group", "City",
                "Email", "Phone", "Score", "Distance", "Available"
            ])

            # Sort by nearest city first, then by score
            result_df = result_df.sort_values(by=["Distance", "Score"], ascending=[True, False])

            st.subheader("📍 Recommended Donors (Nearest City First)")
            st.dataframe(result_df)

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# ==============================
# NAVIGATION
# ==============================

menu = st.sidebar.selectbox("Menu", ["Login", "Register"])

if menu == "Register":
    register_page()
elif not st.session_state.logged_in:
    login_page()
else:
    dashboard()