import React, { useState, useEffect } from 'react';
import { useApi } from './useApi';
import {
    Card,
    CardContent,
    Button,
    Typography,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Stack,
    Chip,
    Box,
    OutlinedInput
} from '@mui/material';
import RestaurantMenuIcon from '@mui/icons-material/RestaurantMenu';
import BlockIcon from '@mui/icons-material/Block';

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

    }, [api])


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
        <Card sx={{ height: '100%' }}>
            <CardContent>
                <Stack spacing={3}>
                    {/* Diets Section */}
                    <Box component="form" onSubmit={publishDiet}>
                        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <RestaurantMenuIcon /> Dietary Preferences
                        </Typography>
                        <Stack spacing={2}>
                            <FormControl fullWidth size="small">
                                <InputLabel id="diet-select-label">Select Diets</InputLabel>
                                <Select
                                    labelId="diet-select-label"
                                    multiple
                                    value={selectedDiets}
                                    onChange={(e) => setSelectedDiets(e.target.value)}
                                    input={<OutlinedInput label="Select Diets" />}
                                    renderValue={(selected) => (
                                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                            {selected.map((value) => {
                                                const diet = diets.find(d => d.id === value);
                                                return diet ? <Chip key={value} label={diet.name} size="small" /> : null;
                                            })}
                                        </Box>
                                    )}
                                >
                                    {diets.map((diet) => (
                                        <MenuItem key={diet.id} value={diet.id}>
                                            {diet.name}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                            <Button type="submit" variant="contained" color="primary" fullWidth>
                                Update Diet
                            </Button>
                        </Stack>
                    </Box>

                    {/* Restricted Ingredients Section */}
                    <Box component="form" onSubmit={publishRestrictions}>
                        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <BlockIcon /> Restricted Ingredients
                        </Typography>
                        <Stack spacing={2}>
                            <FormControl fullWidth size="small">
                                <InputLabel id="ingredient-select-label">Select Ingredients to Restrict</InputLabel>
                                <Select
                                    labelId="ingredient-select-label"
                                    multiple
                                    value={selectedIngredients}
                                    onChange={(e) => setSelectedIngredients(e.target.value)}
                                    input={<OutlinedInput label="Select Ingredients to Restrict" />}
                                    renderValue={(selected) => (
                                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                            {selected.map((value) => {
                                                const ingredient = ingredients.find(i => i.id === value);
                                                return ingredient ? <Chip key={value} label={ingredient.name} size="small" /> : null;
                                            })}
                                        </Box>
                                    )}
                                >
                                    {ingredients.map((ingredient) => (
                                        <MenuItem key={ingredient.id} value={ingredient.id}>
                                            {ingredient.name}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                            <Button type="submit" variant="contained" color="primary" fullWidth>
                                Update Ingredients
                            </Button>
                        </Stack>
                    </Box>
                </Stack>
            </CardContent>
        </Card>
    );
};

export default DietComponent;