import React, { useState, useEffect } from 'react';
import { useApi } from './useApi.jsx';
import DailyMealComponent from './dailyMeal.jsx';
import './style.css';
import ShoppingList from './shoppingList.jsx';

function WeekMealGrid({ days, mealPlan, curWeek, highlightToday = true, disableNutrition = false }) {
  const rows = [
    { label: "Breakfast", type: 1 },
    { label: "Lunch", type: 2 },
    { label: "Dinner", type: 3 },
  ];

  return (
    <div className="week-grid">

      {/* Empty top-left cell */}
      <div className="meal-label-col"></div>
      {days.map(day => (
        <div key={day + "-header"} className="day-header">
          {day}
        </div>
      ))}

      {/* 3 meal rows */}
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
              highlightToday={highlightToday}
            />
          ))}
        </React.Fragment>
      ))}

      <NutritionSummary
        mealPlan={mealPlan}
        curWeek={curWeek}
        disableNutrition={disableNutrition}
      />
    </div>
  );
}

function getWeekRange(offsetWeeks = 0) {
  const today = new Date();
  const day = today.getDay();
  const mondayOffset = day === 0 ? -6 : 1 - day;

  const start = new Date(today);
  start.setDate(today.getDate() + mondayOffset + offsetWeeks * 7);

  const end = new Date(start);
  end.setDate(start.getDate() + 6);

  return {
    startStr: start.toLocaleDateString(),
    endStr: end.toLocaleDateString(),
    startDate: start
  };
}

function NutritionSummary({ mealPlan, curWeek, disableNutrition = false }) {
  const GOALS = { calories: 2747, protein: 123, fat: 80, carbs: 300 };

  if (disableNutrition || !mealPlan || !mealPlan.entries) {
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

  // Nutrition for TODAY only
  const today = new Date();
  const todayKey = today.getDay().toString();

  const todayMeals = mealPlan.entries.filter(e => e.day_of_week == todayKey);

  const totals = todayMeals.reduce(
    (acc, meal) => {
      const r = meal.recipe;
      acc.calories += r.calories_per_serving * meal.servings;
      acc.protein += r.protein_g * meal.servings;
      acc.fat += r.fat_g * meal.servings;
      acc.carbs += r.carbs_g * meal.servings;
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
  const [nextMealPlan, setNextMealPlan] = useState(null);
  const [shoppingList, setShoppingList] = useState(null);
  const [weekStart, setWeekStart] = useState('');
  const [weekEnd, setWeekEnd] = useState('');
  const [nextWeekStart, setNextWeekStart] = useState('');
  const [nextWeekEnd, setNextWeekEnd] = useState('');

  useEffect(() => {
    const thisWeek = getWeekRange(0);
    setWeekStart(thisWeek.startStr);
    setWeekEnd(thisWeek.endStr);
    fetchMealPlanForWeek(thisWeek.startDate, setMealPlan);

    const next = getWeekRange(1);
    setNextWeekStart(next.startStr);
    setNextWeekEnd(next.endStr);
    fetchMealPlanForWeek(next.startDate, setNextMealPlan);
  }, []);

  async function fetchMealPlanForWeek(startDate, setter) {
    const plans = await api.getMealPlans();
    const iso = startDate.toISOString().split('T')[0];
    const found = plans.find(p => p.week_start === iso);

    if (found) setter(found);
    else setter(await api.createMealPlan({ week_start: iso }));
  }

   // new: fetch shopping list for the currently-loaded meal plan
  async function fetchShoppingList(meal_plan) {
    if (!meal_plan || !meal_plan.id) {
      setShoppingList(null);
      return;
    }
    try {
      // adjust api call to match your api client; this uses a generic get
      const res = await api.getShoppingList({ meal_plan_id: meal_plan.id });
      // if your client returns { data } adjust accordingly: res.data
      setShoppingList(res);
    } catch (err) {
      console.error("Failed to fetch shopping list", err);
      setShoppingList(null);
    }
  }

  // call shopping list fetch whenever mealPlan changes
  useEffect(() => {
    fetchShoppingList(mealPlan);
  }, [mealPlan]);

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
        highlightToday={true}
        disableNutrition={false}
      />

      {/* Shopping list for the currently-loaded meal plan */}
      <ShoppingList
        shoppingList={shoppingList}
        onRefresh={() => fetchShoppingList(mealPlan)}
      />

      {/* Next Week */}
      <h1 className="section-title">
        Next Week’s Plan: {nextWeekStart} - {nextWeekEnd}
      </h1>

      <WeekMealGrid
        days={days}
        mealPlan={nextMealPlan}
        curWeek="0"
        highlightToday={false}
        disableNutrition={true}
      />
    </div>
  );
}
