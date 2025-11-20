import React, { useState, useEffect } from 'react';
import { useApi } from './useApi.jsx';
import DailyMealComponent from './dailyMeal.jsx';
import './style.css';

function WeekMealGrid({ days, mealPlan, curWeek }) {
  const rows = [
    { label: "Breakfast", type: 1 },
    { label: "Lunch", type: 2 },
    { label: "Dinner", type: 3 },
  ];

  return (
    <div className="week-grid">

      {/* Empty top left cell */}
      <div className="meal-label-col"></div>
      {days.map(day => (
        <div key={day + "-header"} className="day-header">
          {day}
        </div>
      ))}

      {/* Breakfast, Lunch, Dinner rows */}
      {rows.map(row => (
        <React.Fragment key={row.label}>
          <div className="meal-label-col">{row.label}</div>

          {days.map((day, i) => (
            <DailyMealComponent
              key={day + "-" + row.label}
              dayOfWeek={i === 6 ? "0" : (i + 1).toString()}
              mealType={row.type}
              mealPlan={mealPlan}
              curWeek={curWeek}
            />
          ))}
        </React.Fragment>
      ))}

      <NutritionSummary mealPlan={mealPlan} curWeek={curWeek} />
    </div>
  );
}

function NutritionSummary({ mealPlan, curWeek }) {
  // Nutrition goals
  const GOALS = {
    calories: 2747,
    protein: 123,
    fat: 80,
    carbs: 300,
  };

  if (!mealPlan || !mealPlan.entries) {
    return (
      <div className="nutrition-card">
        <h2>Nutrition</h2>
        <p>Calories (kCal): 0 / {GOALS.calories}</p>
        <p>Protein (g): 0 / {GOALS.protein}</p>
        <p>Fat (g): 0 / {GOALS.fat}</p>
        <p>Carbs (g): 0 / {GOALS.carbs}</p>
      </div>
    );
  }

  // Get today's day index
  const today = new Date();
  let dow = today.getDay();
  const todayKey = dow.toString();

  const todayMeals = mealPlan.entries.filter(e => e.day_of_week == todayKey);

  console.log("Today's meals:", todayMeals);

  // Add today's meals to calc nutrition
  const totals = todayMeals.reduce(
    (acc, meal) => {
      const recipe = meal.recipe;
      acc.calories += recipe.calories_per_serving * meal.servings;
      acc.protein += recipe.protein_g * meal.servings;
      acc.fat += recipe.fat_g * meal.servings;
      acc.carbs += recipe.carbs_g * meal.servings;

      return acc;
    },
    { calories: 0, protein: 0, fat: 0, carbs: 0 }
  );

  return (
    <div className="nutrition-card">
      <h2>Nutrition</h2>
      <p>Calories (kCal): {totals.calories} / {GOALS.calories}</p>
      <p>Protein (g): {totals.protein} / {GOALS.protein}</p>
      <p>Fat (g): {totals.fat} / {GOALS.fat}</p>
      <p>Carbs (g): {totals.carbs} / {GOALS.carbs}</p>
    </div>
  );
}

export default function MealPlanPage() {
  const { api } = useApi();
  const [mealPlan, setMealPlan] = useState(null);
  const [weekStart, setWeekStart] = useState('');
  const [weekEnd, setWeekEnd] = useState('');

  useEffect(() => {
    const today = new Date();
    const day = today.getDay();
    const mondayOffset = day === 0 ? -6 : 1 - day;

    const start = new Date(today);
    start.setDate(today.getDate() + mondayOffset);

    const end = new Date(start);
    end.setDate(start.getDate() + 6);

    setWeekStart(start.toLocaleDateString());
    setWeekEnd(end.toLocaleDateString());
    fetchOrCreateMealPlan(start);
  }, []);

  async function fetchOrCreateMealPlan(startDate) {
    try {
      const plans = await api.getMealPlans();
      const iso = startDate.toISOString().split('T')[0];
      const found = plans.find(p => p.week_start === iso);

      setMealPlan(found || await api.createMealPlan({ week_start: iso }));
    } catch (err) {
      console.error('Error:', err);
    }
  }

  const days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"];

  return (
    <div className="meal-plan-container">

      {/* Current Week */}
      <h1 className="section-title">
        Meal Plan: {weekStart} - {weekEnd}
      </h1>

      <WeekMealGrid
        days={days}
        mealPlan={mealPlan}
        curWeek="1"
      />

      {/* Next Week */}
      <h1 className="section-title">Next Week’s Plan</h1>

      <WeekMealGrid
        days={days}
        mealPlan={null}
        curWeek="0"
      />
    </div>
  );
}
