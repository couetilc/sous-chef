import './style.css';
import { useNavigate } from 'react-router';
import { useState, useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { useApi } from './useApi.jsx';

export default function Nutrition() {
  const navigate = useNavigate();
  const [currentDate, setCurrentDate] = useState('');
  const [nutritionData, setNutritionData] = useState([]);

  const [goals, setGoals] = useState({
    calories_goal: 2500,
    protein_goal_g: 150,
  });

  // ref for chart dom/instance
  const chartRef = useRef(null);
  const chartInstanceRef = useRef(null);
  const {api} = useApi();

  useEffect(() => {
    api.UserNutritionLastDay().then(response => {
      console.log('Nutrition last day data:', response);

      const updatedNutrition = [
        { label: 'Calories (kCal)', consumed: response.calories, goal: goals.calories_goal, color: '#f87171' },
        { label: 'Protein (g)', consumed: response.proteins, goal: goals.protein_goal_g, color: '#60a5fa' },
        { label: 'Fat (g)', consumed: response.fats, goal: 80, color: '#facc15' },
        { label: 'Carbohydrates (g)', consumed: response.carbs, goal: 300, color: '#4ade80' },
      ];

      setNutritionData(updatedNutrition);
    });
  }, []);

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

  // NEW: fetch recommendations on mount
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/user/health/recommendations/', {
          method: 'GET',
          credentials: 'include',
          headers: { Accept: 'application/json' },
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setGoals({
          calories_goal: data.calories_goal,
          protein_goal_g: data.protein_goal_g,
        });

        // If chart already exists, update its markLine immediately
        if (chartInstanceRef.current) {
          chartInstanceRef.current.setOption({
            series: [
              {
                // series[0] is the calories line
                markLine: {
                  data: [{ yAxis: data.calories_goal, name: 'Goal' }],
                  lineStyle: { type: 'dotted', color: '#666' },
                  label: {
                    formatter: `Goal: ${data.calories_goal}`,
                    position: 'insideEndTop',
                    color: '#666',
                    backgroundColor: 'rgba(255,255,255,0.7)',
                    padding: [2, 4],
                    borderRadius: 3,
                  },
                },
              },
            ],
          });
        }
      } catch (e) {
        console.error('Failed to load recommendations:', e);
      }
    })();
  }, []);

  const [lastWeek, setLastWeek] = useState(undefined);

  useEffect(() => {
    (async function () {
      const response = await api.UserCaloriesLastWeek();
      setLastWeek(response);
    })();
  }, [])

  useEffect(() => {
    const chartDom = document.getElementById('main');
    if (!chartDom) return;

    const myChart = echarts.init(chartDom);
    chartInstanceRef.current = myChart;

    if (!lastWeek) return;

    const days = [];
    const today = new Date();
    const calories = lastWeek.daily_calories.map(val => val.calories); // replace with lastWeek if available

    // Generate past 7 days labels
    for (let i = 6; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(today.getDate() - i);
      days.push(d.toLocaleDateString(undefined, { weekday: 'short' }));
    }

    // Compute cumulative averages for trend line
    const trendData = calories.map((_, i) => {
      const subset = calories.slice(0, i + 1);
      const avg = Number((subset.reduce((a, b) => a + b, 0) / subset.length).toFixed(1));
      return avg;
    });

    const option = {
      tooltip: { trigger: 'axis' },
      legend: { data: ['Calories Consumed', 'Trend (Average)'] },
      xAxis: { type: 'category', data: days },
      yAxis: { type: 'value', name: 'Calories', nameLocation: 'middle' },
      series: [
        {
          name: 'Calories Consumed',
          data: calories,
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: { width: 3, color: '#f87171' },
          itemStyle: { color: '#f87171' },
          areaStyle: { color: 'rgba(248,113,113,0.15)' },
          // NEW: goal line driven by API-loaded calories_goal
          markLine: {
            data: [{ yAxis: goals.calories_goal, name: 'Goal' }],
            lineStyle: { type: 'dotted', color: '#666' },
            label: {
              formatter: `Goal: ${goals.calories_goal}`,
              position: 'insideEndTop',
              color: '#666',
              backgroundColor: 'rgba(255,255,255,0.7)',
              padding: [2, 4],
              borderRadius: 3,
            },
          },
        },
        {
          name: 'Trend (Average)',
          data: trendData,
          type: 'line',
          smooth: true,
          symbol: 'none',
          lineStyle: { width: 2, color: '#60a5fa', type: 'dashed' },
          itemStyle: { color: '#60a5fa' },
        },
      ],
    };

    myChart.setOption(option);

    const onResize = () => myChart.resize();
    window.addEventListener('resize', onResize);

    return () => {
      window.removeEventListener('resize', onResize);
      myChart.dispose();
      chartInstanceRef.current = null;
    };
    // Rebuild chart when the goal changes so the markLine/label stay in sync
  }, [goals.calories_goal, lastWeek]);

  return (
    <div className="nutrition-page">
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
                    style={{ width: `${percentage}%`, backgroundColor: item.color }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        <div className="chart-section">
          <h2 className="chart-title">Calorie Intake (Past 7 Days)</h2>
          <div id="main" ref={chartRef} className="nutrition-chart"></div>
        </div>
      </div>
    </div>
  );
}
