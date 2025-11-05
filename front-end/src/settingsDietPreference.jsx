import React, { useState, useEffect } from 'react';
import './style.css';
import SousChefLogo from './souschef-logo.png';
import { useApi } from './useApi';
import DietsSelect from './dietsSelect'

const DietComponent = () => {
  const { api } = useApi();

  // Fetch and populate diet and ingredient list, selected diets/ingredients
  const [diets, setDiets] = useState([]);
  const [selectedDiets, setSelectedDiets] = useState([]);
  const [fetchedSelectedDiets, setFetchedSelectedDiets] = useState([]);

  useEffect(() => {
    // Get diets and user selections
    api.listDiets()
      .then((result) => {
        console.log(result)
        setDiets(result)
      });
    api.listSelectedDiets()
      .then((result) => {
        const fetchedList = result.map(({ id, name }) => ({ value: id, label: name }))
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


  return (
    <div className="settings-container">
      <h3>Edit Diet Restrictions</h3>
      <form className="diet-form" onSubmit={publishDiet}>
        <DietsSelect isMulti
          options={selectedDiets}
          onChange={options => setSelectedDiets(options)}
        />
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
        <button className="button-blue" type='submit'>Update Diet</button>
      </form>
    </div>
  );
};

export default DietComponent;
