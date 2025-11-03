import React from 'react';
import {useNavigate, Navigate} from 'react-router';
import Home from './home.jsx';
import { useUser } from './useUser.jsx';
import { useState } from 'react';
import { useApi } from './useApi.jsx';

const HealthComponent = () => {
  const { api } = useApi();

  const [age, setAge] = useState([]);
  const [height, setHeight] = useState([]);
  const [weight, setWeight] = useState([]);
  const [activityLevel, setActivityLevel] = useState([]);
  const [goal, setGoal] = useState([]);

}

export default function HealthOnboarding(props) {
  const navigate = useNavigate();
  const { user } = useUser();
  const { api } = useApi();
  const boolTrue = true;
  const boolFalse = false;

  function navToHome() {
    return navigate("/home");
  }

  function submit() {
    /*
    submit button onclick
    api call setHealthInfo({age, height_ft, height_in, weight, activity_level, goal})
    */
    alert("1");
    //update user onboarded status
    api.setOnboardingStatus({new_onboarded: true, new_skipped: false});
    navToHome();
  }

  return (
    <div className="health">
      <div className="health-row">
        <p> Age: </p>
        <div className="health-inline">
          <input type="text" name="age"/>
          <p> Years</p>
        </div>
      </div>
      <div className="health-row">
        <p> Height: </p>
        <div>
          <p> Feet: </p>
          <input className="health-inline-text" type="text" name="feet"/>
          <p> Inches: </p>
          <input className="health-inline-text" type="text" name="inches"/>
        </div>
      </div>
      <div className="health-row">
        <p> Weight: </p>
        <div className="health-inline">
          <input type="text" name="age"/>
          <p> pounds </p>
        </div>
      </div>
      <div className="health-row">
        <p> Activity Level: </p>
        <div className="health-inline">
          <select>
            <option value="low"> Low </option>
            <option value="light"> Light </option>
            <option value="moderate"> Moderate </option>
            <option value="high"> High </option>
          </select>
          <p> Activity </p>
        </div>
      </div>
      <div className="health-row">
        <p> Goal: </p>
        <div className="health-inline">
          <select>
            <option value="lose"> Lose </option>
            <option value="maintain"> Maintain </option>
            <option value="gain"> Gain </option>
          </select>
          <p> Weight </p>
        </div>
      </div>
      <div className="health-row">
        <button onClick={submit}> 
          Submit
        </button>
      </div>
    </div>
  );

  }
