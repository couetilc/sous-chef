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
    setOptions([])
    setPage(0)
  }, [search])

  useEffect(() => {
    if (page === 0) {
      setPage(1)
      return;
    }

    const abortController = new AbortController()

    const timeoutId = setTimeout(async () => {
      setIsLoading(true)
      try {
        const response = await api.listIngredients(
          { page, search },
          { signal: abortController.signal },
        )

        const nextOptions = response.results.map(ingredient => ({
          value: ingredient.id,
          label: ingredient.name,
        }))

        setOptions(options => options.concat(nextOptions))
      }
      catch (error) {
        // ignore
      }
      finally {
        setIsLoading(false)
      }
    }, 500)

    return () => {
      clearTimeout(timeoutId)
      abortController.abort()
    }
  }, [page])

  function onMenuScrollToBottom() {
    setPage(page => page + 1)
  }

  useImperativeHandle(ref, () => ({
    updateInventory: async () => {
      setIsLoading(true)
      try {
        const ingredient_ids = value.map(val => val.value)
        await api.UserInventoryAddEntry({ ingredient_ids })
        setOptions([])
        setValue([])
        setPage(0) // triggers refresh of data
      }
      finally {
        setIsLoading(false)
      }
    },
  }))

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
