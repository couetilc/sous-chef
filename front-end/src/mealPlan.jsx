import React, { useState, useEffect } from 'react';
import { useApi } from './useApi.jsx';
import DailyMealComponent from './dailyMeal.jsx';
import './style.css';

export default function MealPlanPage() {
  const { api } = useApi();
  const [mealPlan, setMealPlan] = useState(null);
  const [weekStart, setWeekStart] = useState('');
  const [weekEnd, setWeekEnd] = useState('');
  const [loading, setLoading] = useState(true);

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
      setLoading(true);
      const plans = await api.getMealPlans();
      const iso = startDate.toISOString().split('T')[0];
      const found = plans.find(p => p.week_start === iso);

      setMealPlan(found || await api.createMealPlan({ week_start: iso }));
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="loading">Loading meal plan...</div>;

  const days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"];

  return (
    <div className="meal-plan-container">

      <h1 className="section-title">
        Meal Plan: {weekStart} - {weekEnd}
      </h1>

      <div className="week-grid">
        <div className="meal-label-col"></div>
        {days.map(day => (
          <div key={day} className="day-header">{day}</div>
        ))}

        {/* Breakfast row */}
        <div className="meal-label-col">Breakfast</div>
        {days.map((day, i) => (
          <DailyMealComponent
            key={day + "-b"}
            dayOfWeek={i === 6 ? '0' : (i + 1).toString()}
            mealType={1}
            mealPlan={mealPlan}
          />
        ))}

        {/* Lunch row */}
        <div className="meal-label-col">Lunch</div>
        {days.map((day, i) => (
          <DailyMealComponent
            key={day + "-l"}
            dayOfWeek={i === 6 ? '0' : (i + 1).toString()}
            mealType={2}
            mealPlan={mealPlan}
          />
        ))}

        {/* Dinner row */}
        <div className="meal-label-col">Dinner</div>
        {days.map((day, i) => (
          <DailyMealComponent
            key={day + "-d"}
            dayOfWeek={i === 6 ? '0' : (i + 1).toString()}
            mealType={3}
            mealPlan={mealPlan}
          />
        ))}

        <NutritionSummary />
      </div>

      <h1 className="section-title">
        Next Week’s Plan
      </h1>

      <div className="week-grid">
        {days.map((day, i) => (
          <DailyMealComponent
            key={day + "-next"}
            dayOfWeek={i === 6 ? '0' : (i + 1).toString()}
            curWeek="0"
            day={day}
          />
        ))}

        <NutritionSummary />
      </div>

    </div>
  );
}

function NutritionSummary() {
  return (
    <div className="nutrition-card">
      <h2>Nutrition</h2>
      <p>Calories (kCal): 0 / GOAL</p>
      <p>Protein (g): 0 / GOAL</p>
      <p>Fat (g): 0 / GOAL</p>
      <p>Carbs (g): 0 / GOAL</p>
    </div>
  );
}
