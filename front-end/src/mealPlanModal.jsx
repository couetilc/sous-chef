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
        <p><strong>Servings:</strong> {meal.servings}</p>
        <h3>Nutrition</h3>
        <ul>
          <li>Calories: {recipe.calories_per_serving * meal.servings} kCal</li>
          <li>Protein: {recipe.protein_g * meal.servings}g</li>
          <li>Fat: {recipe.fat_g * meal.servings}g</li>
          <li>Carbs: {recipe.carbs_g * meal.servings}g</li>
        </ul>
      </div>
    </div>
  );
}
