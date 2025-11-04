import { useApi } from './useApi'
import { useState, useEffect, useMemo } from 'react'

export function useGET(api_endpoint, api_arguments) {
  const { api, isReady } = useApi();
  const [data, setData] = useState({})

  useEffect(() => {
    if (api.ready_state == api.READY_STATES.YES) {
      api[api_endpoint](api_arguments)
        .then(data => setData(data))
    }
  }, [isReady])

  const values = useMemo(() => {
    function refresh() {
      if (api.ready_state == api.READY_STATES.YES) {
        api[api_endpoint](api_arguments)
          .then(data => setData(data))
      }
    }

    return { data, refresh }
  }, [data])
  
  return values
}
