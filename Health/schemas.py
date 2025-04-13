from typing import List, Optional, Literal
from pydantic import BaseModel

#------------------------
# -- classes to hold the customer input data --
class general(BaseModel):
    name: str
    age: int
    gender: Literal['Female','Male']
    known_conditions: Optional[str]=None
    chronic_conditions: Optional[str]=None

class diet(BaseModel):
    preferences: Literal['Vegan', 'Vegetarian', 'Keto', 'Paleo', 'Gluten-Free', None]
    calories: int
    allergies: List[str]
    intolerances: List[str]
    disliked_foods: List[str]
    cooking_time_preference: Literal['<30 mins', '30-45 mins', '45-60 mins', '>60 mins']
    budget_preference: Literal[ 'Budget-friendly', 'Moderate', 'Flexible']



class fitness(BaseModel):
    activity_level: Literal['Sedentary', 'Lightly Active', 'Moderately Active', 'Very Active', 'Extra Active']
    goals: List[str]
    available_equipment: List[str]
    time_per_session_minutes: int
    sessions_per_week: int
    preferred_activities: List[str]
    current_fitness_level: Literal['Beginner', 'Intermediate', 'Advanced']
    injuries_limitations: Optional[str] = None

 
class sleep_patterns(BaseModel):
    avg_hours: int
    quality: Literal['Poor', 'Fair', 'Good', 'Excellent']
    issues: List[str]
        
class mental_wellness(BaseModel):
    primary_concerns: List[str]
    stress_triggers: List[str]
    sleep_patterns: sleep_patterns
    preferred_relaxation: List[str]
    cbt_interest: bool


#------------------------
# -- Classes to Hold Output Data --
class FoodItem(BaseModel):
    name: str
    quantity: Optional[str]
    notes: Optional[str]


class Meal(BaseModel):
    meal_type: str
    calories: int
    food_items: List[FoodItem]
    notes: Optional[str]


class DayMealPlan(BaseModel):
    day_number: int
    breakfast: Meal
    snack: Meal
    lunch: Meal
    dinner: Meal
    total_calories: int


class MealPlan(BaseModel):
    days: List[DayMealPlan]       


class Exercise(BaseModel):
    name: str
    sets: int
    reps: int
    equipment: str = None
    notes: Optional[str] = None  # e.g., tempo, rest time, variation tip


class WorkoutDay(BaseModel):
    day: int  
    focus: str  # e.g., "Upper Body Strength"
    warmup: List[str]
    exercises: List[Exercise]
    cooldown: List[str]
    notes: str # e.g., "Adjust weights based on your capacity"


class FitnessPlan(BaseModel):
    workout_days: List[WorkoutDay]
