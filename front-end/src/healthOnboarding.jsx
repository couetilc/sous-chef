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
  const [age, setAge] = useState(0);
  const [height_ft, setHeight_ft] = useState(0);
  const [height_in, setHeight_in] = useState(0);
  const [weight, setWeight] = useState(0);
  const [activity_level, setActivityLevel] = useState('low');
  const [goal, setGoal] = useState('maintain');
  const [sex, setSex] = useState('male');

  function navToHome() {
    return navigate("/home");
  }

  function submit() {
 
    api.setHealthInfo({age, height_ft, height_in, weight, activity_level, goal});
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
          <input type="text" name="age" value={age}
            onChange={e => setAge(e.target.value)}/>
          <p> Years</p>
        </div>
      </div>
      <div className="health-row">
        <p> Height: </p>
        <div>
          <p> Feet: </p>
          <input className="health-inline-text" type="text" name="feet" value={height_ft}
            onChange={e => setHeight_ft(e.target.value)}/>
          <p> Inches: </p>
          <input className="health-inline-text" type="text" name="inches" value={height_in}
            onChange={e => setHeight_in(e.target.value)}/>
        </div>
      </div>
      <div className="health-row">
        <p> Weight: </p>
        <div className="health-inline">
          <input type="text" name="age" value={weight}
            onChange={e => setWeight(e.target.value)}/>
          <p> pounds </p>
        </div>
      </div>
      <div className="health-row">
        <p> Activity Level: </p>
        <div className="health-inline">
          <select value={activity_level} onChange={e => setActivityLevel(e.target.value)}>
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
          <select value={goal} onChange={e => setGoal(e.target.value)}>
            <option value="lose"> Lose </option>
            <option value="maintain"> Maintain </option>
            <option value="gain"> Gain </option>
          </select>
          <p> Weight </p>
        </div>
      </div>
      <div className="health-row">
        <p> Sex: </p>
        <div className="health-inline">
          <select value={sex} onChange={e => setSex(e.target.value)}>
            <option value="male"> Male </option>
            <option value="female"> Female </option>
          </select>
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
