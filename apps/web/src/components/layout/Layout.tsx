import { ReactNode, useState } from 'react'
import { Box, AppBar, Toolbar, Typography, Drawer, List, ListItem, ListItemIcon, ListItemText, IconButton, Avatar, Menu, MenuItem, ListItemButton } from '@mui/material'
import { Dashboard, Chat, Psychology, AdminPanelSettings, Videocam, Menu as MenuIcon, Logout, School, LocalLibrary, DirectionsBus, Home, Event, Notifications, AttachMoney, Campaign, CameraAlt } from '@mui/icons-material'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store'

const drawerWidth = 260

const colors = {
  surface: '#131314',
  surfaceContainer: '#201f20',
  surfaceContainerHigh: '#2a2a2b',
  surfaceContainerHighest: '#353436',
  onSurface: '#e5e2e3',
  onSurfaceVariant: '#c3c6d1',
  outline: '#8d919b',
  outlineVariant: '#424750',
  primary: '#8ab4f8',
  primaryContainer: '#8ab4f8',
  secondary: '#c5c7c5',
}

const navItems = [
  { text: 'Dashboard', icon: <Dashboard />, path: '/dashboard' },
  { text: 'Chat', icon: <Chat />, path: '/chat' },
  { text: 'Agents', icon: <Psychology />, path: '/agents' },
  { text: 'Vision (Camera)', icon: <CameraAlt />, path: '/vision' },
  { text: 'Live Voice', icon: <Videocam />, path: '/live' },
  { text: 'Admin', icon: <AdminPanelSettings />, path: '/admin' },
]

const agentQuickAccess = [
  { text: 'Academic', icon: <School />, path: '/chat?agent=academic', emoji: '📚' },
  { text: 'Library', icon: <LocalLibrary />, path: '/chat?agent=library', emoji: '📖' },
  { text: 'Transport', icon: <DirectionsBus />, path: '/chat?agent=transport', emoji: '🚌' },
  { text: 'Hostel', icon: <Home />, path: '/chat?agent=hostel', emoji: '🏠' },
  { text: 'Events', icon: <Event />, path: '/chat?agent=event', emoji: '🎉' },
  { text: 'Exam', icon: <School />, path: '/chat?agent=exam', emoji: '📅' },
  { text: 'Fee', icon: <AttachMoney />, path: '/chat?agent=fee', emoji: '💰' },
  { text: 'Career', icon: <Campaign />, path: '/chat?agent=career', emoji: '💼' },
  { text: 'Complaint', icon: <Campaign />, path: '/chat?agent=complaint', emoji: '📝' },
  { text: 'Notifications', icon: <Notifications />, path: '/chat?agent=notification', emoji: '🔔' },
]

