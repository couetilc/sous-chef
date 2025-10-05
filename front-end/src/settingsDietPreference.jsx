import React, { useState } from 'react';
import './style.css';
import SousChefLogo from './souschef-logo.png';


const DietComponent = () => {
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
                            <option value="chicken">Chicken</option>
                            <option value="potatoes">Potatoes</option>
                            <option value="milk">Milk</option>
                            <option value="protein">Peanuts</option>
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

export default DietComponent;