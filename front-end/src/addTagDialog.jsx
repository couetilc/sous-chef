import { useEffect, useState } from 'react';
import { useApi } from 'useApi.jsx';

export default function AddTagDialog({ recipe }) {


  const [tag, setTag] = useState('');
  const [new, setNewTag] = useState('');

  useEffect(() => {
    //get user's existing tags on page load
    
  }, [])

  //user is given from api.getCurrentUser()

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
      }}
    }
      <p> {recipe.recipe_name} </p>
      <input type="text" value={newTag} onChange={e => setNewTag(e.target.value)}/>
    </div>
  )
}
