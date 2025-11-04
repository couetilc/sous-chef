import React, { useState, useEffect } from 'react';
import './style.css';
import SousChefLogo from './souschef-logo.png';
import { useApi } from './useApi';

const DietComponent = () => {
    const { api } = useApi();

    // Fetch and populate diet and ingredient list, selected diets/ingredients
    const [diets, setDiets] = useState([]);
    const [ingredients, setIngredients] = useState([]);
    const [selectedDiets, setSelectedDiets] = useState([]);
    const [fetchedSelectedDiets, setFetchedSelectedDiets] = useState([]);
    const [selectedIngredients, setSelectedIngredients] = useState([]);
    const [fetchedSelectedIngredients, setFetchedSelectedIngredients] = useState([]);

    useEffect(() => {
        // Get ingredients and user selections
        api.listIngredients()
            .then((result) => {
                console.log(result)
                setIngredients(result)
            });
        api.listRestricted()
            .then((result) => {
                const fetchedList = result.map(({ id, name }) => (id))
                setSelectedIngredients(fetchedList);
                setFetchedSelectedIngredients(fetchedList);
            })

        // Get diets and user selections
        api.listDiets()
            .then((result) => {
                console.log(result)
                setDiets(result)
            });
        api.listSelectedDiets()
            .then((result) => {
                const fetchedList = result.map(({ id, name }) => (id))
                setSelectedDiets(fetchedList);
                setFetchedSelectedDiets(fetchedList);
            })

    }, [])


    function publishDiet(e) {
        e.preventDefault();

        // Create maps for selected and fetched ingredients to find diff group
        // There is probably some better way to create the maps but I don't know it
        const newDietsMap = new Map();
        selectedDiets.forEach((dietId) => {
            newDietsMap.set(parseInt(dietId, 10), true)
        });

        const oldDietsMap= new Map();
        fetchedSelectedDiets.forEach((dietId) => {
            oldDietsMap.set(parseInt(dietId, 10), true)
        });

        // Create diff lists
        const addedDiets = [];
        selectedDiets.forEach((dietId) => {
            // IDs in selected ingredients are stored as strings
            const intID = parseInt(dietId, 10)
            if (!oldDietsMap.has(intID)) {
                addedDiets.push(intID);
            }
        });

        const removedDiets = []
        fetchedSelectedDiets.forEach((dietId) => {
            if (!newDietsMap.has(dietId)) {
                removedDiets.push(dietId);
            }
        });

        console.log(oldDietsMap)
        console.log(newDietsMap)
        console.log(addedDiets)
        console.log(removedDiets)

        // Forward diff lists to server
        api.postDiets({ added: addedDiets, removed: removedDiets })
            .then((result) => {
                return api.listSelectedDiets()
            })
            .then((result) => {
                alert("Updated Diets!")
                const fetchedList = result.map(({ id, name }) => (id))
                setSelectedDiets(fetchedList);
                setFetchedSelectedDiets(fetchedList);
            })

    }

    function publishRestrictions(e) {
        e.preventDefault();

        // Create maps for selected and fetched ingredients to find diff group
        // There is probably some better way to create the maps but I don't know it
        const newIngredientsMap = new Map();
        selectedIngredients.forEach((ingredientId) => {
            newIngredientsMap.set(parseInt(ingredientId, 10), true)
        });

        const oldIngredientsMap = new Map();
        fetchedSelectedIngredients.forEach((ingredientId) => {
            oldIngredientsMap.set(ingredientId, true)
        });

        // Create diff lists
        const addedIngredients = [];
        selectedIngredients.forEach((ingredientId) => {
            // IDs in selected ingredients are stored as strings
            const intID = parseInt(ingredientId, 10)
            if (!oldIngredientsMap.has(intID)) {
                addedIngredients.push(intID);
            }
        });

        const removedIngredients = []
        fetchedSelectedIngredients.forEach((ingredientId) => {
            if (!newIngredientsMap.has(ingredientId)) {
                removedIngredients.push(ingredientId);
            }
        });

        console.log(oldIngredientsMap)
        console.log(newIngredientsMap)
        console.log(addedIngredients)
        console.log(removedIngredients)

        // Forward diff lists to server
        api.postDietIngredients({ added: addedIngredients, removed: removedIngredients })
            .then((result) => {
                return api.listRestricted()
            })
            .then((result) => {
                alert("Updated ingredients!")
                const fetchedList = result.map(({ id, name }) => (id))
                setSelectedIngredients(fetchedList);
                setFetchedSelectedIngredients(fetchedList);
            })

    }

    return (
        <>
            <div className="settings-container">
              <form onSubmit={publishDiet}>
                  <p>
                      <label>
                          Select diets: <br />
                          <select
                              name="dietSelect"
                              multiple={true}
                              value={selectedDiets}
                              onChange={e => {
                                  const options = [...e.target.selectedOptions]
                                  const values = options.map(option => option.value)
                                  setSelectedDiets(values)
                              }}
                          >
                              {
                                  diets.map((diet) =>
                                      <option value={diet.id}>{diet.name}</option>
                                  )
                              }
                          </select>
                      </label>
                  </p>
                  <p>
                      <button type='submit'>Update Diet</button>
                  </p>
              </form>
            </div>
      <div className="settings-container">
            <form onSubmit={publishRestrictions}>
                <p>
                    <label>
                        Select ingredients: <br />
                        <select
                            name="ingredientSelect"
                            multiple={true}
                            value={selectedIngredients}
                            onChange={e => {
                                const options = [...e.target.selectedOptions]
                                const values = options.map(option => option.value)
                                setSelectedIngredients(values)
                            }}
                        >
                            {
                                ingredients.map((ingredient) =>
                                    <option value={ingredient.id}>{ingredient.name}</option>
                                )
                            }
                        </select>
                    </label>
                </p>
                <p>
                    <button type='submit'>Update Ingredients</button>
                </p>
            </form>
            </div>
        </>
    );
};

export default DietComponent;
