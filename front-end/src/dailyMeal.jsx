import React, {useState, useEffect } from 'react';
import { useNavigate, Navigate } from 'react-router';
import './style.css';
import {useApi } from './useApi.jsx';

export default function DailyMealComponent(props) {
  const [dayOfWeek, setDayOfWeek] = useState(0);
  const [dayText, setDayText] = useState('');

  useEffect(() => {
    //get current day of the week
    const d = new Date();
    setDayOfWeek(d.getDay());
    setDayText(props.day);
  }, []);

  // Get meals for this day from the API response
  const mealsForDay = props.mealPlan?.entries?.filter(
    (e) => e.day_of_week === Number(props.dayOfWeek)
  ) || [];

  // Assign meals based on meal_index
  const breakfast = mealsForDay.find(m => m.meal_index === 1);
  const lunch = mealsForDay.find(m => m.meal_index === 2);
  const dinner = mealsForDay.find(m => m.meal_index === 3);

  // If name does not exist, add placeholder
  const breakfastName = breakfast?.recipe?.title || "No meal added";
  const lunchName = lunch?.recipe?.title || "No meal added";
  const dinnerName = dinner?.recipe?.title || "No meal added";

  if ( dayOfWeek == props.dayOfWeek && props.curWeek == 1 ) {
    return (
      <div className="today-plan-div">
        <p style={{textDecoration: 'underline' }}> {dayText} </p>
        <div className="meal-plan-meal">
          <p> Breakfast </p>
          <p> {breakfastName} </p>
        </div>
        <div className="meal-plan-meal">
          <p> Lunch </p>
          <p> {lunchName} </p>
        </div>
        <div className="meal-plan-meal">
          <p> Dinner</p>
          <p> {dinnerName} </p>
        </div>
      </div>
    )
  }
  return (
    <div className="daily-plan-div">
        <p style={{textDecoration: 'underline' }}> {dayText} </p>
      <div className="meal-plan-meal">
        <p> Breakfast </p>
        <p> {breakfastName} </p>
      </div>
      <div className="meal-plan-meal">
        <p> Lunch </p>
        <p> {lunchName} </p>
      </div>
      <div className="meal-plan-meal">
      <p> Dinner</p>
        <p> {dinnerName} </p>
      </div>
    </div>
  )
}

