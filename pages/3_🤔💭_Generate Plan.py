import streamlit as st
import pandas as pd
import random
import base64
import os
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
from streamlit_lottie import st_lottie
import json

# Function to load a Lottie JSON file
def load_lottie_file(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

# Load Lottie animation
lottie_animation = load_lottie_file("C:/SHREYA/Infosys_internship/assets/lottie/anime_girl.json")

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
        key="anime_girl",
    )
else:
    st.error("Lottie animation could not be loaded.")

# Firebase initialization
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate('diet-planning-e62ca-cee72236ac11.json')
        firebase_admin.initialize_app(cred)
        st.write("Firebase initialized successfully.")
    except Exception as e:
        st.error(f"Firebase initialization failed: {e}")

# Initialize Firestore
db = firestore.client()

# Function to check login
def check_login():
    if 'user' not in st.session_state:
        st.error("You must be logged in to view your diet plans.")
        return False
    return True

# Load dataset
@st.cache_data(ttl=3600)
def load_data():
    try:
        data_path = 'nutrition_dataset.csv'
        data = pd.read_csv(data_path)
        return data
    except FileNotFoundError:
        st.error("Dataset file not found.")
        return None

nutrition_data = load_data()

unique_conditions = [
    "Weight Loss", "Kidney Disease", "Weight Gain",
    "Hypertension", "Diabetes", "Acne", "Heart Disease"
]

# Function to recommend meals
def recommend_meals_streamlit(name, age, weight, height, dietary_pref, health_conditions):
    if nutrition_data is None:
        st.error("Unable to load nutrition data.")
        return

    # Calculate BMI
    height_m = height / 100
    bmi = weight / (height_m ** 2)
    st.info(f"Your BMI is: **{bmi:.2f}**")
    
    recommendation = (
        "Consider a diet to gain weight." if bmi < 18.5 else
        "Maintain a healthy balanced diet." if 18.5 <= bmi < 24.9 else
        "Consider a weight loss diet plan."
    )
    st.success(recommendation)

    # Generate and display meal plans
    daily_calories = []
    weekly_plans = {}
    for week in range(1, 5):
        weekly_plan = pd.DataFrame({
            "Day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "Breakfast": random.choices(nutrition_data["Breakfast Suggestion"].dropna().tolist(), k=7),
            "Lunch": random.choices(nutrition_data["Lunch Suggestion"].dropna().tolist(), k=7),
            "Dinner": random.choices(nutrition_data["Dinner Suggestion"].dropna().tolist(), k=7),
            "Snack": random.choices(nutrition_data["Snack Suggestion"].dropna().tolist(), k=7),
        })

        # Calculate daily calories
        daily_calories_week = []
        for index, row in weekly_plan.iterrows():
            total_calories = 0
            for meal in ["Breakfast", "Lunch", "Dinner", "Snack"]:
                meal_suggestion = row[meal]
                meal_data = nutrition_data[nutrition_data[['Breakfast Suggestion', 'Lunch Suggestion', 'Dinner Suggestion', 'Snack Suggestion']].eq(meal_suggestion).any(axis=1)]
                if not meal_data.empty:
                    total_calories += meal_data.iloc[0].get('Calories', 0)  # Assume there is a 'Calories' column
            daily_calories_week.append(total_calories)
        
        weekly_plans[f"Week {week}"] = weekly_plan
        daily_calories.append(daily_calories_week)

    # Display the plans
    for week, plan in weekly_plans.items():
        st.write(f"### {week}")
        st.dataframe(plan)

    # Save plans to Firestore by splitting into weekly documents
    user_id = st.session_state.get('user_id', 'guest_user')  # Use guest_user for testing
    try:
        # Prepare the user info
        user_info = {
            'name': name,
            'age': age,
            'weight': weight,
            'height': height,
            'dietary_pref': dietary_pref,
            'health_conditions': health_conditions,
            'created_at': firestore.SERVER_TIMESTAMP  # Use Firestore server timestamp
        }

        # Use the current date as the root document ID
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        user_ref = db.collection('diet_plans').document(user_id).collection('plans').document(current_date)
        
        # Store user info
        user_ref.set({'user_info': user_info})

        # Store each week's plan as a separate document
        for week, plan in weekly_plans.items():
            weekly_data = plan.to_dict(orient='list')  # Convert DataFrame to list of values
            user_ref.collection('weeks').document(week).set(weekly_data)

        st.success(f"Meal plans for {current_date} saved to Firestore!")
    except Exception as e:
        st.error(f"Failed to save to Firestore: {e}")
    
    return sum(sum(day) for day in daily_calories) / (7 * 4)  # Calculate average daily calorie intake for the entire plan

# Main function
def main():
    st.title("Generate Your Personalized Diet Plan")

    if check_login():

        name = st.text_input("Name")
        age = st.number_input("Age", min_value=0, max_value=120, step=1)
        weight = st.number_input("Weight (kg)", min_value=1.0, step=0.1)
        height = st.number_input("Height (cm)", min_value=1.0, step=0.1)

        if nutrition_data is not None:
            dietary_pref = st.selectbox("Dietary Preference", nutrition_data['Dietary Preference'].unique())
            health_conditions = st.multiselect("Health Conditions", unique_conditions)
        else:
            dietary_pref, health_conditions = None, []

        if st.button("Generate Plan"):
            if name and age and weight and height:
                daily_calorie_target = recommend_meals_streamlit(name, age, weight, height, dietary_pref, health_conditions)
                st.write(f"**📊 Your Average Daily Calorie Target is: {daily_calorie_target:.2f} kcal**")
            else:
                st.error("Please fill all the required fields.")
    else:
        return

if __name__ == "__main__":
    main()
