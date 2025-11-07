import './style.css';
import { useNavigate } from 'react-router';
import { useApi } from './useApi';
import SousChefLogo from './souschef-logo.png';
import { useEffect, useState, useRef } from 'react';
import SelectInventoryIngredient from './selectInventoryIngredient.jsx'
import { useGET } from './useGET'

export default function Inventory() {
  const selectRef = useRef()
  const { data, refresh } = useGET('UserInventory')
  const { api } = useApi()
  const [searchTerm, setSearchTerm] = useState('')

  return (
    <div className="inventory-page">
      <h1>Inventory</h1>

      <div className="inventory-ingredient-add">
        <h2>
          Add Ingredient to Inventory
        </h2>
        <div>
          <SelectInventoryIngredient ref={selectRef} />
        </div>
        <button className="button" type="button" onClick={
          () => {
            if (selectRef.current) {
              selectRef.current.updateInventory().then(() => {
                refresh()
              })
            }
          }
        }>
          Add Selection
        </button>
      </div>

      <div className="inventory-ingredients">
        <h2>
          Your Inventory
        </h2>
        <div style={{ marginBottom: 8 }}>
          <input
            className="text-input"
            placeholder="Search inventory by name"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            style={{ padding: '6px 8px', width: '100%', maxWidth: 360 }}
          />
        </div>
        <div className="inventory-ingredient-list">
          {data && data
            .filter(item => {
              if (!searchTerm) return true
              return item.ingredient.name.toLowerCase().includes(searchTerm.toLowerCase())
            })
            .map(item => (
            <div className="inventory-item">
              <div className="inventory-item-name">{item.ingredient.name}</div>
              <ul className="inventory-item-nutrition">
                <li>calories: {item.ingredient.calories}</li>
                <li>protein (g): {item.ingredient.protein_g}</li>
                <li>fat (g): {item.ingredient.fat_g}</li>
                <li>carbs (g): {item.ingredient.carbs_g}</li>
                <li>price ($/g): {item.ingredient.price_g}</li>
              </ul>
              <button className="button-blue" type="button" onClick={
                () => {
                  api.UserInventoryDeleteEntry({ inventory_id: item.id })
                    .then(() => {
                      refresh()
                    })
                }
              }>
                Delete
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
