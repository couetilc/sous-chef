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
    
    // api call to get the user's meal plan information for that day
  }, []);

  if ( dayOfWeek == props.dayOfWeek && props.curWeek == 1 ) {
    return (
      <div className="today-plan-div">
        <p style={{textDecoration: 'underline' }}> {dayText} </p>
        <div className="meal-plan-meal">
          <p> Breakfast </p>
          <p> Meal Name 1 </p>
        </div>
        <div className="meal-plan-meal">
          <p> Lunch </p>
          <p> Meal Name 2 </p>
        </div>
        <div className="meal-plan-meal">
          <p> Dinner</p>
          <p> Meal Name 3 </p>
        </div>
      </div>
    )
  }
  return (
    <div className="daily-plan-div">
        <p style={{textDecoration: 'underline' }}> {dayText} </p>
      <div className="meal-plan-meal">
        <p> Breakfast </p>
        <p> Meal Name 1 </p>
      </div>
      <div className="meal-plan-meal">
        <p> Lunch </p>
        <p> Meal Name 2 </p>
      </div>
      <div className="meal-plan-meal">
      <p> Dinner</p>
        <p> Meal Name 3 </p>
      </div>
    </div>
  )
}

