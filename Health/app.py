import streamlit as st
import requests
from typing import List, Optional, Literal
from pydantic import BaseModel, ValidationError


# --- Helper function to parse comma-separated strings into lists ---
def parse_list_input(text_input: str) -> List[str]:
    """Splits a comma-separated string into a list of stripped strings, handling empty input."""
    if not text_input:
        return []
    return [item.strip() for item in text_input.split(',') if item.strip()]

# --- NEW: Function to display the Diet Plan ---
def display_diet_plan(plan_data):
    """Renders the diet plan JSON response in a user-friendly format."""
    st.subheader("📅 Your Generated Diet Plan")

    if not plan_data or 'days' not in plan_data or not plan_data['days']:
        st.warning("No diet plan days were generated or the format is unexpected.")
        st.json(plan_data) # Show raw data if structure is wrong
        return

    # Define meal order and corresponding emojis
    meal_order = ["breakfast", "snack", "lunch", "dinner"]
    meal_emojis = {
        "breakfast": "🍳",
        "snack": "🍎",
        "lunch": "🥗",
        "dinner": "🍲"
    }

    for day_info in plan_data['days']:
        day_number = day_info.get("day_number", "N/A")
        total_calories = day_info.get("total_calories", "N/A")

        with st.expander(f"Day {day_number} (Approx. {total_calories} kcal)", expanded=day_number == 1): # Expand Day 1 by default
            st.markdown(f"#### Plan for Day {day_number}")

            # Iterate through meals in a defined order
            for meal_key in meal_order:
                meal = day_info.get(meal_key)
                if meal: # Check if the meal exists for the day
                    meal_type = meal.get("meal_type", meal_key.capitalize())
                    calories = meal.get("calories", "N/A")
                    food_items = meal.get("food_items", [])
                    meal_notes = meal.get("notes")
                    emoji = meal_emojis.get(meal_key, "🍽️")

                    st.markdown(f"**{emoji} {meal_type} ({calories} kcal)**")

                    if food_items:
                        for item in food_items:
                            name = item.get("name", "Unknown Item")
                            quantity = item.get("quantity", "")
                            item_notes = item.get("notes")

                            display_text = f"- {name}"
                            if quantity:
                                display_text += f" ({quantity})"
                            st.markdown(display_text)

                            if item_notes:
                                st.markdown(f"  *Notes: {item_notes}*")
                    else:
                        st.markdown("- *No specific food items listed.*")

                    if meal_notes:
                        st.markdown(f"*Meal Notes: {meal_notes}*")

                    st.markdown("---") # Separator between meals

            st.markdown(f"**Total Estimated Calories for Day {day_number}: {total_calories} kcal**")
import streamlit as st
# Make sure your Pydantic models (or at least their structure) are implicitly known
# or defined/imported in this file if you want type hints, though not strictly required
# for the display function itself.

