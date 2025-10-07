import { createContext, useState, useEffect, useContext } from 'react';

const ApiContext = createContext();

class Api {
  READY_STATES = {
    YES: 0,
    NO: 1,
    PENDING: 2,
  }

  constructor() {
    this.csrfToken = undefined;
    this.ready_state = this.READY_STATES.NO;
    this.promise = new Promise((resolve, reject) => {
      this.resolve = resolve;
      this.reject = reject;
    })
  }

  isReady() {
    return this.ready_state == this.READY_STATES.YES;
  }

  async becomeReady() {
    if (this.ready_state == this.READY_STATES.NO) {
      this.ready_state = this.READY_STATES.PENDING;
      const response = await fetch('/api/csrf/', { credentials: 'include' })
        .then(res => res.json());

      if (response.csrfToken) {
        this.csrfToken = response.csrfToken;
        this.ready_state = this.READY_STATES.YES;
        this.resolve();
      } else {
        this.ready_state = this.READY_STATES.NO;
        this.reject();
      }
    }
  }

  async fetch(resource, options) {
    if (options.body && !options.method) {
      options.method = 'POST'
    }
    return this.promise.then(() => fetch(resource, {
      ...options,
      headers: {
        ...options.headers,
        'Content-Type': 'application/json',
        'X-CSRFToken': this.csrfToken,
      },
      credentials: 'include',
    })).then(res => res.json())
  }

  async login({ username, password }) {
    return this.fetch('http://localhost:3000/api/login/', {
      body: JSON.stringify({ username, password }),
    })
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
