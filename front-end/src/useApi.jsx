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
      const data = await res.json();
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
    return this.fetch('/api/register/', {
      body: JSON.stringify({
        username,
        email,
        password,
        password_confirm,
        first_name,
        last_name
      }),
    })
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

  async listCuratedIngredients({ page = 1, search } = {}, options) {
    const url = new URL('/api/curated_ingredients/', window.location.href)
    if (page) url.searchParams.set('page', page)
    if (search) url.searchParams.set('search', search)
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

  async getRecipesFiltered({title, ingredients, searchInventory, searchFavorite, page = 1}) {
    return this.fetch(`/api/recipes/searchFiltered/?page=${page}`, {
      body: JSON.stringify({
        title,
        ingredients,
        searchInventory,
        searchFavorite
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
