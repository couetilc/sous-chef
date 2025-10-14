import React, { useState, useEffect } from 'react';
import './style.css';
import SousChefLogo from './souschef-logo.png';
import { useApi } from './useApi';

const DietComponent = () => {
    const api = useApi();

    // Fetch and populate ingredient list, selected diets/ingredients
    const [ingredients, setIngredients] = useState([]);
    const [selectedDiets, setSelectedDiets] = useState([]);
    const [selectedIngredients, setSelectedIngredients] = useState([]);
    const [fetchedSelectedIngredients, setFetchedSelectedIngredients] = useState([]);

    useEffect(() => {
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
    }, [])


    function publishDiet(e) {

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
                const fetchedList = result.map(({ id, name }) => (id))
                setSelectedIngredients(fetchedList);
                setFetchedSelectedIngredients(fetchedList);
            })

    }

    return (
        <div className="diet">
            <form onSubmit={publishDiet}>
                <p>
                    <label>
                        Select diets: <br />
                        <select
                            name="dietSelect"
                            multiple={true}
                            value={selectedDiets}
                            onChange={e => setSelectedDiets(e.target.value)}
                        >
                            <option value="vegetarian">Vegetarian</option>
                            <option value="vegan">Vegan</option>
                            <option value="gf">Gluten-Free</option>
                        </select>
                    </label>
                </p>
                <p>
                    <button type='submit'>Update Diet</button>
                </p>
            </form>
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
    );
};

export default DietComponent;