export default function Layout({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const handleDrawerToggle = () => setMobileOpen(!mobileOpen)
  const handleProfileClick = (e: React.MouseEvent<HTMLElement>) => setAnchorEl(e.currentTarget)
  const handleClose = () => setAnchorEl(null)
  const handleLogout = () => { logout(); navigate('/') }

  const isSelected = (path: string) => location.pathname === path

  const drawer = (
    <Box sx={{ p: 2 }}>
      <Typography sx={{ 
        mb: 3, 
        fontWeight: 500, 
        color: colors.primary, 
        display: 'flex', 
        alignItems: 'center', 
        gap: 1,
        fontSize: '18px',
        fontFamily: '"Roboto Flex", Roboto, sans-serif'
      }}>
        Daffodil Intelligence
      </Typography>
      <List>
        {navItems.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              onClick={() => navigate(item.path)}
              sx={{
                borderRadius: '28px',
                bgcolor: isSelected(item.path) ? 'rgba(138, 180, 248, 0.12)' : 'transparent',
                '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.04)' }
              }}
            >
              <ListItemIcon sx={{ color: isSelected(item.path) ? colors.primary : colors.onSurfaceVariant, minWidth: 40 }}>{item.icon}</ListItemIcon>
              <ListItemText 
                primary={item.text} 
                sx={{ 
                  color: isSelected(item.path) ? colors.primary : colors.onSurface,
                  fontFamily: '"Roboto Flex", Roboto, sans-serif',
                  fontSize: '14px',
                  fontWeight: isSelected(item.path) ? 500 : 400
                }} 
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      
      <Typography sx={{ 
        mt: 3, 
        mb: 2, 
        color: colors.onSurfaceVariant, 
        px: 1,
        fontSize: '12px',
        fontWeight: 500,
        fontFamily: '"Roboto Flex", Roboto, sans-serif'
      }}>
        Quick Agent Access
      </Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, px: 1 }}>
        {agentQuickAccess.map((agent) => (
          <ListItemButton
            key={agent.text}
            onClick={() => navigate(agent.path)}
            sx={{
              borderRadius: '28px',
              bgcolor: 'rgba(255, 255, 255, 0.04)',
              flexBasis: '45%',
              py: 1,
              px: 1.5,
              '&:hover': { bgcolor: 'rgba(138, 180, 248, 0.08)' }
            }}
          >
            <ListItemIcon sx={{ minWidth: 30, fontSize: '1.2rem' }}>{agent.emoji}</ListItemIcon>
            <ListItemText 
              primary={agent.text} 
              primaryTypographyProps={{ 
                sx: { 
                  fontSize: '12px', 
                  fontWeight: 500,
                  color: colors.onSurface,
                  fontFamily: '"Roboto Flex", Roboto, sans-serif'
                }
              }} 
            />
          </ListItemButton>
        ))}
      </Box>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: colors.surface }}>
      <AppBar position="fixed" sx={{ 
        zIndex: (theme) => theme.zIndex.drawer + 1, 
        bgcolor: '#191A1F', 
        borderBottom: '1px solid #444746',
        boxShadow: 'none'
      }}>
        <Toolbar>
          <IconButton 
            color="inherit" 
            edge="start" 
            onClick={handleDrawerToggle} 
            sx={{ mr: 2, display: { sm: 'none' }, color: colors.onSurface }}
          >
            <MenuIcon />
          </IconButton>
          <Typography sx={{ 
            flexGrow: 1, 
            color: colors.onSurface,
            fontSize: '18px',
            fontWeight: 500,
            fontFamily: '"Roboto Flex", Roboto, sans-serif'
          }}>
            Daffodil Intelligence
          </Typography>
          <IconButton onClick={handleProfileClick} sx={{ color: colors.onSurface }}>
            <Avatar sx={{ bgcolor: colors.primary, color: '#131314' }}>{user?.full_name?.[0] || 'U'}</Avatar>
          </IconButton>
          <Menu 
            anchorEl={anchorEl} 
            open={Boolean(anchorEl)} 
            onClose={handleClose}
            sx={{
              '& .MuiPaper-root': {
                bgcolor: '#191A1F',
                border: '1px solid #444746',
                borderRadius: '28px',
              }
            }}
          >
            <MenuItem sx={{ color: colors.onSurface }}>{user?.full_name}</MenuItem>
            <MenuItem onClick={handleLogout} sx={{ color: colors.onSurface }}>
              <Logout sx={{ mr: 1 }} />Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      <Box component="nav" sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}>
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{ 
            display: { xs: 'block', sm: 'none' }, 
            '& .MuiDrawer-paper': { 
              width: drawerWidth,
              bgcolor: '#191A1F',
              borderRight: '1px solid #444746'
            } 
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{ 
            display: { xs: 'none', sm: 'block' }, 
            '& .MuiDrawer-paper': { 
              width: drawerWidth, 
              bgcolor: '#191A1F',
              borderRight: '1px solid #444746'
            } 
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8, bgcolor: colors.surface }}>
        {children}
      </Box>
    </Box>
  )
}