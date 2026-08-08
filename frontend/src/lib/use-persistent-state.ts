import { useCallback, useEffect, useState } from "react"

export function usePersistentState<T>(key: string, fallback: T) {
  const [value, setValue] = useState<T>(() => {
    if (typeof window === "undefined") return fallback
    try {
      const stored = window.localStorage.getItem(key)
      return stored === null ? fallback : (JSON.parse(stored) as T)
    } catch {
      return fallback
    }
  })

  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(value))
    } catch {
      // Storage can be unavailable (private mode, quota); state still works.
    }
  }, [key, value])

  const reset = useCallback(() => setValue(fallback), [fallback])

  return [value, setValue, reset] as const
}
