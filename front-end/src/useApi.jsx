import { createContext, useState, useEffect, useContext, useMemo } from 'react';

const ApiContext = createContext();

export class Api {
  READY_STATES = {
    YES: 0,
    NO: 1,
    PENDING: 2,
  }

  constructor() {
    this.csrfToken = undefined;
    this.ready_state = this.READY_STATES.NO;
    this.initializationPromise = null;
  }

  isReady() {
    return this.ready_state === this.READY_STATES.YES;
  }

  async becomeReady() {
    // If already ready, do nothing
    if (this.ready_state === this.READY_STATES.YES) {
      return;
    }

    // If currently pending, wait for the existing initialization
    if (this.ready_state === this.READY_STATES.PENDING && this.initializationPromise) {
      return this.initializationPromise;
    }

    // Start new initialization
    this.ready_state = this.READY_STATES.PENDING;
    this.initializationPromise = (async () => {
      try {
        const response = await fetch('/api/csrf/', { credentials: 'include' })
          .then(res => res.json());

        if (response.csrfToken) {
          console.log('received token ', response.csrfToken)
          this.csrfToken = response.csrfToken;
          this.ready_state = this.READY_STATES.YES;
        } else {
          console.log('token not ready')
          this.ready_state = this.READY_STATES.NO;
        }
      } catch (error) {
        console.log('token error')
        this.ready_state = this.READY_STATES.NO;
        throw error;
      } finally {
        this.initializationPromise = null;
      }
    })();

    return this.initializationPromise;
  }

  async ensureReady() {
    if (!this.isReady()) {
      await this.becomeReady();
    }
  }

