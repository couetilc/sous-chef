import React, { useState, useEffect, useRef } from 'react';
import './style.css';
import SousChefLogo from './souschef-logo.png';
import { useApi } from './useApi';
import DietsSelect from './dietsSelect'

const DietComponent = () => {
  const dietsRef = useRef()

  return (
    <div className="settings-container">
      <h3>Edit Diet Restrictions</h3>
      <form className="diet-form">
        <DietsSelect ref={dietsRef} isMulti />
        <button
          className="button-blue"
          type='button'
          onClick={() => {
            if (dietsRef.current) {
              dietsRef.current.updateDiets()
            }
          }}
        >
          Update Diet
        </button>
      </form>
    </div>
  );
};

export default DietComponent;
