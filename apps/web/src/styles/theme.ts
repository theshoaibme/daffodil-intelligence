import { createTheme, ThemeOptions, alpha } from '@mui/material/styles';
import { designTokens } from './designTokens';

export const getTheme = (mode: 'light' | 'dark') => {
  const tokens = designTokens[mode];
  const common = designTokens.common;

  const themeOptions: ThemeOptions = {
    palette: {
      mode,
      primary: {
        main: tokens.colors.primary,
        contrastText: tokens.colors.onPrimary,
      },
      secondary: {
        main: tokens.colors.secondary,
        contrastText: tokens.colors.onSecondary,
      },
      error: {
        main: tokens.colors.error,
        contrastText: tokens.colors.onError,
      },
      background: {
        default: tokens.colors.background,
        paper: tokens.colors.surface,
      },
      text: {
        primary: tokens.colors.onSurface,
        secondary: tokens.colors.onSurfaceVariant,
      },
      divider: 'transparent', // NO BORDERS RULE
    },
    typography: {
      fontFamily: tokens.typography.fontFamily,
      h1: { fontWeight: 700 },
      h2: { fontWeight: 600 },
      h3: { fontWeight: 600 },
      button: { textTransform: 'none', fontWeight: 600 },
    },
    shape: {
      borderRadius: parseInt(common.rounded.default.replace('px', '')) || 16,
    },
    transitions: {
      create: () => 'none !important',
      duration: {
        shortest: 0,
        shorter: 0,
        short: 0,
        standard: 0,
        complex: 0,
        enteringScreen: 0,
        leavingScreen: 0,
      },
    },
    components: {
      MuiButtonBase: {
        defaultProps: {
          disableRipple: true,
        },
      },
      MuiButton: {
        defaultProps: {
          disableElevation: true,
          disableRipple: true,
        },
        styleOverrides: {
          root: {
            borderRadius: common.rounded.full,
            padding: '10px 24px',
            boxShadow: 'none !important',
            border: 'none !important',
            textTransform: 'none',
            transition: 'none !important',
            '&:hover': {
              boxShadow: 'none !important',
              border: 'none !important',
            },
          },
          containedPrimary: {
            backgroundColor: tokens.colors.primary,
            color: tokens.colors.onPrimary,
            '&:hover': {
              backgroundColor: alpha(tokens.colors.primary, 0.8),
            },
          },
          outlined: {
            border: 'none !important',
            backgroundColor: mode === 'light' ? '#f4f2ff' : '#201f1f',
            '&:hover': {
              backgroundColor: alpha(tokens.colors.primary, 0.1),
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            borderRadius: common.rounded.lg,
            border: 'none !important',
            boxShadow: 'none !important',
            transition: 'none !important',
            backgroundColor: tokens.colors.surfaceContainer,
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: common.rounded.lg,
            border: 'none !important',
            boxShadow: 'none !important',
            transition: 'none !important',
            backgroundColor: tokens.colors.surfaceContainer,
          },
        },
      },
      MuiTextField: {
        defaultProps: {
          InputLabelProps: {
            shrink: true, // Google/Shadcn style: force label above
          },
        },
        styleOverrides: {
          root: {
            border: 'none !important',
            '& .MuiInputLabel-root': {
              position: 'relative',
              transform: 'none !important',
              fontSize: '14px',
              fontWeight: 500,
              marginBottom: '6px',
              color: `${tokens.colors.onSurface} !important`,
              transition: 'none !important',
            },
            '& .MuiOutlinedInput-root': {
              height: 40,
              fontSize: '14px',
              borderRadius: common.rounded.full, // Styled with Google's iconic 100% pill-shaped rounding
              backgroundColor: mode === 'light' ? '#f4f2ff' : '#141313', // Harmonized neutral backgrounds
              border: 'none !important',
              transition: 'none !important',
              paddingLeft: '16px',
              paddingRight: '16px',
              '& fieldset': {
                border: 'none !important',
              },
              '&:hover fieldset': {
                border: 'none !important',
              },
              '&.Mui-focused fieldset': {
                border: 'none !important',
              },
              '&.Mui-focused': {
                backgroundColor: mode === 'light' ? '#f4f2ff' : '#141313',
              },
              '& input': {
                padding: '8px 0px',
                height: 'auto',
                color: tokens.colors.onSurface,
                '&::placeholder': {
                  color: tokens.colors.onSurfaceVariant,
                  opacity: 0.5,
                },
              },
            },
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: common.rounded.full,
            border: 'none !important',
            transition: 'none !important',
            backgroundColor: tokens.colors.surfaceContainerHighest,
          },
        },
      },
      MuiList: {
        styleOverrides: {
          root: {
            padding: 0,
            border: 'none !important',
          },
        },
      },
      MuiListItem: {
        styleOverrides: {
          root: {
            border: 'none !important',
            transition: 'none !important',
          },
        },
      },
      MuiDialog: {
        styleOverrides: {
          paper: {
            border: 'none !important',
            boxShadow: 'none !important',
            borderRadius: common.rounded.lg,
            transition: 'none !important',
          },
        },
      },
    },
  };

  return createTheme(themeOptions);
};
