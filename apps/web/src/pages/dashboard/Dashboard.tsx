import { Box, Grid, Card, CardContent, Typography, ListItem, ListItemText, ListItemIcon, Chip, LinearProgress } from '@mui/material'
import { School, LibraryBooks, Work, AttachMoney, CalendarMonth, DirectionsBus, Psychology } from '@mui/icons-material'

const colors = {
  surface: '#131314',
  surfaceContainer: '#201f20',
  surfaceContainerHigh: '#2a2a2b',
  onSurface: '#e5e2e3',
  onSurfaceVariant: '#c3c6d1',
  primary: '#8ab4f8',
}

const stats = [
  { label: 'Current CGPA', value: '3.75', icon: <School />, color: '#8ab4f8' },
  { label: 'Books Borrowed', value: '12', icon: <LibraryBooks />, color: '#ec4899' },
  { label: 'Applications', value: '5', icon: <Work />, color: '#22c55e' },
  { label: 'Pending Dues', value: '৳10,000', icon: <AttachMoney />, color: '#f59e0b' },
]

const notices = [
  { title: 'Midterm Schedule Released', date: '2024-03-15', priority: 'high' },
  { title: 'Library Holiday Notice', date: '2024-03-20', priority: 'medium' },
  { title: 'Career Fair Next Week', date: '2024-03-25', priority: 'low' },
]

const upcoming = [
  { title: 'Algorithm Exam', date: 'Mar 20, 2024', time: '10:00 AM' },
  { title: 'Library Booking', date: 'Mar 18, 2024', time: '2:00 PM' },
  { title: 'Career Workshop', date: 'Mar 22, 2024', time: '3:00 PM' },
]

const agents = [
  { name: 'Academic', icon: <Psychology />, status: 'Active', color: '#8ab4f8' },
  { name: 'Library', icon: <LibraryBooks />, status: 'Ready', color: '#ec4899' },
  { name: 'Career', icon: <Work />, status: 'Ready', color: '#22c55e' },
  { name: 'Campus', icon: <DirectionsBus />, status: 'Ready', color: '#f59e0b' },
]

export default function Dashboard() {
  return (
    <Box>
      <Typography sx={{ 
        mb: 3, 
        fontSize: '28px',
        fontWeight: 500,
        color: colors.onSurface,
        fontFamily: '"Roboto Flex", Roboto, sans-serif'
      }}>
        Dashboard
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        {stats.map((stat, i) => (
          <Grid item xs={12} sm={6} md={3} key={i}>
            <Card sx={{ 
              bgcolor: '#191A1F', 
              border: '1px solid #444746',
              borderRadius: '28px'
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box sx={{ p: 1.5, borderRadius: '16px', bgcolor: `${stat.color}20`, color: stat.color }}>{stat.icon}</Box>
                  <Box>
                    <Typography sx={{ 
                      fontSize: '12px', 
                      color: colors.onSurfaceVariant,
                      fontFamily: '"Roboto Flex", Roboto, sans-serif'
                    }}>
                      {stat.label}
                    </Typography>
                    <Typography sx={{ 
                      fontSize: '22px', 
                      fontWeight: 500,
                      color: colors.onSurface,
                      fontFamily: '"Roboto Flex", Roboto, sans-serif'
                    }}>
                      {stat.value}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card sx={{ 
            bgcolor: '#191A1F', 
            border: '1px solid #444746',
            borderRadius: '28px'
          }}>
            <CardContent>
              <Typography sx={{ 
                mb: 2,
                fontSize: '16px',
                fontWeight: 500,
                color: colors.onSurface,
                fontFamily: '"Roboto Flex", Roboto, sans-serif'
              }}>
                Agent Status
              </Typography>
              {agents.map((a, i) => (
                <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Box sx={{ color: a.color }}>{a.icon}</Box>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography sx={{ 
                      color: colors.onSurface,
                      fontFamily: '"Roboto Flex", Roboto, sans-serif',
                      fontSize: '14px'
                    }}>
                      {a.name}
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={a.status === 'Active' ? 100 : 80} 
                      sx={{ 
                        height: 4, 
                        borderRadius: '16px', 
                        mt: 0.5,
                        bgcolor: 'rgba(255,255,255,0.04)',
                        '& .MuiLinearProgress-bar': { bgcolor: a.color }
                      }} 
                    />
                  </Box>
                  <Chip 
                    label={a.status} 
                    size="small" 
                    sx={{ 
                      bgcolor: `${a.color}20`, 
                      color: a.color,
                      borderRadius: '9999px',
                      fontSize: '11px',
                      fontFamily: '"Roboto Flex", Roboto, sans-serif'
                    }} 
                  />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ 
            bgcolor: '#191A1F', 
            border: '1px solid #444746',
            borderRadius: '28px'
          }}>
            <CardContent>
              <Typography sx={{ 
                mb: 2,
                fontSize: '16px',
                fontWeight: 500,
                color: colors.onSurface,
                fontFamily: '"Roboto Flex", Roboto, sans-serif'
              }}>
                Notices
              </Typography>
              {notices.map((n, i) => (
                <ListItem key={i} sx={{ px: 0 }}>
                  <ListItemIcon>
                    <CalendarMonth sx={{ color: n.priority === 'high' ? '#ef4444' : colors.onSurfaceVariant }} />
                  </ListItemIcon>
                  <ListItemText 
                    primary={n.title} 
                    secondary={n.date}
                    primaryTypographyProps={{
                      sx: { color: colors.onSurface, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '14px' }
                    }}
                    secondaryTypographyProps={{
                      sx: { color: colors.onSurfaceVariant, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '12px' }
                    }}
                  />
                  <Chip 
                    label={n.priority} 
                    size="small" 
                    color={n.priority === 'high' ? 'error' : 'default'}
                    sx={{
                      borderRadius: '9999px',
                      fontSize: '11px',
                      fontFamily: '"Roboto Flex", Roboto, sans-serif',
                      bgcolor: n.priority === 'high' ? 'rgba(255, 180, 171, 0.12)' : 'rgba(255,255,255,0.04)',
                      color: n.priority === 'high' ? '#ffb4ab' : colors.onSurfaceVariant
                    }}
                  />
                </ListItem>
              ))}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ 
            bgcolor: '#191A1F', 
            border: '1px solid #444746',
            borderRadius: '28px'
          }}>
            <CardContent>
              <Typography sx={{ 
                mb: 2,
                fontSize: '16px',
                fontWeight: 500,
                color: colors.onSurface,
                fontFamily: '"Roboto Flex", Roboto, sans-serif'
              }}>
                Upcoming Events
              </Typography>
              {upcoming.map((u, i) => (
                <Box key={i} sx={{ mb: 2, p: 2, borderRadius: '16px', bgcolor: 'rgba(138, 180, 248, 0.08)' }}>
                  <Typography sx={{ 
                    fontWeight: 500,
                    color: colors.onSurface,
                    fontFamily: '"Roboto Flex", Roboto, sans-serif',
                    fontSize: '14px'
                  }}>
                    {u.title}
                  </Typography>
                  <Typography sx={{ 
                    fontSize: '12px',
                    color: colors.onSurfaceVariant,
                    fontFamily: '"Roboto Flex", Roboto, sans-serif'
                  }}>
                    {u.date} at {u.time}
                  </Typography>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}