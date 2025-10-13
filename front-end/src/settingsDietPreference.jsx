import React, { useState, useEffect } from 'react';
import './style.css';
import SousChefLogo from './souschef-logo.png';
import { useApi } from './useApi';

const DietComponent = () => {
    const api = useApi();
    // Fetch and populate ingredient list
    const [ingredients, setIngredients] = useState([]);
    useEffect(() => {
        api.listIngredients()
            .then((result) => {
                setIngredients(result)
            }).then(() => {
                console.log(ingredients)
            }
            )
    }, [])

    function publish(formData) {

    }

    return (
        <div className="diet">
            <form action={publish}>
                <p>
                    <label>
                        Select diets: <br />

                        {/*TODO use react mapping to list these items after fetching*/}

                        <select name="selectedDiet" multiple={true}>
                            <option value="vegetarian">Vegetarian</option>
                            <option value="vegan">Vegan</option>
                            <option value="gf">Gluten-Free</option>
                        </select>
                    </label>
                </p>
                <p>
                    <label>
                        Select ingredients: <br />

                        {/*TODO use react mapping to list these items after fetching*/}

                        <select name="selectedIngredient" multiple={true}>
                            {
                                ingredients.map((ingredient) =>
                                    <option>{ingredient.name}</option>
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
    );
};
// <option value="chicken">Chicken</option>
export default DietComponent;