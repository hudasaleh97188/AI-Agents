from crewai_tools import ScrapeWebsiteTool, SerperDevTool
import os
from crewai import LLM
from crewai import Agent, Task, Crew, Process
from typing import List, Optional, Literal
from crewai.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchRun
from fastapi import  FastAPI
from schemas import diet, fitness, mental_wellness, general, FitnessPlan, MealPlan
import uvicorn


# --------------------------------------
# LLM
llm = LLM(model="gemini/gemini-2.0-flash",provider="google",api_key="GEMINI_API_KEY")


# --------------------------------------
# Tool
class MyCustomDuckDuckGoTool(BaseTool):
    name: str = "DuckDuckGo Search Tool"
    description: str = "Search the web for a given query."

    def _run(self, query: str) -> str:
        if not query.strip():
            return "Please provide a valid search query."
        duckduckgo_tool = DuckDuckGoSearchRun(backend="auto")
        response = duckduckgo_tool.invoke(query)
        return response

    def _get_tool(self):
        # Create an instance of the tool when needed
        return MyCustomDuckDuckGoTool()
    
Duck_search = MyCustomDuckDuckGoTool()


# --------------------------------------
# Agents
# Dietitian Agent
dietitian_agent = Agent(
    role='Dietitian & Nutritionist',
    goal='Create personalized meal plans, recipes, and nutritional insights based on user details (preferences, allergies, goals etc) and evidence-based nutritional science.',
    backstory='A knowledgeable and empathetic AI dietitian focused on creating healthy, delicious, and achievable eating plans tailored to individual needs.',
    llm=llm,
    tools=[Duck_search], # Can search for recipe ideas or nutritional info
    verbose=True,
    allow_delegation=False # Might delegate complex recipe searches or saving tasks
)


# Fitness Coach Agent
fitness_coach_agent = Agent(
    role='Fitness Coach',
    goal='Design customized workout plans and provide exercise guidance based on user fitness level, goals, available equipment, and preferences.',
    backstory='An encouraging and expert AI fitness coach that crafts effective and safe workout routines, adapting them to the user\'s progress and feedback.',
    llm=llm,
    tools=[Duck_search], # Can search for exercise variations/videos
    verbose=True,
    allow_delegation=False
)


# Mental Wellness Agent
mental_wellness_agent = Agent(
    role='Mental Wellness Assistant',
    goal='Generate guided meditations scripts, stress management techniques (like CBT-based exercises), sleep improvement insights, and relaxation exercises based on user needs.',
    backstory='A calm, compassionate, and insightful AI assistant dedicated to supporting users\' mental and emotional well-being through evidence-based practices.',
    llm=llm,
    tools=[Duck_search],
    verbose=True,
    allow_delegation=False # Generally focuses on generation based on profile
)
# Example (use cautiously and refine heavily):
chronic_support_agent = Agent(
    role='Chronic Condition Informational Support',
    goal='Provide GENERAL LIFESTYLE and INFORMATIONAL support related to managing chronic conditions (like diabetes, hypertension) based on user profile. CRITICALLY, DO NOT PROVIDE MEDICAL ADVICE. Always recommend consulting a healthcare professional.',
    backstory='An AI assistant designed to offer educational content and general lifestyle tips (diet, exercise reminders based on common knowledge) for users managing chronic conditions. It acts as an informational resource ONLY and cannot replace professional medical consultation.',
    llm=llm,
    tools=[Duck_search],
    verbose=True,
    allow_delegation=False # Strict control, no delegation for safety
)


# --------------------------------------
# --- Define Tasks ---
# Generate a Meal Plan
meal_plan_task = Task(
    description=(
        "1. Understand the user's dietary preferences, allergies, and goals from {general_user} and {diet_user} "
        "2. Based *only* on the retrieved profile information, create a personalized 3-day meal plan f. "
        "3. Ensure the plan avoids any allergies mentioned in the profile. "
        "4. Include breakfast, lunch, dinner, and one snack per day. "
        "5. Provide estimated calorie counts for each meal. "
        "6. Format the output clearly (e.g., Day 1 Breakfast: ..., Day 1 Lunch: ...). "
    ),
    expected_output=(
        "A detailed 3-day meal plan formatted clearly, respecting user preferences "
        "including estimated calories per meal. Follow a JSON object matching the MealPlan class"
    ),  
    output_pydantic=MealPlan,
    agent=dietitian_agent, 
)

# Generate a Workout Plan
workout_plan_task = Task(
    description=(
        "1. Understand the user's fitness goals, level, available equipment, and time constraints  "
        "2. Create a 3-day-per-week workout plan focused on the user profile. "
        "3. Structure the plan clearly in FitnessPlan pydantic class  "
        "4. Include specific exercises, sets, and reps for each day. "
        "5. Suggest brief warm-up and cool-down routines. "
    ),
    expected_output=(
        "A structured 3-day workout plan tailored to the user's profile , "
        "including exercises, sets/reps, warm-up/cool-down in FitnessPlan pydantic class ."
    ),
    agent=fitness_coach_agent,
    output_pydantic=FitnessPlan,
)