def display_fitness_plan(plan_data):
    """Renders the fitness plan JSON response in a user-friendly format."""
    st.subheader("🏋️ Your Generated Fitness Plan")

    if not plan_data or 'workout_days' not in plan_data or not plan_data['workout_days']:
        st.warning("No workout days were generated or the format is unexpected.")
        st.json(plan_data) # Show raw data if structure is wrong
        return

    # Sort days just in case they come out of order
    workout_days = sorted(plan_data.get('workout_days', []), key=lambda x: x.get('day', 0))

    for day_info in workout_days:
        day_number = day_info.get("day", "N/A")
        focus = day_info.get("focus", "Workout")
        day_notes = day_info.get("notes")

        # Use day number and focus in the expander title
        with st.expander(f"Day {day_number}: {focus}", expanded=(day_number == 1)): # Expand Day 1 by default
            st.markdown(f"#### Day {day_number} - Focus: {focus}")

            # --- Warm-up ---
            warmup_list = day_info.get('warmup', [])
            if warmup_list:
                st.markdown("**🤸 Warm-up:**")
                for item in warmup_list:
                    st.markdown(f"- {item}")
            else:
                st.markdown("**🤸 Warm-up:** *No specific warm-up listed.*")
            st.markdown("---") # Separator

            # --- Exercises ---
            exercises_list = day_info.get('exercises', [])
            if exercises_list:
                st.markdown("**💪 Exercises:**")
                for exercise in exercises_list:
                    ex_name = exercise.get("name", "Unknown Exercise")
                    ex_sets = exercise.get("sets", "N/A")
                    ex_reps = exercise.get("reps", "N/A")
                    ex_equip = exercise.get("equipment", "N/A")
                    ex_notes = exercise.get("notes")

                    # Display core exercise info
                    st.markdown(f"**{ex_name}**: {ex_sets} sets x {ex_reps} reps")

                    # Display equipment if available
                    if ex_equip and ex_equip.lower() not in ['none', 'n/a','bodyweight only']:
                         st.markdown(f"  *Equipment: {ex_equip}*")
                    elif ex_equip: # Still show if it explicitly says None/Bodyweight
                         st.markdown(f"  *Equipment: {ex_equip}*")


                    # Display exercise notes if available
                    if ex_notes:
                        st.markdown(f"  *Notes: {ex_notes}*")

                    st.markdown("---") # Separator between exercises
            else:
                 st.markdown("**💪 Exercises:** *No specific exercises listed.*")
                 st.markdown("---") # Separator

            # --- Cool-down ---
            cooldown_list = day_info.get('cooldown', [])
            if cooldown_list:
                st.markdown("**🧘 Cool-down:**")
                for item in cooldown_list:
                    st.markdown(f"- {item}")
            else:
                st.markdown("**🧘 Cool-down:** *No specific cool-down listed.*")
            st.markdown("---") # Separator

            # --- Overall Day Notes ---
            if day_notes:
                st.markdown(f"**📝 Overall Notes for Day {day_number}:** {day_notes}")
# --- Streamlit App ---
st.set_page_config(layout="wide")
st.title("Eunoia - Your Personalized Health Assistant")

# --- API Configuration ---
api_base_url = "http://127.0.0.1:8000"

# --- General User Information ---
st.header("👤 General Information")
# (Keep the general info input section exactly as before)
with st.container(border=True): # Use border for better visual grouping
    col1, col2, col3 = st.columns(3)
    with col1:
        user_name = st.text_input("Name", key="gen_name")
    with col2:
        user_age = st.number_input("Age", min_value=1, max_value=120, step=1, key="gen_age")
    with col3:
        user_gender = st.selectbox("Gender", ['Female', 'Male'], key="gen_gender")

    user_known_conditions = st.text_area(
        "Known Medical Conditions (Optional, comma-separated)",
        key="gen_known_cond",
        help="List any diagnosed conditions, e.g., Hypertension, Asthma"
    )
    user_chronic_conditions = st.text_area(
        "Chronic Conditions (Optional, comma-separated)",
        key="gen_chronic_cond",
        help="List any ongoing health conditions, e.g., Diabetes Type 2, Arthritis"
    )


# --- Functionality Tabs ---
tab_diet, tab_fitness, tab_mental, tab_chronic = st.tabs([
    "🥗 Diet Plan", "🏃 Fitness Plan", "🧠 Mental Wellness Support", "🩺 Chronic Condition Support"
])

