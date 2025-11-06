import Select from 'react-select'
import { useApi } from './useApi'
import { useState, useEffect, useMemo, forwardRef, useImperativeHandle } from 'react'

const SelectRestrictedIngredients = forwardRef((props, ref) => {
  const { api } = useApi()
  const [options, setOptions] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [value, setValue] = useState([])
  const [search, setSearch] = useState('')

  useEffect(() => {
    if (page === 0) {
      setPage(1)
      return;
    }

    const abortController = new AbortController()

    const timeoutId = setTimeout(async () => {
      setIsLoading(true)
      try {
        const response = await api.getSettingsRestrictedIngredients(
          { page, search },
          { signal: abortController.signal },
        )
        const restricted = response.results
          .filter(ingredient => ingredient.is_restricted)
          .map(ingredient => ({
            value: ingredient.id,
            label: ingredient.name,
          }))

        if (restricted.length > 0) {
          setValue(values => values.concat(restricted))
        }

        const nextOptions = response.results.map(ingredient => ({
          value: ingredient.id,
          label: ingredient.name,
        }))

        setOptions(options => options.concat(nextOptions))
      }
      finally {
        setIsLoading(false)
      }
    }, 500)

    return () => {
      clearTimeout(timeoutId)
      abortController.abort()
    }
  }, [page, search])

  function onMenuScrollToBottom() {
    setPage(page => page + 1)
  }

  useImperativeHandle(ref, () => ({
    updateIngredients: async () => {
      setIsLoading(true)
      try {
        const ingredient_ids = value.map(val => val.value)
        await api.postSettingsRestrictedIngredients({ ingredient_ids })
        setOptions([])
        setValue([])
        setPage(0) // triggers refresh of data
      }
      finally {
        setIsLoading(false)
      }
    },
  }))

  // I want an api that returns:
  // {
  //   "ingredients": [{
  //     ...
  //     "is_restricted": true|false,
  //   }],
  // }
  //
  // backend logic:
  // - always return ingredients that have been restricted.
  // - otherwise, return ingredients according to the page requested
  //   - and according to a "?search=<name>" parameter
  //
  // frontend logic:
  // - call GET "/api/settings/restricted_ingredients/"
  // - map over response
  //   - sort "is_restricted" true into pre-selected values
  //   - put the rest as options
  // - on user typing
  //   - call GET "/api/settings/restricted_ingredients/?search=<name>&page=1"
  //   - delay the call until user stops typing for 500ms
  //   - if the user types again, abort any in-flight calls.
  //   - "page" state gets reset to 1 if they type.
  // - on user submission (button press)
  //   - POST "/api/settings/restricted_ingredients/" with {"ingredient_ids":[...]}
  //   - backend will perform a sync operation, similar to diet

  return (
    <Select
      {...props}
      isMulti
      value={value}
      inputValue={search}
      options={options}
      isLoading={isLoading}
      onMenuScrollToBottom={onMenuScrollToBottom}
      onChange={value => setValue(value)}
      onInputChange={input => setSearch(input)}
    />
  )
})

export default SelectRestrictedIngredients
