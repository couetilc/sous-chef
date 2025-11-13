import React, { useState, useEffect } from 'react';

export default function MealPlanPage() {
  const [weekStart, setWeekStart] = useState(null);
  const [weekEnd, setWeekEnd] = useState(null);

  useEffect(() => {
    const today = new Date();
    const dayOfWeek = today.getDay();
    const start = new Date(today);
    start.setDate(today.getDate() - dayOfWeek);
    const end = new Date(start);
    end.setDate(start.getDate() + 6);

    setWeekStart(start.toLocaleDateString());
    setWeekEnd(end.toLocaleDateString());
  }, []);

  const daysOfWeek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const mealTypes = ['Breakfast', 'Lunch', 'Dinner'];

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
            <tr key={meal}>
              <td style={{ border: '1px solid #ddd', padding: '10px', fontWeight: 'bold' }}>
                {meal}
              </td>
              {daysOfWeek.map(day => (
                <td key={`${meal}-${day}`} style={{ border: '1px solid #ddd', padding: '10px' }}>
                  {/* Meal content goes here */}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
