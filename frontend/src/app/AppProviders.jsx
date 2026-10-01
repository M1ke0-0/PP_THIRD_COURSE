import { CssBaseline, ThemeProvider } from '@mui/material'

import { theme } from './theme'

export function AppProviders({ children }) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  )
}

