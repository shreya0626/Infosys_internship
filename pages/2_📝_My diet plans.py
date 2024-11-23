import streamlit as st
import firebase_admin
import pandas as pd
from datetime import datetime
from firebase_admin import credentials, firestore, auth
from streamlit_lottie import st_lottie
import json

# Function to load a Lottie JSON file
def load_lottie_file(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)
# Load Lottie animation
lottie_animation = load_lottie_file("C:/SHREYA/Infosys_internship/assets/lottie/diet.json")

# Sidebar Styling
st.sidebar.markdown(
    """
    <style>
    [data-testid="stSidebar"]::before {
        content: "Diet Mate 🥗"; 
        font-size: 24px; 
        font-weight: bold; 
        padding: 120px 90px 0px 30px;
        display: block;
    }
    </style>
    """, 
    unsafe_allow_html=True
)

# Display Lottie animation at the top of the page
if lottie_animation:
    st_lottie(
        lottie_animation,
        speed=1,
        reverse=False,
        loop=True,
        quality="high",
        height=300,
        width=300,
        key="diet",
    )
else:
    st.error("Lottie animation could not be loaded.")
# Sidebar Branding
st.sidebar.markdown(
    """
    <style>
    [data-testid="stSidebar"]::before {
        content: "Diet Mate 🥗"; 
        font-size: 24px; 
        font-weight: bold; 
        padding: 120px 90px 0px 30px;
        display: block;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Firebase Initialization
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate('diet-planning-e62ca-cee72236ac11.json')
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase initialization failed: {e}")

# Initialize Firestore
db = firestore.client()

# Check if the user is logged in
def check_login():
    if 'user_id' not in st.session_state:
        st.error("You must be logged in to view your diet plans.")
        return False
    return True

# Sidebar Profile Options
def show_profile():
    with st.sidebar:
        st.header("User Options")
        if 'user_id' in st.session_state:
            if st.button("Log Out"):
                del st.session_state['user_id']
                st.success("You have been logged out!")
                st.experimental_rerun()
        else:
            st.info("You are not logged in.")

# User Login Function
def login_user(email):
    try:
        user = auth.get_user_by_email(email)
        st.session_state['user_id'] = user.uid
        st.success(f"Logged in as {email}")
        st.rerun()
    except Exception as e:
        st.error(f"Login failed: {e}")

# Fetch Diet Plans from Firestore
def fetch_diet_plans(user_id, selected_date):
    try:
        # Get a reference to the specific document for the selected date
        plan_ref = (
            db.collection('diet_plans')
            .document(user_id)
            .collection('plans')
            .document(selected_date)
        )
        plan_doc = plan_ref.get()
        
        # Check if the document exists
        if plan_doc.exists:
            plan_data = plan_doc.to_dict()
            return plan_data.get('plans', {})
        else:
            st.warning(f"No diet plan found for {selected_date}.")
            return {}
    except Exception as e:
        st.error(f"Error fetching diet plans: {e}")
        return {}

# Transform Diet Plan for Display
def transform_diet_plan(raw_plan):
    if not raw_plan:
        return {"message": "No data available for the selected week."}

    transformed_plan = {}

    # Assuming the data contains weeks with meal data for each day
    for week, data in raw_plan.items():
        days = data.get("Day", [])
        transformed_plan[week] = {}

        meal_types = ["Breakfast", "Lunch", "Dinner", "Snack"]

        for idx, day in enumerate(days):
            meals = {meal_type: data.get(meal_type, [])[idx] if idx < len(data.get(meal_type, [])) else "No suggestion" for meal_type in meal_types}
            transformed_plan[week][day] = meals

    # Sort weeks based on the numeric part (e.g., "Week 1", "Week 2", etc.)
    sorted_plan = dict(sorted(transformed_plan.items(), key=lambda x: int(x[0].split()[-1])))

    return sorted_plan


# Display Diet Plans in Collapsible Format
def display_diet_plan(transformed_plan):
    if "message" in transformed_plan:
        st.warning(transformed_plan["message"])
        return
    
    # Buttons for each week
    week_buttons = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
    selected_week = st.radio("Select a Week", week_buttons)

    # Display the selected week’s diet plan
    if selected_week in transformed_plan:
        week_plan = transformed_plan[selected_week]
        st.header(f"{selected_week} Diet Plan")
        for day, meals in week_plan.items():
            st.subheader(day)
            for meal, suggestion in meals.items():
                st.write(f"**{meal}:** {suggestion}")


# Main App Logic
def main():
    if 'user_id' not in st.session_state:
        email = st.text_input("Please enter your email to view meal plans")
        if email and st.button("Login"):
            login_user(email)
    else:
        show_profile()

        # Date input to select a plan
        selected_date = st.date_input("Select a date", datetime.now()).strftime("%Y-%m-%d")

        # Fetch and transform diet plans
        raw_plan = fetch_diet_plans(st.session_state['user_id'], selected_date)
        transformed_plan = transform_diet_plan(raw_plan)

        # Display the transformed diet plan
        display_diet_plan(transformed_plan)

if __name__ == "__main__":
    main()
