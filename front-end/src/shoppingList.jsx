import React from 'react';

export default function ShoppingList({ shoppingList, onRefresh }) {
  if (!shoppingList) {
    return (
      <div className="shopping-list-card">
        <h3>Shopping List</h3>
        <p>No shopping list available for this week.</p>
        <button className="button" onClick={onRefresh}>Refresh</button>
      </div>
    );
  }

  // support both flat items or grouped by aisle
  const groups = shoppingList.groups ?? [{ title: 'Items', items: shoppingList.items ?? shoppingList }];

  return (
    <div className="shopping-list-card">
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
        <h3>Shopping List</h3>
        <div>
          <button className="button" onClick={onRefresh}>Refresh</button>
        </div>
      </div>

      {groups.map((g, idx) => (
        <div key={idx} style={{marginBottom:12}}>
          {g.title && <strong>{g.title}</strong>}
          <ul style={{margin:6,paddingLeft:18}}>
            {(g.items || []).map((it, i) => {
              // try common shapes
              const name = it.name ?? it.item ?? String(it);
              const qty = it.quantity ?? it.qty ?? it.amount;
              const unit = it.unit ?? '';
              return <li key={i} className="shopping-list-item">{name}{qty ? ` — ${qty}${unit ? ' ' + unit : ''}` : ''}</li>;
            })}
          </ul>
        </div>
      ))}
    </div>
  );
}
