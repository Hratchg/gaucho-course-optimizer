import { useEffect, useState } from 'react'

export function useColdStartMessage(isLoading: boolean): boolean {
  const [thresholdReached, setThresholdReached] = useState(false)

  useEffect(() => {
    if (!isLoading) {
      setThresholdReached(false)
      return
    }

    const timer = setTimeout(() => {
      setThresholdReached(true)
    }, 3000)

    return () => {
      clearTimeout(timer)
    }
  }, [isLoading])

  return thresholdReached
}
