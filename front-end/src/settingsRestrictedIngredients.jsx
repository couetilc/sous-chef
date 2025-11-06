import { useRef } from 'react';
import IngredientsSelect from './ingredientsSelect'
import { useApi } from './useApi';
import SelectRestrictedIngredients from './selectRestrictedIngredients.jsx'

export default function RestrictedIngredientsComponent(props) {
  const selectRef = useRef()

  return (
    <div className="settings-container">
      <h3>Edit Ingredient Restrictions</h3>
      <form className="ingredient-restriction-form">
        <SelectRestrictedIngredients ref={selectRef} />
        <button className="button-blue" type='button' onClick={() => {
          if (selectRef.current) {
            selectRef.current.updateIngredients()
          }
        }}>
          Update Ingredients
        </button>
      </form>
    </div>
  )
}
