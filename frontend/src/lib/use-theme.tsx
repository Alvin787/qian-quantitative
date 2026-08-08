import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"

export type Theme = "light" | "dark"

const THEME_STORAGE_KEY = "qq.theme"

type ThemeContextValue = {
  theme: Theme
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

function systemPrefersDark() {
  return window.matchMedia("(prefers-color-scheme: dark)").matches
}

function readStoredTheme(): Theme | null {
  try {
    const stored = window.localStorage.getItem(THEME_STORAGE_KEY)
    if (stored === null) return null
    const parsed = JSON.parse(stored) as unknown
    return parsed === "dark" || parsed === "light" ? parsed : null
  } catch {
    return null
  }
}

function resolveTheme(stored: Theme | null): Theme {
  return stored ?? (systemPrefersDark() ? "dark" : "light")
}

export function applyThemeClass(theme: Theme) {
  document.documentElement.classList.toggle("dark", theme === "dark")
}

export function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "light"
  return resolveTheme(readStoredTheme())
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => getInitialTheme())
  const [userChosen, setUserChosen] = useState(() => readStoredTheme() !== null)

  useEffect(() => {
    applyThemeClass(theme)
    if (!userChosen) return
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(theme))
    } catch {
      // Storage can be unavailable; theme still applies for this session.
    }
  }, [theme, userChosen])

  useEffect(() => {
    if (userChosen) return

    const media = window.matchMedia("(prefers-color-scheme: dark)")
    const onChange = () => {
      setThemeState(media.matches ? "dark" : "light")
    }

    media.addEventListener("change", onChange)
    return () => media.removeEventListener("change", onChange)
  }, [userChosen])

  const setTheme = useCallback((next: Theme) => {
    setUserChosen(true)
    setThemeState(next)
  }, [])

  const toggleTheme = useCallback(() => {
    setUserChosen(true)
    setThemeState((current) => (current === "dark" ? "light" : "dark"))
  }, [])

  const value = useMemo(
    () => ({ theme, setTheme, toggleTheme }),
    [theme, setTheme, toggleTheme]
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider")
  }
  return context
}
