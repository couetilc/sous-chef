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
  const [filters, setFilters] = useState({
    caloriesMin: '', caloriesMax: '',
    proteinMin: '', proteinMax: '',
    fatMin: '', fatMax: '',
    carbsMin: '', carbsMax: '',
    priceMin: '', priceMax: ''
  })

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
        <div style={{ marginBottom: 8, display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'flex-start' }}>
          <div style={{ minWidth: 240 }}>
            <input
              className="text-input"
              placeholder="Search inventory by name"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              style={{ padding: '6px 8px', width: '100%', maxWidth: 360 }}
            />
          </div>

          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {/* Nutrition filters: calories, protein, fat, carbs, price */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12 }}>Calories</label>
              <div style={{ display: 'flex', gap: 4 }}>
                <input className="text-input" placeholder="min" value={filters.caloriesMin} onChange={e => setFilters(f => ({ ...f, caloriesMin: e.target.value }))} style={{ width: 80 }} />
                <input className="text-input" placeholder="max" value={filters.caloriesMax} onChange={e => setFilters(f => ({ ...f, caloriesMax: e.target.value }))} style={{ width: 80 }} />
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12 }}>Protein (g)</label>
              <div style={{ display: 'flex', gap: 4 }}>
                <input className="text-input" placeholder="min" value={filters.proteinMin} onChange={e => setFilters(f => ({ ...f, proteinMin: e.target.value }))} style={{ width: 80 }} />
                <input className="text-input" placeholder="max" value={filters.proteinMax} onChange={e => setFilters(f => ({ ...f, proteinMax: e.target.value }))} style={{ width: 80 }} />
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12 }}>Fat (g)</label>
              <div style={{ display: 'flex', gap: 4 }}>
                <input className="text-input" placeholder="min" value={filters.fatMin} onChange={e => setFilters(f => ({ ...f, fatMin: e.target.value }))} style={{ width: 80 }} />
                <input className="text-input" placeholder="max" value={filters.fatMax} onChange={e => setFilters(f => ({ ...f, fatMax: e.target.value }))} style={{ width: 80 }} />
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12 }}>Carbs (g)</label>
              <div style={{ display: 'flex', gap: 4 }}>
                <input className="text-input" placeholder="min" value={filters.carbsMin} onChange={e => setFilters(f => ({ ...f, carbsMin: e.target.value }))} style={{ width: 80 }} />
                <input className="text-input" placeholder="max" value={filters.carbsMax} onChange={e => setFilters(f => ({ ...f, carbsMax: e.target.value }))} style={{ width: 80 }} />
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 12 }}>Price ($/g)</label>
              <div style={{ display: 'flex', gap: 4 }}>
                <input className="text-input" placeholder="min" value={filters.priceMin} onChange={e => setFilters(f => ({ ...f, priceMin: e.target.value }))} style={{ width: 80 }} />
                <input className="text-input" placeholder="max" value={filters.priceMax} onChange={e => setFilters(f => ({ ...f, priceMax: e.target.value }))} style={{ width: 80 }} />
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
              <button className="button" type="button" onClick={() => setFilters({ caloriesMin: '', caloriesMax: '', proteinMin: '', proteinMax: '', fatMin: '', fatMax: '', carbsMin: '', carbsMax: '', priceMin: '', priceMax: '' })}>Clear Filters</button>
            </div>
          </div>
        </div>
        <div className="inventory-ingredient-list">
          {data && data
            .filter(item => {
              if (searchTerm && !item.ingredient.name.toLowerCase().includes(searchTerm.toLowerCase())) return false

              // helper to parse numeric values safely
              const n = (val) => {
                const x = Number(val)
                return Number.isFinite(x) ? x : 0
              }

              const calories = n(item.ingredient.calories)
              const protein = n(item.ingredient.protein_g)
              const fat = n(item.ingredient.fat_g)
              const carbs = n(item.ingredient.carbs_g)
              const price = n(item.ingredient.price_g)

              if (filters.caloriesMin !== '' && calories < Number(filters.caloriesMin)) return false
              if (filters.caloriesMax !== '' && calories > Number(filters.caloriesMax)) return false
              if (filters.proteinMin !== '' && protein < Number(filters.proteinMin)) return false
              if (filters.proteinMax !== '' && protein > Number(filters.proteinMax)) return false
              if (filters.fatMin !== '' && fat < Number(filters.fatMin)) return false
              if (filters.fatMax !== '' && fat > Number(filters.fatMax)) return false
              if (filters.carbsMin !== '' && carbs < Number(filters.carbsMin)) return false
              if (filters.carbsMax !== '' && carbs > Number(filters.carbsMax)) return false
              if (filters.priceMin !== '' && price < Number(filters.priceMin)) return false
              if (filters.priceMax !== '' && price > Number(filters.priceMax)) return false

              return true
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
