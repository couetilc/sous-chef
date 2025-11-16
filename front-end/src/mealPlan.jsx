import React, {useState, useEffect } from 'react';
import { useNavigate, Navigate } from 'react-router';
import './style.css';
import { useApi } from './useApi.jsx'; 
import DailyMealComponent from './dailyMeal.jsx';

export default function MealPlanPage(props) {
  const { api } = useApi();
  const [mealPlan, setMealPlan] = useState(null);
  const [weekStart, setWeekStart] = useState(null);
  const [weekEnd, setWeekEnd] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const today = new Date();
    const dayOfWeek = today.getDay();
    const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
    const start = new Date(today);
    start.setDate(today.getDate() - daysToMonday);
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
      const existingPlan = plans.find(p => p.week_start === startDate.toISOString().split('T')[0]);
      
      if (existingPlan) {
        setMealPlan(existingPlan);
      } else {
        const newPlan = await api.createMealPlan({ 
          week_start: startDate.toISOString().split('T')[0] 
        });
        setMealPlan(newPlan);
      }
    } catch (error) {
      console.error('Error fetching meal plan:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div>Loading meal plan...</div>;

  return ( 
    <div className="meal-plan-div">
      <div className="meal-plan-text">
        <h1 style={{ marginTop: '10px'}}> Your Meal Plan for {weekStart} to {weekEnd} </h1>
      </div>
      <div className="weekly-plan-div">
        <div> <p> </p></div>
        <DailyMealComponent dayOfWeek='1' curWeek='1' day='Monday' mealPlan={mealPlan}> </DailyMealComponent>
        <DailyMealComponent dayOfWeek='2' curWeek='1' day='Tuesday' mealPlan={mealPlan}> </DailyMealComponent>
        <DailyMealComponent dayOfWeek='3' curWeek='1' day='Wednesday' mealPlan={mealPlan}> </DailyMealComponent>
        <DailyMealComponent dayOfWeek='4' curWeek='1' day='Thursday' mealPlan={mealPlan}> </DailyMealComponent>
        <DailyMealComponent dayOfWeek='5' curWeek='1' day='Friday' mealPlan={mealPlan}> </DailyMealComponent>
        <DailyMealComponent dayOfWeek='6' curWeek='1' day='Saturday' mealPlan={mealPlan}> </DailyMealComponent>
        <DailyMealComponent dayOfWeek='0' curWeek='1' day='Sunday' mealPlan={mealPlan}> </DailyMealComponent>
        <div className="meal-plan-nutr">
          <h1> Nutrition </h1>
          <p> Calories(kCal): 0/GOAL </p>
          <p> Protein(g): 0/GOAL </p>
          <p> Fat(g): 0/GOAL </p>
          <p> Carbohydrates(g): 0/GOAL </p>
        </div>

      </div>
      <div className="meal-plan-text">
        <h1> Next Week's Plan: start_date-end_date </h1>
      </div>
      <div className="weekly-plan-div">
        <div> <p> </p></div>
        <DailyMealComponent dayOfWeek='1' curWeek='0' day='Monday'> </DailyMealComponent>
        <DailyMealComponent dayOfWeek='2' curWeek='0' day='Tuesday'> </DailyMealComponent>
        <DailyMealComponent dayOfWeek='3' curWeek='0' day='Wednesday'> </DailyMealComponent>
        <DailyMealComponent dayOfWeek='4' curWeek='0' day='Thursday'> </DailyMealComponent>
        <DailyMealComponent dayOfWeek='5' curWeek='0' day='Friday'> </DailyMealComponent>
        <DailyMealComponent dayOfWeek='6' curWeek='0' day='Saturday'> </DailyMealComponent>
        <DailyMealComponent dayOfWeek='0' curWeek='0' day='Sunday'> </DailyMealComponent>
        <div className="meal-plan-nutr">
          <h1> Nutrition </h1>
          <p> Calories(kCal): 0/GOAL </p>
          <p> Protein(g): 0/GOAL </p>
          <p> Fat(g): 0/GOAL </p>
          <p> Carbohydrates(g): 0/GOAL </p>
        </div>
      </div>
    </div>
  )
}