# Generate Meditation Script
meditation_task = Task(
    description=(
        "1. Understand the user's current challenges (e.g., stress, sleep issues). "
        "2. Search for techiques to resolve the user's problem such as Generate guided meditations scripts, stress management techniques (like CBT-based exercises), sleep improvement insights, and relaxation exercises based on user needs "
        "3. provide the details to the user "
    ),
    expected_output=(
        "A list of techniques for stress relief and pre-sleep relaxation"
    ),
    agent=mental_wellness_agent
)

# Chronic Support Task
chronic_support_task = Task(
    description=(
        "1. Understand the user's chronic condition(s), lifestyle habits, and goals. "
        "2. Provide general tips on managing such conditions through diet, physical activity, sleep hygiene, and stress management. "
        "3. Include clear disclaimers: this is not medical advice. "
        "4. Ensure content is informative, positive, and based on common knowledge or public health guidelines. "
        "5. Optionally include links to reputable resources (CDC, WHO, etc.)."
    ),
    expected_output=(
        "A general lifestyle support guide for managing the user's chronic condition(s), "
        "including tips for diet, exercise, sleep, and mental well-being. "
        "All advice must be general and contain disclaimers encouraging users to consult healthcare professionals."
    ),
    agent=chronic_support_agent,
    
)


# --------------------------------------
# --- Define Crews ---
dietitian_crew = Crew(agents=[dietitian_agent],tasks=[meal_plan_task], process=Process.sequential, verbose=True)
fitness_crew = Crew(agents=[fitness_coach_agent],tasks=[workout_plan_task],process=Process.sequential,  verbose=True)
wellness_crew = Crew(agents=[mental_wellness_agent],tasks=[meditation_task], process=Process.sequential, verbose=True)
chronic_support_crew = Crew(agents=[chronic_support_agent],tasks=[chronic_support_task], process=Process.sequential, verbose=True)

# --------------------------------------
# --- Test ---
# user_general_data = {'name': 'Huua', 'age': 40, 'gender': 'Male','known_conditions':None,'chronic_conditions':None}
# user_general = general(**user_general_data) 
# user_diet_data = {'preferences': 'Keto', 'calories': 1800, 'allergies': ['Peanuts'],
#                   'intolerances':['Lactose'],'disliked_foods':["Mushrooms", "Olives"],'cooking_time_preference': '30-45 mins','budget_preference':'Budget-friendly'}
# user_diet = diet(**user_diet_data) 
# result = dietitian.kickoff(inputs={'general':user_general,'diet':user_diet})
            # --- Prepare Data ---
# user_general_data = {
#     "name": 'HH',
#     "age": 40,
#     "gender": 'Male',
#     "known_conditions":  None,
#     "chronic_conditions": None
# }
# user_general = general(**user_general_data) 
# user_fitness_data = { # Renamed for clarity
#     'activity_level': 'Sedentary',
#     'goals': ['improve health'],
#     'available_equipment': ['None'],
#     'time_per_session_minutes': 90,
#     'sessions_per_week': 2,
#     'preferred_activities': ['yoga'],
#     'current_fitness_level': 'Beginner',
#     # CHANGE HERE: Use an empty string or descriptive text
#     'injuries_limitations': ""
#     # OR
#     # 'injuries_limitations': "None reported"
# }
# user_fitness = fitness(**user_fitness_data) 

# result = fitness_crew.kickoff(inputs={'general_user':user_general,'fitness_user':user_fitness})
# print(result.pydantic)


# --------------------------------------
# --- Create APIs ---
app = FastAPI(title="Eunoia AI Health API")

@app.post("/diet-plan/")
async def get_diet_plan(general_user:general, diet_user:diet):
    result = dietitian_crew.kickoff(inputs={'general_user':general_user,'diet_user':diet_user})
    return result.pydantic

@app.post("/fitness-plan/")
async def get_fitness_plan(general_user:general,fitness_user:fitness):
    result = fitness_crew.kickoff(inputs={'general_user':general_user,'fitness_user':fitness_user})
    return result

@app.post("/mental-support/")
async def get_mental_support(general_user:general, wellness_user:mental_wellness):
    result = wellness_crew.kickoff(inputs={'general_user':general_user,'wellness_user':wellness_user})
    return result

@app.post("/chronic-support/")
async def get_chronic_support(general_user: general):
    result = chronic_support_crew.kickoff(inputs={'general_user':general_user})
    return result

if __name__ == "__main__":
    uvicorn.run("crew:app", host="0.0.0.0", port=8000, reload=True)



