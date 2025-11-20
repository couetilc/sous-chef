import React, { useState } from 'react';
import MealPlanModal from './mealPlanModal.jsx';
import './style.css';

export default function DailyMealComponent({ dayOfWeek, mealType, mealPlan }) {
  const [openMeal, setOpenMeal] = useState(null);

  const meals = mealPlan?.entries?.filter(
    e => e.day_of_week === Number(dayOfWeek)
  ) || [];

  const meal = meals.find(m => m.meal_index === mealType);

  const name = meal?.recipe?.title || "No meal added";
  const isToday = new Date().getDay().toString() === dayOfWeek;

  return (
    <>
      <div
        className={`meal-cell ${isToday ? "today-cell" : ""}`}
        onClick={() => meal && setOpenMeal(meal)}
        style={{ cursor: meal ? "pointer" : "default" }}
      >
        {name}
      </div>

      {openMeal && (
        <MealPlanModal
          meal={openMeal}
          onClose={() => setOpenMeal(null)}
        />
      )}
    </>
  );
}
