import React, {useState, useEffect } from 'react';
import { useNavigate, Navigate } from 'react-router';
import './style.css';
import { useApi } from './useApi.jsx'; 
import DailyMealComponent from './dailyMeal.jsx';

export default function MealPlanPage(props) {
  //use useEffect to read the user's meal plan on page load
  //useEffect()

  return ( 
    <div className="meal-plan-div">
      <div className="meal-plan-text">
        <h1 style={{ marginTop: '5px'}}> Your Meal Plan for week_start to week_end </h1>
      </div>
      <div className="weekly-plan-div">
        <div> <p> </p></div>
        <DailyMealComponent dayOfWeek='1' curWeek='1' day='Monday'> </DailyMealComponent>
        <DailyMealComponent dayOfWeek='2' curWeek='1' day='Tuesday'> </DailyMealComponent>
        <DailyMealComponent dayOfWeek='3' curWeek='1' day='Wednesday'> </DailyMealComponent>
        <DailyMealComponent dayOfWeek='4' curWeek='1' day='Thursday'> </DailyMealComponent>
        <DailyMealComponent dayOfWeek='5' curWeek='1' day='Friday'> </DailyMealComponent>
        <DailyMealComponent dayOfWeek='6' curWeek='1' day='Saturday'> </DailyMealComponent>
        <DailyMealComponent dayOfWeek='0' curWeek='1' day='Sunday'> </DailyMealComponent>
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



