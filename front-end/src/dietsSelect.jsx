import Select from 'react-select'
import { useApi } from './useApi'
import { useState, useEffect, useRef, useImperativeHandle, forwardRef, useMemo } from 'react'

const DietsSelect = forwardRef((props, ref) => {
  const { api } = useApi()
  const [options, setOptions] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [value, setValue] = useState([])

  const fetchDiets = useMemo(() => {
    return () => {
      api.listDiets().then(response => {
        setOptions(
          response.map(({ id, name }) => ({
            value: id,
            label: name,
          }))
        )
        setValue(
          response
            .filter(diet => diet.is_restricted)
            .map(({ id, name }) => ({
              value: id,
              label: name,
            }))
        )
        setIsLoading(false)
      })
    }
  }, [setOptions, setValue, setIsLoading])

  useImperativeHandle(ref, () => ({
    updateDiets: async () => {
      setIsLoading(true)
      try {
        const diet_ids = value.map(val => val.value)
        await api.syncDiets({ diet_ids })
        await fetchDiets()
      }
      finally {
        setIsLoading(false)
      }
    },
  }))

  useEffect(() => {
    fetchDiets()
  }, [])

  return (
    <Select
      value={value}
      options={options}
      isLoading={isLoading}
      onChange={value => setValue(value)}
      {...props}
    />
  )
})

export default DietsSelect
