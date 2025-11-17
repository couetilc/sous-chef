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

      <NutritionSummary />
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