import React from 'react';
import './style.css';

export default function MealPlanModal({ meal, onClose }) {
  if (!meal) return null;

  const recipe = meal.recipe;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        
        <button className="modal-close" onClick={onClose}>×</button>

        <h2>{recipe.title}</h2>

        {recipe.image_url && (
          <img className="modal-image" src={recipe.image_url} alt={recipe.title} />
        )}

        <p><strong>Prep/Cook Time:</strong> {recipe.total_time_min || 0} min</p>

        <h3>Nutrition (per serving)</h3>
        <ul>
          <li>Calories: {recipe.calories_per_serving}</li>
          <li>Protein: {recipe.protein_g} g</li>
          <li>Fat: {recipe.fat_g} g</li>
          <li>Carbs: {recipe.carbs_g} g</li>
        </ul>
      </div>
    </div>
  );
}
