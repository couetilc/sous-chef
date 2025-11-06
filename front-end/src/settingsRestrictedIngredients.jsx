import { useRef } from 'react';
import IngredientsSelect from './ingredientsSelect'
import { useApi } from './useApi';
import SelectRestrictedIngredients from './selectRestrictedIngredients.jsx'

export default function RestrictedIngredientsComponent(props) {
  // const { api } = useApi();
  // const [ingredients, setIngredients] = useState([]);
  // const [selectedIngredients, setSelectedIngredients] = useState([]);
  // const [fetchedSelectedIngredients, setFetchedSelectedIngredients] = useState([]);

  const selectRef = useRef()

  // useEffect(() => {
  //   // Get ingredients and user selections
  //   api.listIngredients()
  //     .then((result) => {
  //       console.log(result)
  //       setIngredients(result.results)
  //     });
  //   api.listRestricted()
  //     .then((result) => {
  //       const fetchedList = result.map(({ id, name }) => (id))
  //       setSelectedIngredients(fetchedList);
  //       setFetchedSelectedIngredients(fetchedList);
  //     })
  // }, [])
  //
  // function publishRestrictions(e) {
  //   e.preventDefault();
  //
  //   // Create maps for selected and fetched ingredients to find diff group
  //   // There is probably some better way to create the maps but I don't know it
  //   const newIngredientsMap = new Map();
  //   selectedIngredients.forEach((ingredientId) => {
  //     newIngredientsMap.set(parseInt(ingredientId, 10), true)
  //   });
  //
  //   const oldIngredientsMap = new Map();
  //   fetchedSelectedIngredients.forEach((ingredientId) => {
  //     oldIngredientsMap.set(ingredientId, true)
  //   });
  //
  //   // Create diff lists
  //   const addedIngredients = [];
  //   selectedIngredients.forEach((ingredientId) => {
  //     // IDs in selected ingredients are stored as strings
  //     const intID = parseInt(ingredientId, 10)
  //     if (!oldIngredientsMap.has(intID)) {
  //       addedIngredients.push(intID);
  //     }
  //   });
  //
  //   const removedIngredients = []
  //   fetchedSelectedIngredients.forEach((ingredientId) => {
  //     if (!newIngredientsMap.has(ingredientId)) {
  //       removedIngredients.push(ingredientId);
  //     }
  //   });
  //
  //   console.log(oldIngredientsMap)
  //   console.log(newIngredientsMap)
  //   console.log(addedIngredients)
  //   console.log(removedIngredients)
  //
  //   // Forward diff lists to server
  //   api.postDietIngredients({ added: addedIngredients, removed: removedIngredients })
  //     .then((result) => {
  //       return api.listRestricted()
  //     })
  //     .then((result) => {
  //       alert("Updated ingredients!")
  //       const fetchedList = result.map(({ id, name }) => (id))
  //       setSelectedIngredients(fetchedList);
  //       setFetchedSelectedIngredients(fetchedList);
  //     })
  //
  // }
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
