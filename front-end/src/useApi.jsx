import { createContext, useState, useEffect, useContext } from 'react';

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

  async fetch(resource, options) {
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

  async listIngredients() {
    return this.fetch('/api/ingredients/', {});
  }
}



const createApi = () => new Api();

export function ApiProvider(props) {
  const [context, setContext] = useState(createApi);

  useEffect(() => {
    if (!context.isReady()) {
      context.becomeReady();
    }
  })

  return (
    <ApiContext value={context}>
      {props.children}
    </ApiContext>
  )
}

export function useApi() {
  return useContext(ApiContext);
}
