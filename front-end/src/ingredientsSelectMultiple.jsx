import Select from 'react-select'

import { useApi } from './useApi'
import { useState, useEffect, useMemo } from 'react'

export default function IngredientsSelectMultiple(props) {
  const { api } = useApi()
  const [options, setOptions] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [page, setPage] = useState(1)

  const [selectedOptions, setSelectedOptions] = useState([])
  const handleChange = (selectedOption) => {
    props.setSelectedOptions(selectedOption)
  }

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
      options={options}
      value={props.selectedOptions}
      isLoading={isLoading}
      onInputChange={props.onInputChange}
      onChange = {handleChange}
      noOptionsMessage={() => "No options found"}
      onMenuScrollToBottom={onMenuScrollToBottom}
      isMulti={true}
    />
  )
}
