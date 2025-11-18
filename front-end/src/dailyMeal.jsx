import React, {useState, useEffect } from 'react';
import { useNavigate, Navigate } from 'react-router';
import './style.css';
import {useApi } from './useApi.jsx';

export default function DailyMealComponent({ dayOfWeek, mealType, mealPlan }) {
  const meals = mealPlan?.entries?.filter(
    e => e.day_of_week === Number(dayOfWeek)
  ) || [];

  const meal = meals.find(m => m.meal_index === mealType);
  const name = meal?.recipe?.title || "No meal added";

  const isToday = new Date().getDay().toString() === dayOfWeek;

  return (
    <div className={`meal-cell ${isToday ? "today-cell" : ""}`}>
      {name}
    </div>
  );
}