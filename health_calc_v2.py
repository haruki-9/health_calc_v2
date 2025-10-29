#(Version 2)

import streamlit as st
import requests
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import re
import hashlib
from datetime import datetime, timedelta
import time

# ---------- Admin Config ----------
ADMIN_PASSWORD = "Admin2233"  # Change this to a secure password
USERS_FILE = "users.csv"

st.set_page_config(page_title="Health Assistant Dashboard", layout="centered")

# ---------- Session State Initialization ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# ---------- User Registration & Login ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def save_user(username, password):
    hashed_pw = hash_password(password)
    df = pd.DataFrame([[username, hashed_pw]], columns=["username", "password"])
    if os.path.exists(USERS_FILE):
        df.to_csv(USERS_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(USERS_FILE, index=False)

def check_user(username, password):
    if not os.path.exists(USERS_FILE):
        return False
    df = pd.read_csv(USERS_FILE)
    hashed_pw = hash_password(password)
    if 'username' not in df.columns or 'password' not in df.columns:
        return False
    return ((df['username'] == username) & (df['password'] == hashed_pw)).any()

# ---------- LOGIN/SIGNUP PAGE ----------
if not st.session_state.logged_in:
    st.title("💪 Health Assistant Dashboard")
    st.write("Welcome! Please login or sign up to continue.")
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    with tab1:
        st.subheader("Login to Your Account")
        username_login = st.text_input("Username", key="login_user")
        password_login = st.text_input("Password", type="password", key="login_pass")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login", use_container_width=True):
                if check_user(username_login, password_login):
                    st.session_state.logged_in = True
                    st.session_state.username = username_login
                    st.success(f"Welcome back, {username_login}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        
        with col2:
            # Admin login option
            if st.button("Admin Login", use_container_width=True):
                admin_pass = st.text_input("Enter admin password", type="password", key="admin_login")
                if admin_pass == ADMIN_PASSWORD:
                    st.session_state.is_admin = True
                    st.session_state.logged_in = True
                    st.session_state.username = "Admin"
                    st.success("Admin access granted.")
                    st.rerun()
                elif admin_pass:
                    st.error("Incorrect admin password.")
    
    with tab2:
        st.subheader("Create New Account")
        username_reg = st.text_input("Choose Username", key="reg_user")
        password_reg = st.text_input("Choose Password", type="password", key="reg_pass")
        password_confirm = st.text_input("Confirm Password", type="password", key="reg_pass_confirm")
        
        if st.button("Sign Up", use_container_width=True):
            if not username_reg or not password_reg:
                st.warning("Please enter both username and password.")
            elif password_reg != password_confirm:
                st.error("Passwords do not match!")
            else:
                if os.path.exists(USERS_FILE):
                    existing = pd.read_csv(USERS_FILE)
                    if 'username' not in existing.columns:
                        st.error("Corrupted user file. Please contact admin.")
                    elif username_reg in existing['username'].values:
                        st.error("Username already exists. Please choose another.")
                    else:
                        save_user(username_reg, password_reg)
                        st.success("Registration successful! You can now log in.")
                else:
                    save_user(username_reg, password_reg)
                    st.success("Registration successful! You can now log in.")
    
    st.stop()  # Stop here if not logged in

# ---------- MAIN DASHBOARD (Only shown after login) ----------
st.title("💪 Health Assistant Dashboard")
st.write(f"Welcome, **{st.session_state.username}**! Choose a tool from the sidebar.")

# Logout button in sidebar
with st.sidebar:
    st.write(f"👤 Logged in as: **{st.session_state.username}**")
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.is_admin = False
        st.rerun()
    st.markdown("---")

# Determine available tools based on admin status
if st.session_state.get("is_admin"):
    tools = [
        "Ideal Body Weight Calculator",
        "Exercise Planner",
        "Nutrition Analyzer",
        "Symptom Checker",
        "📊 Health Charts",
        "My Wellness Planner",
        "🔬 View Feedback"
    ]
else:
    tools = [
        "Ideal Body Weight Calculator",
        "Exercise Planner",
        "Nutrition Analyzer",
        "Symptom Checker",
        "📊 Health Charts",
        "My Wellness Planner"
    ]

# Sidebar options
tool = st.sidebar.selectbox("Choose a tool", tools)

# ---------- Wellness Planner ----------
def load_wellness_tasks():
    file = f"planner_{st.session_state.username}.csv"
    if os.path.exists(file):
        df = pd.read_csv(file)
        required_cols = ["task", "completed", "timestamp", "last_updated"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = "" if col != "completed" else False
        return df[required_cols]
    return pd.DataFrame(columns=["task", "completed", "timestamp", "last_updated"])

def save_wellness_tasks(df):
    file = f"planner_{st.session_state.username}.csv"
    df.to_csv(file, index=False)

if tool == "My Wellness Planner":
    st.header("🧘 My Wellness Planner")
    df_tasks = load_wellness_tasks()

    # Auto-reset daily task completion
    try:
        last_updated = pd.to_datetime(df_tasks['last_updated'][0]).date()
        today = datetime.now().date()
        if last_updated != today:
            df_tasks['completed'] = False
            df_tasks['last_updated'] = datetime.now().isoformat()
            save_wellness_tasks(df_tasks)
    except:
        pass

    with st.form("add_task_form"):
        new_task = st.text_input("Add a new wellness task")
        duration = st.number_input("Time (in minutes) to complete this task", min_value=1, max_value=1440, value=30)
        submit = st.form_submit_button("Add Task")
        if submit and new_task:
            deadline = (datetime.now() + timedelta(minutes=duration)).isoformat()
            df_tasks = df_tasks[["task", "completed", "timestamp", "last_updated"]]
            df_tasks.loc[len(df_tasks)] = [new_task, False, datetime.now().isoformat(), datetime.now().isoformat()]
            save_wellness_tasks(df_tasks)
            st.success("Task added!")

    for idx, row in df_tasks.iterrows():
        col1, col2 = st.columns([0.1, 0.9])
        with col1:
            if st.checkbox("", key=f"task_{idx}", value=row['completed']):
                df_tasks.at[idx, 'completed'] = True
        with col2:
            task_text = row['task']
            task_time = pd.to_datetime(row['timestamp'])
            time_left = (task_time + timedelta(minutes=30)) - datetime.now()
            if time_left.total_seconds() > 0:
                st.markdown(f"**{task_text}** ⏳ Time left: `{str(time_left).split('.')[0]}`")
            else:
                st.markdown(f"**{task_text}** ❌ Time's up!")

    save_wellness_tasks(df_tasks)

    st.markdown("---")
    st.subheader("🏋 Weekly & Monthly Badges")
    completed = df_tasks[df_tasks['completed'] == True]

    badge_history_file = f"badges_{st.session_state.username}.csv"

    if os.path.exists(badge_history_file):
        badge_history = pd.read_csv(badge_history_file)
    else:
        badge_history = pd.DataFrame(columns=["badge", "date"])

    unlocked = []
    if len(completed) >= 5:
        unlocked.append("🥇 Week 1 Champ")
    if len(completed) >= 20:
        unlocked.append("🏆 Month Champ")

    for badge in unlocked:
        if badge not in badge_history['badge'].values:
            badge_history.loc[len(badge_history)] = [badge, datetime.now().isoformat()]
            st.success(f"{badge} Badge Unlocked!")

    badge_history.to_csv(badge_history_file, index=False)

    with st.expander("📜 View Badge History"):
        if len(badge_history):
            for i, row in badge_history.iterrows():
                st.markdown(f"{row['badge']} — _earned on {row['date'].split('T')[0]}_")
        else:
            st.info("No badges earned yet.")

    with st.expander("🔮 Sneak Peek: Upcoming Badges"):
        st.markdown("- Complete 5 tasks: 🥇 Week 1 Champ")
        st.markdown("- Complete 20 tasks: 🏆 Month Champ")

# Utilities

def height_to_inches(height_str):
    try:
        if "'" in height_str:
            feet, inches = height_str.split("'")
            inches = inches.replace('"', '').strip()
            return int(feet) * 12 + int(inches)
        elif "ft" in height_str:
            parts = height_str.lower().replace("in", "").split("ft")
            feet = int(parts[0].strip())
            inches = int(parts[1].strip()) if len(parts) > 1 else 0
            return feet * 12 + inches
    except:
        return None

def convert_height_to_cm(height_str):
    feet = 0
    inches = 0
    match1 = re.match(r"(\d+)'(\d+)", height_str)
    match2 = re.match(r"(\d+)\s*ft\s*(\d*)\s*in*", height_str)

    if match1:
        feet = int(match1.group(1))
        inches = int(match1.group(2))
    elif match2:
        feet = int(match2.group(1))
        inches = int(match2.group(2)) if match2.group(2) else 0
    else:
        return None

    total_inches = feet * 12 + inches
    return round(total_inches * 2.54, 2)

# Initialize scores
if 'nutrition_score' not in st.session_state:
    st.session_state.nutrition_score = 0
if 'exercise_score' not in st.session_state:
    st.session_state.exercise_score = 0

# Tool: IBW
if tool == "Ideal Body Weight Calculator":
    st.header("🏋️ Ideal Body Weight (IBW) Calculator")
    height_str = st.text_input("Enter your height (e.g., 5'7 or 5 ft 7 in)")
    gen = st.selectbox("Select your gender", options=["-- Select --", "male", "female"])
    if gen == "-- Select --":
        gen = None

    if st.button("Calculate IBW"):
        height_in = height_to_inches(height_str)
        if height_in is None:
            st.error("Please enter a valid height.")
        elif gen is None:
            st.error("Please select a gender.")
        else:
            base_height = 60
            if gen == "male":
                ibw = 50 + 2.3 * (height_in - base_height) if height_in > base_height else 50
            else:
                ibw = 45.5 + 2.3 * (height_in - base_height) if height_in > base_height else 45.5
            st.success(f"Your Ideal Body Weight is approximately {ibw:.2f} kg")

# Tool: Exercise Planner
elif tool == "Exercise Planner":
    st.header("🧘 Exercise Planner")
    age = st.number_input("Enter your age", min_value=1, max_value=120, step=1)
    gen = st.selectbox("Select your gender", options=["-- Select --", "male", "female"])
    if gen == "-- Select --":
        gen = None

    height_str = st.text_input("Enter your height (e.g., 5'7 or 5 ft 7 in)")
    weight = st.number_input("Enter your weight in kg", min_value=10.0, max_value=300.0, step=0.1)
    goal = st.selectbox("What's your fitness goal?", ["Weight Loss", "Muscle Gain", "General Fitness", "Flexibility & Stress Relief"])

    if st.button("Get Plan"):
        height_in = height_to_inches(height_str)
        if height_in is None:
            st.error("Please enter a valid height.")
        elif gen is None:
            st.error("Please select a gender.")
        else:
            st.success("Here's your recommended fitness plan:")

            if goal == "Weight Loss":
                st.markdown("""
                - **Cardio:** 5 days/week — 30 to 45 minutes/session  
                - **Strength Training:** 2–3 days/week  
                - **Diet Tip:** Stay in calorie deficit.  
                - **Recovery:** 7–8 hours sleep, hydration (2.5–3 L/day)  
                """)
            elif goal == "Muscle Gain":
                st.markdown("""
                - **Strength Training:** 4–5 days/week  
                - **Protein Intake:** Include dal, paneer, eggs, chicken, sprouts  
                - **Rest & Recovery:** Sleep 8 hrs/night  
                - **Cardio:** Light cardio 2x/week  
                """)
            elif goal == "General Fitness":
                st.markdown("""
                - **Routine Mix:** Cardio + strength + flexibility (3–4x/week)  
                - **Examples:** Walking, yoga, home circuits  
                - **Diet:** Whole grains, local veggies, pulses  
                """)
            elif goal == "Flexibility & Stress Relief":
                st.markdown("""
                - **Yoga & Stretching:** 4–5x/week  
                - **Breathing & Meditation:** Daily  
                - **Supplemental:** Walks, music meditation  
                """)

            st.session_state.exercise_score = 25

# Tool: Nutrition Analyzer
elif tool == "Nutrition Analyzer":
    st.header("🍽️ Nutrition Analyzer")
    st.write("This tool estimates your daily caloric needs and suggests a South Indian-style diet plan.")

    age = st.number_input("Enter your age", min_value=1, max_value=120, step=1)
    gen = st.selectbox("Select your gender", options=["-- Select --", "male", "female"])
    height_str = st.text_input("Enter your height (e.g., 5'7 or 5 ft 7 in)")
    weight = st.number_input("Enter your weight in kg", min_value=10.0, max_value=300.0, step=0.1)
    diet_type = st.radio("Are you vegan or non-vegan?", ["non-vegan", "vegan"])

    if st.button("Analyze Diet Plan"):
        if gen == "-- Select --":
            st.error("Please select a gender.")
        elif not height_str:
            st.error("Please enter your height.")
        else:
            height_cm = convert_height_to_cm(height_str)
            if height_cm is None:
                st.error("Invalid height format. Please use formats like 5'7 or 5 ft 7 in.")
            else:
                bmr = 10 * weight + 6.25 * height_cm - 5 * age + (5 if gen == "male" else -161)
                caloric_needs = int(bmr * 1.2)
                st.success("Nutrition analysis complete!")
                st.write(f"Your estimated daily caloric need is **{caloric_needs} calories**.")

                st.subheader(f"Here's a sample {diet_type} South Indian-style diet plan:")
                if diet_type == "non-vegan":
                    st.markdown("""
                    - **Breakfast:** Boiled egg with poha, Banana with milk
                    - **Lunch:** Fish gravy with rice, Chicken curry with roti
                    - **Dinner:** Fish fry with chapati, Egg masala with jowar roti
                    """)
                else:
                    st.markdown("""
                    - **Breakfast:** Millet dosa with coconut chutney, Salad with toasted paneer
                    - **Lunch:** Roti with paneer & mushroom curry, Brown rice with dal
                    - **Dinner:** Steamed vegetables and nuts, Salad with channa, rajma, sprouts
                    """)

                st.session_state.nutrition_score = 25

# Tool: Symptom Checker
elif tool == "Symptom Checker":
    st.header("🤔 Symptom Checker")
    symptoms = ["headache", "fatigue", "cold", "fever", "vomiting", "dizziness", "dehydration", "diarrhea", "sunburn", "heat rash", "muscle cramps", "nausea", "sore throat"]

    symptom_info = {
        "headache": ("Dehydration, stress", "Drink water, rest."),
        "fatigue": ("Lack of sleep", "Get proper rest."),
        "cold": ("Viral Infection", "Take rest, drink fluids."),
        "fever": ("Infection", "Use paracetamol."),
        "vomiting": ("Food poisoning", "Use ORS, avoid solid food."),
        "dizziness": ("Low BP", "Sit down, drink fluids."),
        "dehydration": ("Low fluids", "Drink ORS."),
        "diarrhea": ("Contaminated food", "Hydrate."),
        "sunburn": ("UV exposure", "Use aloe vera."),
        "heat rash": ("Blocked sweat glands", "Keep cool."),
        "muscle cramps": ("Overuse", "Stretch, hydrate."),
        "nausea": ("Indigestion", "Rest, sip fluids."),
        "sore throat": ("Infection", "Gargle,drink warm fluids.")
    }

    selected = st.multiselect("Select symptoms", symptoms)
    st.session_state.selected_symptoms = selected

    if selected:
        for sym in selected:
            cause, solution = symptom_info.get(sym, ("Unknown", "Consult a doctor."))
            st.subheader(sym.capitalize())
            st.write(f"**Cause:** {cause}")
            st.write(f"**Solution:** {solution}")

        symptom_score = max(50 - len(selected) * 5, 0)
        total_score = symptom_score + st.session_state.nutrition_score + st.session_state.exercise_score

        st.markdown("---")
        st.header("🌟 Your Overall Wellness Score")
        st.write(f"**Symptom Score:** {symptom_score}/50")
        st.write(f"**Nutrition Score:** {st.session_state.nutrition_score}/25")
        st.write(f"**Exercise Score:** {st.session_state.exercise_score}/25")
        st.success(f"✅ Total Score: {total_score}/100")

# Tool: 📊 Health Charts
elif tool == "📊 Health Charts":
    st.header("📊 Visualize Your Health Scores")

    symptom_score = max(50 - len(st.session_state.get("selected_symptoms", [])) * 5, 0) if "selected_symptoms" in st.session_state else 50
    nutrition_score = st.session_state.get("nutrition_score", 0)
    exercise_score = st.session_state.get("exercise_score", 0)
    total_score = symptom_score + nutrition_score + exercise_score

    # Pie Chart
    st.subheader("🥧 Score Distribution - Pie Chart")
    pie_labels = ['Symptom', 'Nutrition', 'Exercise']
    pie_values = [symptom_score, nutrition_score, exercise_score]
    fig1, ax1 = plt.subplots()
    ax1.pie(pie_values, labels=pie_labels, autopct='%1.1f%%', startangle=90, colors=['#ff9999', '#66b3ff', '#99ff99'])
    ax1.axis('equal')
    st.pyplot(fig1)

    # Bar Chart
    st.subheader("📊 Score Comparison - Bar Chart")
    fig2, ax2 = plt.subplots()
    categories = ['Symptom\n(/50)', 'Nutrition\n(/25)', 'Exercise\n(/25)']
    values = [symptom_score, nutrition_score, exercise_score]
    ax2.bar(categories, values, color=['#ff9999', '#66b3ff', '#99ff99'])
    ax2.set_ylabel('Score')
    ax2.set_title('Health Score Breakdown')
    st.pyplot(fig2)

    # Radar Chart
    st.subheader("🕸️ Health Score Radar")
    categories = ['Symptom', 'Nutrition', 'Exercise']
    values = [symptom_score, nutrition_score, exercise_score]
    values += values[:1]  # Complete the circle
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]

    fig3, ax3 = plt.subplots(subplot_kw=dict(polar=True))
    ax3.plot(angles, values, color='teal', linewidth=2)
    ax3.fill(angles, values, color='teal', alpha=0.3)
    ax3.set_yticklabels([])
    ax3.set_xticks(angles[:-1])
    ax3.set_xticklabels(categories)
    ax3.set_title("Health Score Radar", y=1.1)
    st.pyplot(fig3)

    st.markdown("---")
    st.write(f"**Symptom Score:** {symptom_score}/50")
    st.write(f"**Nutrition Score:** {nutrition_score}/25")
    st.write(f"**Exercise Score:** {exercise_score}/25")
    st.success(f"✅ Total Wellness Score: {total_score}/100")

# Tool: 🔬 View Feedback (Admin Only)
elif tool == "🔬 View Feedback" and st.session_state.get("is_admin"):
    st.header("🔬 User Feedback")
    if os.path.exists("feedback.csv"):
        df = pd.read_csv("feedback.csv")
        st.dataframe(df)
    else:
        st.info("No feedback received yet.")

# Floating Feedback Button
st.markdown("""
    <style>
        #feedback-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background-color: #f63366;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 16px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            z-index: 100;
        }
    </style>
    <script>
        function showForm() {
            var el = window.parent.document.querySelector("details[open]");
            if (!el) {
                window.parent.document.querySelector("details").setAttribute("open", "true");
            }
        }
    </script>
    <button id="feedback-btn" onclick="showForm()">Feedback</button>
""", unsafe_allow_html=True)

with st.expander("Submit Feedback"):
    st.subheader("📝 We'd love your feedback!")
    name = st.text_input("Your Name (optional)")
    rating = st.slider("Rate your experience (1-5)", 1, 5, 3)
    comment = st.text_area("Comments")

    if st.button("Submit Feedback"):
        feedback_entry = {
            "Name": name if name else "Anonymous",
            "Rating": rating,
            "Comment": comment,
            "Timestamp": datetime.now().isoformat()
        }

        df = pd.DataFrame([feedback_entry])

        if os.path.exists("feedback.csv"):
            df.to_csv("feedback.csv", mode='a', header=False, index=False)
        else:
            df.to_csv("feedback.csv", index=False)

        st.success("Thank you for your feedback!")
