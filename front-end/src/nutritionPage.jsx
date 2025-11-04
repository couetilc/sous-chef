import './style.css';
import { useNavigate } from 'react-router';
import { useState, useEffect } from 'react';

import * as echarts from 'echarts';


export default function Nutrition() {
  const navigate = useNavigate();
  const [currentDate, setCurrentDate] = useState('');

  useEffect(() => {
    const today = new Date();
    const formattedDate = today.toLocaleDateString(undefined, {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
    setCurrentDate(formattedDate);
  }, []);

  const nutritionData = [
    { label: 'Calories', consumed: 2000, goal: 2500, color: '#f87171' },
    { label: 'Protein', consumed: 120, goal: 150, color: '#60a5fa' },
    { label: 'Fat', consumed: 60, goal: 80, color: '#facc15' },
    { label: 'Carbohydrates', consumed: 220, goal: 300, color: '#4ade80' },
  ];

  useEffect(() => {
    var chartDom = document.getElementById('main');
    var myChart = echarts.init(chartDom);

    const days = [];
    const calories = [2100, 2300, 1950, 2600, 2400, 2200, 2500]; // example values
    const today = new Date();

    for (let i = 6; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(today.getDate() - i);
      days.push(d.toLocaleDateString(undefined, { weekday: 'short' }));
    } 
    const option = {
      title: {
        text: 'Calorie Intake (Past 7 Days)',
        left: 'left',
        textStyle: {
          fontSize: 16,
          fontWeight: 600,
        },
      },
      tooltip: {
        trigger: 'axis',
      },
      xAxis: {
        type: 'category',
        data: days,
      },
      yAxis: {
        type: 'value',
        name: 'Calories',
      },
      series: [
        {
          name: 'Calories Consumed',
          data: calories,
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: {
            width: 3,
            color: '#f87171',
          },
          itemStyle: {
            color: '#f87171',
          },
          areaStyle: {
            color: 'rgba(248,113,113,0.15)',
          },
          markLine: {
            data: [
              {
                yAxis: 2500,
                name: 'Goal',
              },
            ],
            lineStyle: {
              type: 'dotted',
              color: '#666',
            },
            label: {
              formatter: 'Goal: 2500',
              position: 'insideEndTop',
              color: '#666',
              backgroundColor: 'rgba(255,255,255,0.7)',
              padding: [2, 4],
              borderRadius: 3,
            },
          },
        },
      ],
    };

    myChart.setOption(option);
    window.addEventListener('resize', () => myChart.resize());

    return () => {
      window.removeEventListener('resize', () => myChart.resize());
      myChart.dispose();
    };

  }, []);

  return (
    <div className="centered-div">
      <h1>Daily Nutrition Tracker</h1>

      <div className="nutrition-section">
        <div className="nutrition-date">{currentDate}</div>

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

        <div className="chart-container">
          <div id="main" style={{ width: '600px', height: '400px' }}></div>

        </div>
      </div>
    </div>
  );
}