# --- Diet Plan Tab ---
with tab_diet:
    st.header("🥗 Diet Plan Generator")
    st.markdown("Provide your dietary details to generate a personalized meal plan.")

    with st.form("diet_form"):
        st.subheader("Dietary Preferences & Needs")
        col1, col2 = st.columns(2)
        with col1:
            diet_pref = st.selectbox(
                "Dietary Preferences",
                ['None', 'Vegan', 'Vegetarian', 'Keto', 'Paleo', 'Gluten-Free'],
                index=0, # Default to 'None'
                key="diet_pref"
            )
            diet_calories = st.number_input(
                "Target Daily Calories",
                min_value=800, max_value=10000, step=50, value=2000, key="diet_cal"
            )
            diet_cooking_time = st.selectbox(
                "Preferred Cooking Time Per Meal",
                ['<30 mins', '30-45 mins', '45-60 mins', '>60 mins'],
                key="diet_cook_time"
            )
            diet_budget = st.selectbox(
                "Food Budget Preference",
                ['Budget-friendly', 'Moderate', 'Flexible'],
                key="diet_budget"
            )
        with col2:
             diet_allergies_str = st.text_area(
                 "Allergies (comma-separated)",
                 placeholder="e.g., Peanuts, Shellfish, Soy",
                 key="diet_allergy"
            )
             diet_intolerances_str = st.text_area(
                 "Food Intolerances (comma-separated)",
                 placeholder="e.g., Lactose, Gluten (if not preference)",
                 key="diet_intol"
            )
             diet_disliked_foods_str = st.text_area(
                 "Disliked Foods (comma-separated)",
                 placeholder="e.g., Mushrooms, Olives, Cilantro",
                 key="diet_dislike"
            )

        submit_diet = st.form_submit_button("Generate Diet Plan")

    if submit_diet:
        # --- Validate General Info ---
        if not user_name or user_age <= 0:
             st.error("Please provide your Name and a valid Age in the General Information section.")
        else:
            # --- Prepare Data ---
            general_data = {
                "name": user_name,
                "age": user_age,
                "gender": user_gender,
                "known_conditions": user_known_conditions or None,
                "chronic_conditions": user_chronic_conditions or None
            }
            diet_data = {
                "preferences": diet_pref if diet_pref != 'None' else None,
                "calories": diet_calories,
                "allergies": parse_list_input(diet_allergies_str),
                "intolerances": parse_list_input(diet_intolerances_str),
                "disliked_foods": parse_list_input(diet_disliked_foods_str),
                "cooking_time_preference": diet_cooking_time,
                "budget_preference": diet_budget
            }
            payload = {"general_user": general_data, "diet_user": diet_data}

            # --- Call API ---
            endpoint = f"{api_base_url}/diet-plan/"
            st.info(f"Sending request to: {endpoint}")
            # st.json(payload) # Optional: Keep for debugging if needed

            try:
                with st.spinner("Generating your diet plan..."):
                    response = requests.post(endpoint, json=payload)
                    response.raise_for_status()

                    result = response.json()

                    # --- <<< CHANGE HERE: Use the new display function >>> ---
                    display_diet_plan(result)
                    # --- <<< End of Change >>> ---

                    # Optional: Display raw JSON for debugging if needed
                    # with st.expander("Show Raw API Response"):
                    #    st.json(result)


            except requests.exceptions.ConnectionError:
                st.error(f"Connection Error: Could not connect to the API at {api_base_url}. Is the backend running?")
            except requests.exceptions.HTTPError as e:
                st.error(f"HTTP Error: {e.response.status_code} - {e.response.reason}")
                try:
                    st.error(f"API Response: {e.response.json()}")
                except ValueError:
                    st.error(f"API Response: {e.response.text}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                # Also display the raw result if an error happens during display
                st.error("Raw data received (if any):")
                # Check if 'result' was assigned before the error
                if 'result' in locals():
                     st.json(result)
                else:
                     st.write("Could not retrieve result from API.")


# --- Fitness Plan Tab (Keep as before) ---
with tab_fitness:
    st.header("🏃 Fitness Plan Generator")
    # (Code for fitness form and API call remains the same for now)
    st.markdown("Provide your fitness details to generate a personalized workout plan.")

    with st.form("fitness_form"):
        st.subheader("Fitness Profile & Goals")
        col1, col2 = st.columns(2)
        with col1:
            fit_level = st.selectbox(
                "Current Fitness Level",
                ['Beginner', 'Intermediate', 'Advanced'],
                key="fit_level"
            )
            fit_activity = st.selectbox(
                "General Activity Level (outside workouts)",
                ['Sedentary', 'Lightly Active', 'Moderately Active', 'Very Active', 'Extra Active'],
                key="fit_activity"
            )
            fit_sessions = st.number_input(
                "Workout Sessions Per Week",
                min_value=1, max_value=14, step=1, value=3, key="fit_sessions"
            )
            fit_time = st.number_input(
                "Time Available Per Session (minutes)",
                min_value=10, max_value=180, step=5, value=45, key="fit_time"
            )

        with col2:
            fit_goals_str = st.text_area(
                "Fitness Goals (comma-separated)",
                placeholder="e.g., Weight Loss, Muscle Gain, Improve Endurance, Flexibility",
                key="fit_goals"
            )
            fit_equip_str = st.text_area(
                "Available Equipment (comma-separated)",
                placeholder="e.g., Dumbbells, Resistance Bands, Treadmill, Bodyweight only",
                key="fit_equip"
            )
            fit_pref_act_str = st.text_area(
                "Preferred Activities (comma-separated)",
                placeholder="e.g., Running, Weightlifting, Yoga, Swimming, Dancing",
                key="fit_pref_act"
            )

        fit_injuries = st.text_area(
            "Any Injuries or Limitations?",
            placeholder="e.g., Knee pain when squatting, Previous shoulder injury",
            key="fit_injuries"
        )

        submit_fitness = st.form_submit_button("Generate Fitness Plan")

    if submit_fitness:
         # --- Validate General Info ---
        if not user_name or user_age <= 0:
             st.error("Please provide your Name and a valid Age in the General Information section.")
        else:
            # --- Prepare Data ---
            general_data = {
                "name": user_name,
                "age": user_age,
                "gender": user_gender,
                "known_conditions": user_known_conditions or None,
                "chronic_conditions": user_chronic_conditions or None
            }
            fitness_data = {
                "activity_level": fit_activity,
                "goals": parse_list_input(fit_goals_str),
                "available_equipment": parse_list_input(fit_equip_str),
                "time_per_session_minutes": fit_time,
                "sessions_per_week": fit_sessions,
                "preferred_activities": parse_list_input(fit_pref_act_str),
                "current_fitness_level": fit_level,
                "injuries_limitations": fit_injuries or "None reported" # Ensure it's a string
            }
            payload = {"general_user": general_data, "fitness_user": fitness_data}


            # --- Call API ---
            endpoint = f"{api_base_url}/fitness-plan/"
            st.info(f"Sending request to: {endpoint}")
            # st.json(payload) # Optional debug

            try:
                with st.spinner("Generating your fitness plan..."):
                    response = requests.post(endpoint, json=payload)
                    response.raise_for_status()

                    st.subheader("Generated Fitness Plan:")
                    result = response.json()
                    #st.json(result) # Displaying raw JSON for now
                    display_fitness_plan(result)

            except requests.exceptions.ConnectionError:
                st.error(f"Connection Error: Could not connect to the API at {api_base_url}. Is the backend running?")
            except requests.exceptions.HTTPError as e:
                st.error(f"HTTP Error: {e.response.status_code} - {e.response.reason}")
                try:
                    st.error(f"API Response: {e.response.json()}")
                except ValueError:
                    st.error(f"API Response: {e.response.text}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")


# --- Mental Wellness Tab (Keep as before) ---
with tab_mental:
    st.header("🧠 Mental Wellness Support")
    # (Code for mental wellness form and API call remains the same)
    st.markdown("Share your concerns and preferences to receive mental wellness guidance.")

    with st.form("mental_form"):
        st.subheader("Wellness & Sleep Details")
        col1, col2 = st.columns(2)
        with col1:
            m_concerns_str = st.text_area(
                "Primary Mental Wellness Concerns (comma-separated)",
                placeholder="e.g., Stress, Anxiety, Low Mood, Focus Issues",
                key="m_concerns"
            )
            m_triggers_str = st.text_area(
                "Known Stress Triggers (comma-separated)",
                placeholder="e.g., Work deadlines, Social situations, Financial worries",
                key="m_triggers"
            )
            m_relax_str = st.text_area(
                "Preferred Relaxation Techniques (comma-separated)",
                placeholder="e.g., Meditation, Deep Breathing, Reading, Walking in Nature",
                key="m_relax"
            )
            m_cbt = st.checkbox("Interested in Cognitive Behavioral Therapy (CBT) techniques?", key="m_cbt")

        with col2:
            st.subheader("Sleep Patterns")
            sleep_avg_hours = st.slider(
                "Average Hours of Sleep per Night",
                min_value=0, max_value=16, step=1, value=7, key="sleep_hours"
            )
            sleep_quality = st.select_slider(
                "Typical Sleep Quality",
                options=['Poor', 'Fair', 'Good', 'Excellent'],
                value='Good', key="sleep_qual"
            )
            sleep_issues_str = st.text_area(
                "Sleep Issues (comma-separated)",
                placeholder="e.g., Difficulty falling asleep, Waking up frequently, Feeling tired upon waking",
                key="sleep_issues"
            )


        submit_mental = st.form_submit_button("Get Mental Wellness Support")

    if submit_mental:
         # --- Validate General Info ---
        if not user_name or user_age <= 0:
             st.error("Please provide your Name and a valid Age in the General Information section.")
        else:
            # --- Prepare Data ---
            general_data = {
                "name": user_name,
                "age": user_age,
                "gender": user_gender,
                "known_conditions": user_known_conditions or None,
                "chronic_conditions": user_chronic_conditions or None
            }
            sleep_data = {
                "avg_hours": sleep_avg_hours,
                "quality": sleep_quality,
                "issues": parse_list_input(sleep_issues_str)
            }
            wellness_data = {
                "primary_concerns": parse_list_input(m_concerns_str),
                "stress_triggers": parse_list_input(m_triggers_str),
                "sleep_patterns": sleep_data, # Nested structure
                "preferred_relaxation": parse_list_input(m_relax_str),
                "cbt_interest": m_cbt
            }
            payload = {"general_user": general_data, "wellness_user": wellness_data}

            # --- Call API ---
            endpoint = f"{api_base_url}/mental-support/"
            st.info(f"Sending request to: {endpoint}")
            # st.json(payload) # Optional debug

            try:
                with st.spinner("Generating mental wellness support..."):
                    response = requests.post(endpoint, json=payload)
                    response.raise_for_status()

                    st.subheader("Mental Wellness Support:")
                    result = response.json()['raw']
                    st.write(result)


            except requests.exceptions.ConnectionError:
                st.error(f"Connection Error: Could not connect to the API at {api_base_url}. Is the backend running?")
            except requests.exceptions.HTTPError as e:
                st.error(f"HTTP Error: {e.response.status_code} - {e.response.reason}")
                try:
                    st.error(f"API Response: {e.response.json()}")
                except ValueError:
                    st.error(f"API Response: {e.response.text}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")


# --- Chronic Condition Support Tab (Keep as before) ---
with tab_chronic:
    st.header("🩺 Chronic Condition Support")
    # (Code for chronic condition form and API call remains the same)
    st.markdown("Receive information and support related to the chronic conditions listed in your General Information.")
    st.info("This feature uses the 'Chronic Conditions' field from the General Information section above.")

    if st.button("Get Chronic Condition Support"):
        # --- Validate General Info ---
        if not user_name or user_age <= 0:
            st.error("Please provide your Name and a valid Age in the General Information section.")
        elif not user_chronic_conditions:
            st.warning("Please enter at least one condition in the 'Chronic Conditions' field under General Information to get support.")
        else:
            # --- Prepare Data ---
            general_data = {
                "name": user_name,
                "age": user_age,
                "gender": user_gender,
                "known_conditions": user_known_conditions or None,
                "chronic_conditions": user_chronic_conditions
            }
            payload = general_data


            # --- Call API ---
            endpoint = f"{api_base_url}/chronic-support/"
            st.info(f"Sending request to: {endpoint}")
            # st.json(payload) # Optional debug

            try:
                with st.spinner("Generating chronic condition support..."):
                    response = requests.post(endpoint, json=payload)
                    response.raise_for_status()
                    result = response.json()['raw']
                    st.subheader("Chronic Condition Support Information:")
                    st.write(result)

            except requests.exceptions.ConnectionError:
                st.error(f"Connection Error: Could not connect to the API at {api_base_url}. Is the backend running?")
            except requests.exceptions.HTTPError as e:
                st.error(f"HTTP Error: {e.response.status_code} - {e.response.reason}")
                try:
                    st.error(f"API Response: {e.response.json()}")
                except ValueError:
                    st.error(f"API Response: {e.response.text}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")


#streamlit run app.py
