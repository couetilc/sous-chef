import './style.css';
import { useNavigate } from 'react-router';
import { useApi } from './useApi';
import SousChefLogo from './souschef-logo.png';
import { useEffect, useState } from 'react';

export default function Inventory() {
  const navigate = useNavigate();
  const { api, isReady } = useApi() || {};

  const [ingredients, setIngredients] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [selectedIngredient, setSelectedIngredient] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load ingredients and user inventory when api is ready
  useEffect(() => {
    if (!isReady || !api) return;

    let mounted = true;

    const load = async () => {
      setLoading(true);
      try {
        const [ingList, invList] = await Promise.all([
          api.listIngredients(),
          api.UserInventory(),
        ]);

        if (!mounted) return;

        setIngredients(ingList || []);
        setInventory(invList || []);

        // default selected ingredient to first not-in-inventory
        const invIds = new Set((invList || []).map(i => i.ingredient.id));
        const firstAvailable = (ingList || []).find(i => !invIds.has(i.id));
        setSelectedIngredient(firstAvailable ? String(firstAvailable.id) : (ingList[0] ? String(ingList[0].id) : ''));
      } catch (err) {
        console.error(err);
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    load();

    return () => { mounted = false };
  }, [isReady, api]);

  const handleAdd = async () => {
    if (!selectedIngredient) return;
    setLoading(true);
    try {
      const created = await api.UserInventoryAddEntry({ ingredient_id: Number(selectedIngredient) });
      // API returns the created inventory item (id + ingredient)
      setInventory(prev => {
        // avoid duplicates
        if (prev.some(i => i.id === created.id)) return prev;
        return [created, ...prev].sort((a, b) => a.ingredient.name.localeCompare(b.ingredient.name));
      });

      // pick next available ingredient
      const invIds = new Set(inventory.map(i => i.ingredient.id).concat([Number(selectedIngredient)]));
      const next = ingredients.find(i => !invIds.has(i.id));
      setSelectedIngredient(next ? String(next.id) : '');
    } catch (err) {
      // some endpoints may return 204/empty body and cause parsing errors; surface a simple message
      console.error(err);
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  const handleDelete = async (inventoryId) => {
    setLoading(true);
    try {
      // Some delete endpoints return 204 and the fetch wrapper may attempt to parse JSON and throw.
      // Wrap in try/catch but optimistically remove the entry from UI on success.
      try {
        await api.UserInventoryDeleteEntry({ inventory_id: inventoryId });
      } catch (e) {
        // If the error is a 204/no-content parse error, fall through to remove locally.
        // Otherwise, rethrow so it's caught by outer catch.
        if (!e || (e && e.status && e.status !== 204)) {
          throw e;
        }
      }

      setInventory(prev => prev.filter(i => i.id !== inventoryId));
    } catch (err) {
      console.error(err);
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="centered-div">
      <img src={SousChefLogo} alt="logo" style={{ width: 120, height: 'auto' }} />
      <h1>Inventory</h1>

      {error && <div style={{ color: 'red' }}>Error: {error.message || JSON.stringify(error)}</div>}

      <div style={{ marginTop: 12 }}>
        <label htmlFor="ingredient-select">Add ingredient to inventory:&nbsp;</label>
        <select
          id="ingredient-select"
          value={selectedIngredient}
          onChange={(e) => setSelectedIngredient(e.target.value)}
          disabled={loading || ingredients.length === 0}
        >
          {ingredients.map(ing => (
            <option key={ing.id} value={String(ing.id)}>{ing.name}</option>
          ))}
        </select>
        <button onClick={handleAdd} disabled={loading || !selectedIngredient} style={{ marginLeft: 8 }}>Add</button>
      </div>

      <h2 style={{ marginTop: 20 }}>Your Inventory</h2>
      {loading && <div>Loading…</div>}
      {!loading && inventory.length === 0 && <div>No items in inventory.</div>}

      <ul>
        {inventory.map(item => (
          <li key={item.id} style={{ marginBottom: 8 }}>
            {item.ingredient.name}
            <button onClick={() => handleDelete(item.id)} style={{ marginLeft: 12 }}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  )
}
