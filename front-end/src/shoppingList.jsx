import React from 'react';

export default function ShoppingList({ shoppingList, onRefresh }) {
  if (!shoppingList) {
    return (
      <div className="shopping-list-card">
        <h3>Shopping List</h3>
        <p>No shopping list available for this week.</p>
      </div>
    );
  }

  // Prefer the API's missing_ingredients array; fall back to items or empty list
  const ingredients = Array.isArray(shoppingList.missing_ingredients)
    ? shoppingList.missing_ingredients
    : Array.isArray(shoppingList.items)
      ? shoppingList.items
      : [];

  return (
    <div className="shopping-list-card">
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
        <h3>Shopping List</h3>
      </div>

      <ul style={{margin:6,paddingLeft:18, listStyle: 'none' }}>
        {ingredients.length === 0 && <li>No missing ingredients.</li>}
        {ingredients.map((it, i) => {
          const label = it.display_name ?? it.name ?? String(it);
          const key = it.id ?? `${label}-${i}`;
          return <li key={key} className="shopping-list-item">{label}</li>;
        })}
      </ul>
    </div>
  );
}
