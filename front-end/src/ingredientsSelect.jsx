import Select from 'react-select'
import { useApi } from './useApi'
import { useState, useEffect, useMemo } from 'react'

export default function IngredientsSelect(props) {
  const { api } = useApi()
  const [options, setOptions] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [page, setPage] = useState(1)

  useEffect(() => {
    api.listIngredients({ page }).then(response => {
      const nextOptions = response.results.map(ingredient => ({
        value: ingredient.id,
        label: ingredient.name,
      }))
      setOptions(options => options.concat(nextOptions))
      setIsLoading(false)
    })
  }, [page])

  function onMenuScrollToBottom() {
    setPage(page => page + 1)
  }

  return (
    <Select
      {...props}
      options={options}
      isLoading={isLoading}
      onMenuScrollToBottom={onMenuScrollToBottom}
    />
  )
}
