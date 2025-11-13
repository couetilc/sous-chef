import React, { useState, useEffect } from 'react';
import { useApi } from './useApi';
import { useGET } from './useGET';

export default function MealPlanPage() {
  const { api } = useApi();
  const [mealPlan, setMealPlan] = useState(null);
  const [weekStart, setWeekStart] = useState(null);
  const [weekEnd, setWeekEnd] = useState(null);
  const [loading, setLoading] = useState(true);

  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const mealTypes = [
    { index: 1, name: 'Breakfast' },
    { index: 2, name: 'Lunch' },
    { index: 3, name: 'Dinner' }
  ];

  useEffect(() => {
    const today = new Date();
    const dayOfWeek = today.getDay();
    const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1; // 0 = Sunday, so -1 day to get to Monday
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

  async function handleRemoveRecipe(entryId) {
    try {
      await api.deleteMealPlanEntry({ 
        meal_plan_id: mealPlan.id, 
        entry_id: entryId 
      });
      // Refresh meal plan
      const updated = await api.getMealPlan({ id: mealPlan.id });
      setMealPlan(updated);
    } catch (error) {
      console.error('Error removing recipe:', error);
    }
  }

  if (loading) return <div>Loading meal plan...</div>;

  return (
    <div style={{ padding: '20px' }}>
      <h1>Weekly Meal Plan</h1>
      <p>Week of {weekStart} to {weekEnd}</p>
      
      <table style={{ borderCollapse: 'collapse', width: '100%', marginTop: '20px' }}>
        <thead>
          <tr>
            <th style={{ border: '1px solid #ddd', padding: '10px' }}>Meal</th>
            {daysOfWeek.map(day => (
              <th key={day} style={{ border: '1px solid #ddd', padding: '10px' }}>
                {day}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {mealTypes.map(meal => (
            <tr key={meal.index}>
              <td style={{ border: '1px solid #ddd', padding: '10px', fontWeight: 'bold' }}>
                {meal.name}
              </td>
              {daysOfWeek.map((_, dayIndex) => {
                const entry = mealPlan?.entries?.find(
                  e => e.day_of_week === dayIndex && e.meal_index === meal.index
                );
                return (
                  <td 
                    key={`${meal.index}-${dayIndex}`} 
                    style={{ border: '1px solid #ddd', padding: '10px', minHeight: '100px' }}
                  >
                    {entry?.recipe && (
                      <div>
                        <strong>{entry.recipe.title}</strong>
                        <div style={{ fontSize: '12px', marginTop: '4px' }}>
                          {entry.recipe.servings} servings | {entry.recipe.calories_per_serving} cal
                        </div>
                        <button 
                          onClick={() => handleRemoveRecipe(entry.id)}
                          style={{ marginTop: '8px', fontSize: '12px' }}
                        >
                          Remove
                        </button>
                      </div>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}