import React from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Button, 
  Card, 
  CardContent, 
  Grid, 
  IconButton, 
  Stack,
  TextField,
  Chip,
  alpha
} from '@mui/material';
import { 
  Sun, 
  Moon, 
  Layout, 
  Palette, 
  Type, 
  Box as BoxIcon,
  Github,
  Twitter,
  Linkedin
} from 'lucide-react';
import { useThemeMode } from './components/ThemeProvider';
import { motion } from 'framer-motion';
import GoogleLoader from './components/GoogleLoader';
import GoogleSpinner from './components/GoogleSpinner';

const App: React.FC = () => {
  const { mode, toggleTheme } = useThemeMode();

  return (
    <Box sx={{ minHeight: '100vh', py: 8 }}>
      <Container maxWidth="lg">
        {/* Header */}
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 8 }}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
              Daffodil Design System
            </Typography>
            <Typography variant="body1" color="text.secondary">
              A high-fidelity, dynamic setup with MUI and Tailwind CSS.
            </Typography>
          </Box>
          <IconButton 
            onClick={toggleTheme} 
            sx={{ 
              p: 2, 
              bgcolor: 'surface.bright',
              '&:hover': { bgcolor: 'surface.containerHighest' }
            }}
          >
            {mode === 'dark' ? <Sun size={24} /> : <Moon size={24} />}
          </IconButton>
        </Stack>

        <Grid container spacing={4}>
          {/* Colors Section */}
          <Grid item xs={12} md={6}>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
            >
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
                    <Palette size={24} className="text-primary" />
                    <Typography variant="h5">Dynamic Palette</Typography>
                  </Stack>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
                    Colors are derived from the central design tokens and applied via CSS variables.
                  </Typography>
                  <Stack spacing={2}>
                    <Box className="p-4 rounded-default bg-primary text-on-primary font-bold">
                      Primary Brand Color
                    </Box>
                    <Box 
                      sx={{ 
                        p: 4, 
                        borderRadius: 'var(--rounded-default)', 
                        bgcolor: 'background.paper', 
                        border: 1, 
                        borderColor: (theme) => alpha(theme.palette.divider, 0.1),
                        color: 'text.primary'
                      }}
                    >
                      Surface Layer
                    </Box>
                    <Box className="p-4 rounded-default bg-secondary text-white font-bold">
                      Secondary Accent
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>

          {/* Typography Section */}
          <Grid item xs={12} md={6}>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
                    <Type size={24} className="text-primary" />
                    <Typography variant="h5">Typography</Typography>
                  </Stack>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
                    Switching themes changes the entire font family (Hanken Grotesk vs Roboto Flex).
                  </Typography>
                  <Box className="space-y-4">
                    <Typography variant="h1" sx={{ fontSize: '3rem' }}>Heading 1</Typography>
                    <Typography variant="h4">Subheading</Typography>
                    <Typography variant="body1">
                      The quick brown fox jumps over the lazy dog.
                    </Typography>
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        fontFamily: 'var(--font-mono)',
                        color: 'primary.main',
                        bgcolor: (theme) => alpha(theme.palette.primary.main, 0.1),
                        px: 1,
                        py: 0.5,
                        borderRadius: 'var(--rounded-sm)'
                      }}
                    >
                      JetBrains Mono for technical data
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>

          {/* Components Section */}
          <Grid item xs={12}>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <Card>
                <CardContent>
                  <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
                    <Layout size={24} className="text-primary" />
                    <Typography variant="h5">Interactive Components</Typography>
                  </Stack>
                  <Grid container spacing={4}>
                    <Grid item xs={12} md={4}>
                      <Typography variant="subtitle2" gutterBottom>Buttons</Typography>
                      <Stack spacing={2}>
                        <Button variant="contained">Primary Action</Button>
                        <Button variant="outlined">Secondary Action</Button>
                        <Button variant="text">Tertiary Action</Button>
                      </Stack>
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <Typography variant="subtitle2" gutterBottom>Inputs</Typography>
                      <Stack spacing={2}>
                        <TextField fullWidth label="Full Name" variant="outlined" placeholder="Enter your name" />
                        <TextField fullWidth label="Password" type="password" variant="outlined" />
                      </Stack>
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <Typography variant="subtitle2" gutterBottom>Rounding & Shapes</Typography>
                      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                        <Chip label="Pill-shaped" />
                        <Chip label="Category" variant="outlined" />
                        <Box 
                          sx={{ 
                            w: 48, 
                            h: 48, 
                            borderRadius: 'var(--rounded-md)', 
                            bgcolor: (theme) => alpha(theme.palette.primary.main, 0.2),
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                          }}
                        >
                          <BoxIcon size={20} className="text-primary" />
                        </Box>
                      </Stack>
                    </Grid>

                    <Grid item xs={12}>
                      <Box sx={{ mt: 4, pt: 4, borderTop: 1, borderColor: 'divider' }}>
                        <Typography variant="subtitle2" gutterBottom align="center">Google Loading States</Typography>
                        <Stack direction="row" spacing={8} justifyContent="center" sx={{ py: 2 }}>
                          <Box sx={{ textAlign: 'center' }}>
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>Dots</Typography>
                            <GoogleLoader />
                          </Box>
                          <Box sx={{ textAlign: 'center' }}>
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>Spinner</Typography>
                            <GoogleSpinner />
                          </Box>
                        </Stack>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>
        </Grid>

        {/* Footer */}
        <Box sx={{ mt: 8, pt: 4, borderTop: 1, borderColor: 'outlineVariant', opacity: 0.6 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="body2">
              © 2026 Daffodil Intelligence. All rights reserved.
            </Typography>
            <Stack direction="row" spacing={2}>
              <IconButton size="small"><Github size={18} /></IconButton>
              <IconButton size="small"><Twitter size={18} /></IconButton>
              <IconButton size="small"><Linkedin size={18} /></IconButton>
            </Stack>
          </Stack>
        </Box>
      </Container>
    </Box>
  );
};

export default App;