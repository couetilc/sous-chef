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

    useEffect(() => {
        api.listIngredients()
            .then((result) => {
                console.log(result)
                setIngredients(result)
            });
        api.listRestricted()
            .then((result) => {
                console.log(result)
                setSelectedIngredients(result)
            })
    }, [])


    function publishDiet(e) {

    }

    function publishRestrictions(e) {
        e.preventDefault();

        const form = e.target;
        const formData = new FormData(form);
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
// <option value="chicken">Chicken</option>
export default DietComponent;