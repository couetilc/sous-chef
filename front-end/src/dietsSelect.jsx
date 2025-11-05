import Select from 'react-select'
import { useApi } from './useApi'
import { useState, useEffect } from 'react'

export default function DietsSelect(props) {
  const { api } = useApi()
  const [options, setOptions] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    api.listDiets().then(response => {
      setOptions(
        response.map(({ id, name }) => ({
          value: id,
          label: name,
        }))
      )
      setIsLoading(false)
    })
  }, [])

  return (
    <Select
      {...props}
      options={options}
      isLoading={isLoading}
    />
  )
}
