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
      },
      error: {
        main: tokens.colors.error,
      },
      background: {
        default: tokens.colors.background,
        paper: tokens.colors.surface,
      },
      text: {
        primary: tokens.colors.onSurface,
        secondary: tokens.colors.onSurfaceVariant,
      },
      divider: tokens.colors.outlineVariant || tokens.colors.outline,
    },
    typography: {
      fontFamily: tokens.typography.fontFamily,
      h1: { fontWeight: 700 },
      h2: { fontWeight: 600 },
      h3: { fontWeight: 600 },
      button: { textTransform: 'none', fontWeight: 600 },
    },
    shape: {
      borderRadius: parseInt(common.rounded.default.replace('rem', '')) * 16, // Default (matches common.rounded.default)
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: common.rounded.full,
            padding: '10px 24px',
            boxShadow: 'none',
            '&:hover': {
              boxShadow: 'none',
            },
          },
          containedPrimary: {
            backgroundColor: tokens.colors.primary,
            color: tokens.colors.onPrimary,
            '&:hover': {
              backgroundColor: alpha(tokens.colors.primary, 0.9),
            },
          },
          outlined: {
            borderColor: tokens.colors.outline,
            '&:hover': {
              backgroundColor: alpha(tokens.colors.primary, 0.04),
              borderColor: tokens.colors.primary,
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            borderRadius: common.rounded.lg, // 32px
            border: `1px solid ${alpha(tokens.colors.outline, 0.1)}`,
            boxShadow: 'none',
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: common.rounded.lg, // 32px
            boxShadow: 'none',
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              borderRadius: common.rounded.default, // 16px
            },
          },
        },
      },
    },
  };

  return createTheme(themeOptions);
};
