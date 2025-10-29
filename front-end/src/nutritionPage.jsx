import './style.css';
import {useNavigate} from 'react-router';

import SousChefLogo from './souschef-logo.png';

export default function Nutrition() {
  const navigate = useNavigate();

  const nutritionData = [
    { label: 'Calories', consumed: 2000, goal: 2500, color: '#f87171' },
    { label: 'Protein', consumed: 120, goal: 150, color: '#60a5fa' },
    { label: 'Fat', consumed: 60, goal: 80, color: '#facc15' },   
    { label: 'Carbohydrates', consumed: 220, goal: 300, color: '#4ade80' },
  ];

  return (
    <div className="centered-div">
      <h1>NUTRITION</h1>
      <p>Welcome to the Nutrition Interface page!</p>

      <div className="nutrition-container">
        {nutritionData.map((item, index) => {
          const percentage = Math.min((item.consumed / item.goal) * 100, 100);
          return (
            <div key={index} className="nutrition-bar">
              <div className="nutrition-label">
                <strong>{item.label}</strong>
                <div className="nutrition-amount">
                  {item.consumed}/{item.goal}
                </div>
              </div>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{
                    width: `${percentage}%`,
                    backgroundColor: item.color,
                  }}
                ></div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
