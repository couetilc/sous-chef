import { useEffect, useState, useRef } from 'react';
import { useApi } from 'useApi.jsx';

export default function AddTagDialog({ recipe }) {

  const [tag, setTag] = useState('');
  const [newTag, setNewTag] = useState('');
  const [tagSelect, setTagSelect] = useState([]);

  useEffect(() => {
    //api call to populate tagSelect with users's existing tags
  }, [])


  //user is given from api.getCurrentUser()

  useEffect(() => {
    const original = document.bodystyle.overflow
    document.body.style.overflow = "hidden"
  }, [])


  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
      }}
    }
      <h1> Select Tag </h1>
      <p> {recipe.recipe_name} </p>
      <input type="text" value={newTag} onChange={e => setNewTag(e.target.value)}/>
      <select
        id="tag-select"
        multiple={true}
        value={tagOptions}
        onChange={e =>setTagSelect(e.target.selectedOption)}/>
      </select>
    </div>
  )
}
