import streamlit as st
import firebase_admin
import random
from firebase_admin import credentials, auth, firestore
from streamlit_lottie import st_lottie
import json

# Function to load a Lottie JSON file
def load_lottie_file(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)
# Load Lottie animation
lottie_animation = load_lottie_file("C:/SHREYA/Infosys_internship/assets/lottie/profile.json")

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
        width=200,
        key="profile",
    )
else:
    st.error("Lottie animation could not be loaded.")
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

# Initialize Firebase if not already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate('diet-planning-e62ca-cee72236ac11.json')
    firebase_admin.initialize_app(cred)

# Function to check if the user is logged in
def check_login():
    if 'user' not in st.session_state:
        st.error("You must be logged in to view your profile.")
        return False
    return True 

# Firestore initialization
db = firestore.client()

def show_profile():
    st.title('User Profile')

    # Sidebar with Logout Button
    with st.sidebar:
        st.header("User Options")
        if 'user' in st.session_state:
            if st.button("Log Out"):
                # Log out the user
                del st.session_state.user
                st.success("You have been logged out!")
                st.rerun()  # Refresh the page after logout
        else:
            st.info("You are not logged in.")
    
    # Check if user is logged in
    if 'user' not in st.session_state:
        st.error("You must be logged in to view your profile.")
        return

    try:
        # Fetch user details using UID
        user = auth.get_user(st.session_state.user['uid'])  # Get user by UID
        
        # Retrieve user data from Firestore
        user_ref = db.collection('users').document(user.uid)
        user_doc = user_ref.get()
        user_data = user_doc.to_dict() if user_doc.exists else {}

        # Extract the name from UID (adjust this based on your UID format)
        user_name = user_data.get('display_name', user.uid.split('-')[0])  # Fetch display name from Firestore, fallback to UID if missing
        
        # Display User Info
        st.write(f"**😊Hii!** {user_name}")
        st.write(f"**📨** {user.email}")

        # Notes Input Section
        st.subheader("📝 User Notes")
        user_notes = st.text_area("Add a Note", value=user_data.get('notes', ''), height=150)

        if st.button("Save Note"):
            # Save the note in Firestore
            user_ref.set({'notes': user_notes}, merge=True)
            st.success("Note saved successfully!")
            st.balloons()

        # Streaks Tracking
        st.subheader("🔥 Streak Badges")
        streak_days = random.randint(1, 14)  # Mock streak data
        if streak_days >= 7:
            st.success(f"💪 7-Day Streak! Keep going, you're unstoppable!")
        else:
            st.info(f"Current Streak: {streak_days} days. Stay consistent!")

        st.subheader("🏆 Your Achievements")
        st.write("• 7-Day Streak Badge")
        st.write("• Healthy Eating Challenge Completed")

        # Edit Profile Button
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = False

        if not st.session_state.edit_mode:
            if st.button("Edit Profile"):
                st.session_state.edit_mode = True
        else:
            st.subheader("✏️ Edit Profile")
            
            # Edit Username
            new_username = st.text_input("Username", value=user_name)  # Display current name from UID
            
            # Edit Health Condition and Diet Preference
            health_condition = st.text_input("Health Condition", value=user_data.get('health_condition', 'Healthy Living'))
            diet_preference = st.selectbox(
                "Diet Preference", 
                ['Vegetarian', 'Non-Vegetarian', 'Vegan', 'Gluten-Free', 'Paleo'], 
                index=['Vegetarian', 'Non-Vegetarian', 'Vegan', 'Gluten-Free', 'Paleo'].index(user_data.get('diet_preference', 'Vegetarian'))
            )

            # Edit Age, Height, and Weight
            age = st.number_input("Age", value=user_data.get('age', 25), min_value=0)
            height = st.number_input("Height (in cm)", value=user_data.get('height', 160), min_value=0)
            weight = st.number_input("Weight (in kg)", value=user_data.get('weight', 60), min_value=0)

            # Edit Activity Level
            activity_level = st.selectbox(
                "Activity Level", 
                ['Sedentary', 'Light', 'Moderate', 'Active', 'Very Active'],
                index=['Sedentary', 'Light', 'Moderate', 'Active', 'Very Active'].index(user_data.get('activity_level', 'Moderate'))
            )
            
            # Edit Health Goal
            health_goal = st.selectbox(
                "Health Goal", 
                ['Weight Loss', 'Weight Gain', 'Maintain Weight', 'Improve Fitness', 'Healthy Living'],
                index=['Weight Loss', 'Weight Gain', 'Maintain Weight', 'Improve Fitness', 'Healthy Living'].index(user_data.get('health_goal', 'Healthy Living'))
            )

            # Edit Email
            new_email = st.text_input("Email ID", value=user.email)
            
            if st.button("Update Email"):
                try:
                    auth.update_user(user.uid, email=new_email)
                    st.success("Email updated successfully!")
                except Exception as e:
                    st.error(f"Error updating email: {e}")
            
            # Save Changes Button
            if st.button("Save Changes"):
                try:
                    auth.update_user(user.uid, display_name=new_username)
                    st.success("Username updated successfully!")
                    
                except Exception as e:
                    st.error(f"Error updating username: {e}")
                
                # Update the user data in Firestore
                user_ref.set({
                    'health_condition': health_condition,
                    'diet_preference': diet_preference,
                    'age': age,
                    'height': height,
                    'weight': weight,
                    'activity_level': activity_level,
                    'health_goal': health_goal,
                    'display_name': new_username  # Update display name in Firestore
                }, merge=True)
                
                # Refresh user data after saving
                user_doc = user_ref.get()
                user_data = user_doc.to_dict() if user_doc.exists else {}
                
                st.success("Profile updated successfully!")
                st.session_state.edit_mode = False  # Exit edit mode
                st.balloons()

            if st.button("Cancel Edit"):
                st.session_state.edit_mode = False  # Cancel editing without saving

    except Exception as e:
        st.error(f"Error fetching user details: {e}")

# Call the profile function
if __name__ == "__main__":
    show_profile()
