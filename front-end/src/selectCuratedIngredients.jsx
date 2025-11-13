import Select from 'react-select'
import { useApi } from './useApi'
import { useState, useEffect, useMemo, forwardRef, useImperativeHandle } from 'react'

const SelectCuratedIngredients = forwardRef(function SeletCuratedIngredient(props, ref) {
  const { excludeInventory = true, ...selectProps } = props
  const { api } = useApi()
  const [options, setOptions] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [value, setValue] = useState([])
  const [search, setSearch] = useState('')

  useEffect(() => {
    setOptions([])
    setPage(0)
  }, [search, excludeInventory])

  useEffect(() => {
    if (page === 0) {
      setPage(1)
      return;
    }

    const abortController = new AbortController()

    const timeoutId = setTimeout(async () => {
      setIsLoading(true)
      try {
        const response = await api.listCuratedIngredients(
          { page, search, exclude_inventory: excludeInventory },
          { signal: abortController.signal },
        )

        const nextOptions = response.results.map(ingredient => ({
          value: ingredient.id,
          label: ingredient.display_name,
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
  }, [page, search, excludeInventory, api])

  function onMenuScrollToBottom() {
    setPage(page => page + 1)
  }

  useImperativeHandle(ref, () => ({
    updateInventory: async () => {
      setIsLoading(true)
      try {
        const curated_ingredient_ids = value.map(val => val.value)
        await api.UserCuratedInventoryAddEntry({ curated_ingredient_ids })
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
      {...selectProps}
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

export default SelectCuratedIngredients
