import React, { useState } from 'react';
import MealPlanModal from './mealPlanModal.jsx';

export default function DailyMealComponent({
  dayOfWeek,
  mealType,
  mealPlan,
  curWeek,
  highlightToday = true
}) {
  const [modalMeal, setModalMeal] = useState(null);

  if (!mealPlan || !mealPlan.entries) return <div className="meal-cell empty"></div>;

  const entry = mealPlan.entries.find(
    e => e.day_of_week == dayOfWeek && e.meal_index === mealType
  );

  const today = new Date();
  const todayKey = today.getDay().toString();

  const isToday =
    highlightToday &&
    curWeek === "1" &&
    dayOfWeek === todayKey;

  return (
    <>
      <div
        className={`meal-cell ${isToday ? "today-cell" : ""}`}
        onClick={() => entry && setModalMeal(entry)}
      >
        {entry ? entry.recipe.title : ""}
      </div>

      {modalMeal && (
        <MealPlanModal
          meal={modalMeal}
          onClose={() => setModalMeal(null)}
        />
      )}
    </>
  );
}
