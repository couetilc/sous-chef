import React, {useState, useEffect } from 'react';
import { useNavigate, Navigate } from 'react-router';
import './style.css';
import { useApi } from './useApi.jsx'; 

export default function MealPlanPage(props) {
  //use useEffect to read the user's meal plan on page load
  //useEffect()
  return ( 
    <div className="meal-plan-div">
      <div className="meal-plan-text">
        <h1> Your Meal Plan for week_start to week_end </h1>
      </div>
      <div className="weekly-plan-div">
        <div> <p> </p></div>
        <div className="daily-plan-div">
          <p> Monday </p>
          <div className="meal-plan-meal">
            <p> Breakfast </p>
            <p> Meal Name 1</p>
          </div>
          <div className="meal-plan-meal">
            <p> Lunch </p>
            <p> Meal Name 2</p>
          </div>
          <div className="meal-plan-meal">
            <p> Dinner  </p>
            <p> Meal Name 3</p>
          </div>
        </div>
        <div className="daily-plan-div">
          <p> Tuesday </p>
          <div className="meal-plan-meal">
            <p> Breakfast </p>
            <p> Meal Name 1</p>
          </div>
          <div className="meal-plan-meal">
            <p> Lunch </p>
            <p> Meal Name 2</p>
          </div>
          <div className="meal-plan-meal">
            <p> Dinner  </p>
            <p> Meal Name 3</p>
          </div>
        </div>
        <div className="daily-plan-div">
          <p> Wednesday </p>
          <div className="meal-plan-meal">
            <p> Breakfast </p>
            <p> Meal Name 1</p>
          </div>
          <div className="meal-plan-meal">
            <p> Lunch </p>
            <p> Meal Name 2</p>
          </div>
          <div className="meal-plan-meal">
            <p> Dinner  </p>
            <p> Meal Name 3</p>
          </div>
        </div>
        <div className="daily-plan-div">
          <p> Thursday </p>
          <div className="meal-plan-meal">
            <p> Breakfast </p>
            <p> Meal Name 1</p>
          </div>
          <div className="meal-plan-meal">
            <p> Lunch </p>
            <p> Meal Name 2</p>
          </div>
          <div className="meal-plan-meal">
            <p> Dinner  </p>
            <p> Meal Name 3</p>
          </div>
        </div>
        <div className="daily-plan-div">
          <p> Friday </p>
          <div className="meal-plan-meal">
            <p> Breakfast </p>
            <p> Meal Name 1</p>
          </div>
          <div className="meal-plan-meal">
            <p> Lunch </p>
            <p> Meal Name 2</p>
          </div>
          <div className="meal-plan-meal">
            <p> Dinner  </p>
            <p> Meal Name 3</p>
          </div>
        </div>
        <div className="daily-plan-div">
          <p> Saturday </p>
          <div className="meal-plan-meal">
            <p> Breakfast </p>
            <p> Meal Name 1</p>
          </div>
          <div className="meal-plan-meal">
            <p> Lunch </p>
            <p> Meal Name 2</p>
          </div>
          <div className="meal-plan-meal">
            <p> Dinner  </p>
            <p> Meal Name 3</p>
          </div>
        </div>
        <div className="daily-plan-div">
          <p> Sunday </p>
          <div className="meal-plan-meal">
            <p> Breakfast </p>
            <p> Meal Name 1</p>
          </div>
          <div className="meal-plan-meal">
            <p> Lunch </p>
            <p> Meal Name 2</p>
          </div>
          <div className="meal-plan-meal">
            <p> Dinner  </p>
            <p> Meal Name 3</p>
          </div>
        </div>
        <div className="meal-plan-nutr">
          <h1> Nutrition </h1>
          <p> Calories(kCal): 0/GOAL </p>
          <p> Protein(g): 0/GOAL </p>
          <p> Fat(g): 0/GOAL </p>
        </div>
      </div>
      <div className="meal-plan-text">
        <h1> Next Week's Plan: start_date-end_date </h1>
      </div>
      <div className="weekly-plan-div">
        <div> <p> </p></div>
        <div className="daily-plan-div">
          <p> Monday </p>
          <div className="meal-plan-meal">
            <p> Breakfast </p>
            <p> Meal Name 1</p>
          </div>
          <div className="meal-plan-meal">
            <p> Lunch </p>
            <p> Meal Name 2</p>
          </div>
          <div className="meal-plan-meal">
            <p> Dinner  </p>
            <p> Meal Name 3</p>
          </div>
        </div>
        <div className="daily-plan-div">
          <p> Tuesday </p>
          <div className="meal-plan-meal">
            <p> Breakfast </p>
            <p> Meal Name 1</p>
          </div>
          <div className="meal-plan-meal">
            <p> Lunch </p>
            <p> Meal Name 2</p>
          </div>
          <div className="meal-plan-meal">
            <p> Dinner  </p>
            <p> Meal Name 3</p>
          </div>
        </div>
        <div className="daily-plan-div">
          <p> Wednesday </p>
          <div className="meal-plan-meal">
            <p> Breakfast </p>
            <p> Meal Name 1</p>
          </div>
          <div className="meal-plan-meal">
            <p> Lunch </p>
            <p> Meal Name 2</p>
          </div>
          <div className="meal-plan-meal">
            <p> Dinner  </p>
            <p> Meal Name 3</p>
          </div>
        </div>
        <div className="daily-plan-div">
          <p> Thursday </p>
          <div className="meal-plan-meal">
            <p> Breakfast </p>
            <p> Meal Name 1</p>
          </div>
          <div className="meal-plan-meal">
            <p> Lunch </p>
            <p> Meal Name 2</p>
          </div>
          <div className="meal-plan-meal">
            <p> Dinner  </p>
            <p> Meal Name 3</p>
          </div>
        </div>
        <div className="daily-plan-div">
          <p> Friday </p>
          <div className="meal-plan-meal">
            <p> Breakfast </p>
            <p> Meal Name 1</p>
          </div>
          <div className="meal-plan-meal">
            <p> Lunch </p>
            <p> Meal Name 2</p>
          </div>
          <div className="meal-plan-meal">
            <p> Dinner  </p>
            <p> Meal Name 3</p>
          </div>
        </div>
        <div className="daily-plan-div">
          <p> Saturday </p>
          <div className="meal-plan-meal">
            <p> Breakfast </p>
            <p> Meal Name 1</p>
          </div>
          <div className="meal-plan-meal">
            <p> Lunch </p>
            <p> Meal Name 2</p>
          </div>
          <div className="meal-plan-meal">
            <p> Dinner  </p>
            <p> Meal Name 3</p>
          </div>
        </div>
        <div className="daily-plan-div">
          <p> Sunday </p>
          <div className="meal-plan-meal">
            <p> Breakfast </p>
            <p> Meal Name 1</p>
          </div>
          <div className="meal-plan-meal">
            <p> Lunch </p>
            <p> Meal Name 2</p>
          </div>
          <div className="meal-plan-meal">
            <p> Dinner  </p>
            <p> Meal Name 3</p>
          </div>
        </div>
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