  async fetch(resource, options = {}) {
    // Ensure we have a CSRF token before making the request
    await this.ensureReady();

    if (options.body && !options.method) {
      options.method = 'POST'
    }

    return fetch(resource, {
      ...options,
      headers: {
        ...options.headers,
        'Content-Type': 'application/json',
        'X-CSRFToken': this.csrfToken,
      },
      credentials: 'include',
    }).then(async (res) => {
      // Try to parse JSON, but handle cases where response is not JSON
      let data;
      const contentType = res.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        try {
          data = await res.json();
        } catch (e) {
          console.error('Failed to parse JSON response:', e);
          data = { error: 'Invalid JSON response from server' };
        }
      } else {
        // Not JSON - might be HTML error page
        const text = await res.text();
        console.error('Non-JSON response received:', text.substring(0, 200));
        data = { error: 'Server returned non-JSON response', details: text.substring(0, 200) };
      }
      
      if (!res.ok) {
        throw { status: res.status, data };
      }
      return data;
    })
  }

  async login({ username, password }) {
    const result = await this.fetch('/api/login/', {
      body: JSON.stringify({ username, password }),
    });

    // Django rotates CSRF token on login, so we need to fetch the new one
    this.ready_state = this.READY_STATES.NO;
    this.csrfToken = undefined;
    await this.becomeReady();

    return result;
  }

  async register({ username, email, password, password_confirm, first_name, last_name }) {
    try {
      return await this.fetch('/api/register/', {
        body: JSON.stringify({
          username,
          email,
          password,
          password_confirm,
          first_name,
          last_name
        }),
      });
    } catch (error) {
      console.error('Registration API error:', error);
      throw error;
    }
  }

  async updateEmail({ email }) {
    return this.fetch('/api/user/updateEmail/', {
      body: JSON.stringify({
        email,
      }),
    })
  }

  async updatePassword({ password }) {
    return this.fetch('/api/user/updatePassword/', {
      body: JSON.stringify({
        password,
      }),
    })
  }

  async listIngredients({ page = 1, search } = {}, options) {
    const url = new URL('/api/ingredients/', window.location.href)
    if (page) url.searchParams.set('page', page)
    if (search) url.searchParams.set('search', search)
    return this.fetch(url.toString(), options);
  }

  async listCuratedIngredients({ page = 1, search, exclude_inventory } = {}, options) {
    const url = new URL('/api/curated_ingredients/', window.location.href)
    if (page) url.searchParams.set('page', page)
    if (search) url.searchParams.set('search', search)
    if (exclude_inventory) url.searchParams.set('exclude_inventory', 'true')
    return this.fetch(url.toString(), options);
  }

  async listRestricted() {
    return this.fetch('/api/ingredients/restricted', {})
  }

  async postDietIngredients({added, removed}) {
    return this.fetch('/api/ingredients/updateRestricted/', {
      body: JSON.stringify({
        added,
        removed
      })
    })
  }

  async listDiets() {
    return this.fetch('/api/diets/', {});
  }

  async listSelectedDiets() {
    return this.fetch('/api/diets/selected/', {});
  }

  async postDiets({added, removed}) {
    return this.fetch('/api/diets/updateSelected/', {
      body: JSON.stringify({
        added,
        removed
      })
    })
  }

  async syncDiets({ diet_ids }) {
    return this.fetch('/api/diets/sync/', {
      body: JSON.stringify({ diet_ids })
    })
  }

  async logout() {
    return this.fetch('/api/logout/', { method: "POST" })
  }

  async getCurrentUser() {
    return this.fetch('/api/user/')
  }

  async deleteUser({username, password}) {
    return this.fetch('/api/user/delete/', {
      body: JSON.stringify({
        username,
        password
      })
    })
  }

  async getOnboardingStatus() {
    return this.fetch('/api/user/isOnboarded/')
  }

  async setOnboardingStatus({new_onboarded, new_skipped}) {
   return this.fetch('/api/user/updateOnboarded/', {
     body: JSON.stringify({
       new_onboarded,
       new_skipped
     })
   })
  }

  async getHealthInfo() {
    return this.fetch('/api/user/health');
  }

  async setHealthInfo({age, height_ft, height_in, weight, activity_level, goal, sex}) {
    return this.fetch('/api/user/updateHealth/', {method: "POST",
      body: JSON.stringify({
        age,
        height_ft,
        height_in,
        weight,
        activity_level,
        goal,
        sex
      })
    })
  }

  async getRecipesFiltered({title, ingredients, searchInventory, searchFavorite, searchMyRecipes, curated_ingredients, searchCuratedInventory, curated_ingredients_match_all, page = 1, sort_by }) {
    return this.fetch(`/api/recipes/searchFiltered/?page=${page}`, {
      body: JSON.stringify({
        title,
        ingredients,
        searchInventory,
        searchFavorite,
        searchMyRecipes,
        curated_ingredients,
        searchCuratedInventory,
        curated_ingredients_match_all,
        sort_by,
      })
    })
  }

  async updateFavoriteRecipe({id}) {
    return this.fetch('/api/recipes/createFavorite/', {
      body: JSON.stringify({
        recipeID: id
      })
    })
  }

  async getCustomRecipe() {
    return this.fetch('/api/user_recipes/');
  }

  async updateCustomRecipe({id, ingredients, instructions}) {
    return this.fetch(`api/user_recipe_update/${id}/`, {
      body: JSON.stringify({
        ingredients,
        instructions
      })
    })
  }

  async recipeHistory() {
    return this.fetch('/api/recipe_history/')
  }

  async recipeHistoryCreateMeal({ recipe_id }) {
    return this.fetch(`/api/recipe_history/${recipe_id}/meal/`)
  }

  async UserInventory() {
    return this.fetch('/api/user_inventory/')
  }

  async UserInventoryDeleteEntry({ inventory_id }) {
    return this.fetch(`/api/user_inventory/${inventory_id}/`,
      { method: `DELETE` }
    )
  }

  async UserInventoryAddEntry({ ingredient_ids }) {
    return this.fetch(`/api/user_inventory/`, {
      body: JSON.stringify({ ingredient_ids })
    })
  }

  async UserCuratedInventory() {
    return this.fetch('/api/user_curated_inventory/')
  }

  async UserCuratedInventoryDeleteEntry({ inventory_id }) {
    return this.fetch(`/api/user_curated_inventory/${inventory_id}/`,
      { method: `DELETE` }
    )
  }

  async UserCuratedInventoryAddEntry({ curated_ingredient_ids }) {
    return this.fetch(`/api/user_curated_inventory/`, {
      body: JSON.stringify({ curated_ingredient_ids })
    })
  }

  async UserNutritionLastDay() {
    return this.fetch('/api/nutrition/nutrition_last_day/')
  }

  async UserCaloriesLastWeek() {
    return this.fetch('/api/nutrition/calories_last_week/')
  }

  async getSettingsRestrictedIngredients({ page = 1, search } = {}, options) {
    const url = new URL('/api/settings/restricted_ingredients/', window.location.href)
    if (page) url.searchParams.set('page', page)
    if (search) url.searchParams.set('search', search)
    return this.fetch(url.toString(), options)
  }

  async postSettingsRestrictedIngredients({ ingredient_ids } = {}) {
    return this.fetch('/api/settings/restricted_ingredients/', {
      body: JSON.stringify({ ingredient_ids }),
    })
  }

  async getRecipeDetail({ id }) {
    return this.fetch(`/api/recipes/${id}/`)
  }

  async getTags() {
    return this.fetch(`/api/tags/`)
  }

  async deleteTag({ id }) {
    return this.fetch(`/api/tags/${id}/`, { method: 'DELETE' })
  }

  async createTag({ name }) {
    return this.fetch(`/api/tags/`, {
      body: JSON.stringify({ name })
    })
  }

  // Nutritionist chat
  async getConversation() {
    return this.fetch(`/api/nutritionist/conversation/`, {
      method: 'GET',
    })
  }

  async nutritionistChat({ message }) {
    return this.fetch(`/api/nutritionist/conversation/`, {
      body: JSON.stringify({ message }),
    })
  }

  async clearConversation() {
    return this.fetch(`/api/nutritionist/conversation/clear/`, {
      body: JSON.stringify({}),
    })
  }

  async getInProgressRecipe() {
    return this.fetch(`/api/nutritionist/recipe/`, {
      method: 'GET',
    })
  }

  async saveInProgressRecipe() {
    return this.fetch(`/api/nutritionist/recipe/save/`, {
      body: JSON.stringify({}),
    })
  }

  async discardInProgressRecipe() {
    return this.fetch(`/api/nutritionist/recipe/discard/`, {
      body: JSON.stringify({}),
    })
  }

  // Meal plans
  async getMealPlans() {
    return this.fetch('/api/meal_plans/')
  }

  async createMealPlan({ week_start }) {
    return this.fetch('/api/meal_plans/', {
      body: JSON.stringify({ week_start })
    })
  }

  async getMealPlan({ id }) {
    return this.fetch(`/api/meal_plans/${id}/`)
  }

  async addMealPlanEntry({ meal_plan_id, day_of_week, meal_index, recipe_id }) {
    return this.fetch(`/api/meal_plans/${meal_plan_id}/entries/`, {
      body: JSON.stringify({ day_of_week, meal_index, recipe_id })
    })
  }

  async deleteMealPlanEntry({ meal_plan_id, entry_id }) {
    return this.fetch(`/api/meal_plans/${meal_plan_id}/entries/${entry_id}/`, {
      method: 'DELETE',
    })
  }

  // SousChef AI chat
  async getSousChefConversation() {
    return this.fetch(`/api/souschef/conversation/`, {
      method: 'GET',
    })
  }

  async sousChefChat({ message, recipe_id }) {
    return this.fetch(`/api/souschef/conversation/`, {
      body: JSON.stringify({ message, recipe_id }),
    })
  }

  async clearSousChefConversation() {
    return this.fetch(`/api/souschef/conversation/clear/`, {
      body: JSON.stringify({}),
    })
  }

  async startCookingSession({ recipe_id }) {
    return this.fetch(`/api/cooking_session/start/`, {
      body: JSON.stringify({ recipe_id }),
    })
  }

  async endCookingSession({ recipe_id }) {
    return this.fetch(`/api/cooking_session/end/`, {
      body: JSON.stringify({ recipe_id }),
    })
  }

  async getCookingSession({ recipe_id }) {
    return this.fetch(`/api/cooking_session/?recipe_id=${recipe_id}`, {
      method: 'GET',
    })
  }

  async getCookingSessionHistory() {
    return this.fetch(`/api/cooking_session/history/`, {
      method: 'GET',
    })
  }

  async clearCookingSessionHistory() {
    return this.fetch(`/api/cooking_session/history/`, {
      method: 'DELETE',
    })
  }
}

export function ApiProvider(props) {
  const api = useMemo(() => new Api(), []);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    console.log('ready effect triggered')
    if (!api.isReady()) {
      console.log('becoming ready')
      api.becomeReady().then(() => { setIsReady(true) });
    }
  })

  const context = useMemo(() => {
    return { api, isReady };
  }, [isReady, api]);

  return (
    <ApiContext value={context}>
      {props.children}
    </ApiContext>
  )
}

export function useApi() {
  return useContext(ApiContext);
}
