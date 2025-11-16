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
    if ( dayOfWeek == 0 ) {
      setDayText('Sunday');
    }
    else if ( dayOfWeek == 1 ) {
      setDayText('Monday');
    }
    else if ( dayOfWeek == 2 ) {
      setDayText('Tuesday');
    }
    else if ( dayOfWeek == 3 ) {
      setDayText('Wednesday');
    }
    else if ( dayOfWeek == 4 ) {
      setDayText('Thursday');
    }
    else if ( dayOfWeek == 5 ) {
      setDayText('Friday');
    }
    else if ( dayOfWeek == 6 ) {
      setDayText('Saturday');
    }
    
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

