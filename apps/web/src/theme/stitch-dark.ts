import { createTheme } from '@mui/material/styles';

export const stitchDarkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#8ab4f8',
      light: '#d5e3ff',
      dark: '#315f9d',
      contrastText: '#131314',
    },
    secondary: {
      main: '#c5c7c5',
      light: '#e1e3e1',
      dark: '#444746',
      contrastText: '#e5e2e3',
    },
    error: {
      main: '#ffb4ab',
      light: '#ffdad6',
      dark: '#93000a',
    },
    warning: {
      main: '#f9e596',
    },
    info: {
      main: '#a8c8ff',
    },
    success: {
      main: '#9ef2c2',
    },
    background: {
      default: '#131314',
      paper: '#191A1F',
    },
    text: {
      primary: '#e5e2e3',
      secondary: '#c3c6d1',
    },
    divider: '#444746',
  },
  typography: {
    fontFamily: '"Roboto Flex", "Roboto", sans-serif',
  },
  shape: {
    borderRadius: 28,
  },
  spacing: 8,
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#131314',
          color: '#e5e2e3',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '16px',
          textTransform: 'none' as const,
          fontWeight: 500,
          padding: '10px 24px',
        },
        contained: {
          backgroundColor: '#8ab4f8',
          color: '#131314',
          boxShadow: 'none',
          '&:hover': {
            backgroundColor: '#a8c8ff',
          },
        },
        outlined: {
          borderColor: '#444746',
          color: '#e5e2e3',
          '&:hover': {
            backgroundColor: 'rgba(138, 180, 248, 0.08)',
            borderColor: '#8ab4f8',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: '16px',
            backgroundColor: 'transparent',
            '& fieldset': {
              borderColor: '#444746',
              borderWidth: '1px',
            },
            '&:hover fieldset': {
              borderColor: '#8d919b',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#8ab4f8',
              borderWidth: '2px',
            },
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: '#191A1F',
          border: '1px solid #444746',
          borderRadius: '32px',
          boxShadow: 'none',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: '#191A1F',
          backgroundImage: 'none',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: '16px',
          '&.Mui-selected': {
            backgroundColor: 'rgba(138, 180, 248, 0.12)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '9999px',
          border: '1px solid #444746',
        },
        filled: {
          backgroundColor: 'rgba(138, 180, 248, 0.12)',
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          backgroundColor: '#191A1F',
          border: '1px solid #444746',
          borderRadius: '32px',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#191A1F',
          borderRight: '1px solid #444746',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#191A1F',
          borderBottom: '1px solid #444746',
          boxShadow: 'none',
        },
      },
    },
  },
});

export const colors = {
  surface: '#131314',
  surfaceDim: '#131314',
  surfaceBright: '#39393a',
  surfaceContainerLowest: '#0e0e0f',
  surfaceContainerLow: '#1c1b1c',
  surfaceContainer: '#201f20',
  surfaceContainerHigh: '#2a2a2b',
  surfaceContainerHighest: '#353436',
  onSurface: '#e5e2e3',
  onSurfaceVariant: '#c3c6d1',
  inverseSurface: '#e5e2e3',
  inverseOnSurface: '#313031',
  outline: '#8d919b',
  outlineVariant: '#424750',
  surfaceTint: '#a8c8ff',
  primary: '#b5cfff',
  onPrimary: '#003061',
  primaryContainer: '#8ab4f8',
  onPrimaryContainer: '#0d4582',
  inversePrimary: '#315f9d',
  secondary: '#c5c7c5',
  onSecondary: '#2e3130',
  secondaryContainer: '#444746',
  onSecondaryContainer: '#b3b6b4',
  tertiary: '#cfcdd4',
  onTertiary: '#2f3035',
  tertiaryContainer: '#b3b2b9',
  onTertiaryContainer: '#44454a',
  error: '#ffb4ab',
  onError: '#690005',
  errorContainer: '#93000a',
  onErrorContainer: '#ffdad6',
  primaryFixed: '#d5e3ff',
  primaryFixedDim: '#a8c8ff',
  onPrimaryFixed: '#001b3c',
  onPrimaryFixedVariant: '#114784',
  secondaryFixed: '#e1e3e1',
  secondaryFixedDim: '#c5c7c5',
  onSecondaryFixed: '#191c1b',
  onSecondaryFixedVariant: '#444746',
  tertiaryFixed: '#e3e2e9',
  tertiaryFixedDim: '#c7c6cd',
  onTertiaryFixed: '#1a1b20',
  onTertiaryFixedVariant: '#46464c',
  background: '#131314',
  onBackground: '#e5e2e3',
  surfaceVariant: '#353436',
};