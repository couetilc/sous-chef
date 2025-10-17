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
          this.csrfToken = response.csrfToken;
          this.ready_state = this.READY_STATES.YES;
        } else {
          this.ready_state = this.READY_STATES.NO;
        }
      } catch (error) {
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
    return this.fetch('/api/login/', {
      body: JSON.stringify({ username, password }),
    })
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

  async listIngredients() {
    return this.fetch('/api/ingredients/', {});
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
}

export function ApiProvider(props) {
  const api = useMemo(() => new Api(), []);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    if (!api.isReady()) {
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
