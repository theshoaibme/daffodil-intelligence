import { Box, Grid, Card, CardContent, Typography, ListItem, ListItemText, ListItemIcon, Chip, LinearProgress } from '@mui/material'
import { School, LibraryBooks, Work, AttachMoney, CalendarMonth, DirectionsBus, Psychology } from '@mui/icons-material'

const stats = [
  { label: 'Current CGPA', value: '3.75', icon: <School />, color: '#6366f1' },
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
  { name: 'Academic', icon: <Psychology />, status: 'Active', color: '#6366f1' },
  { name: 'Library', icon: <LibraryBooks />, status: 'Ready', color: '#ec4899' },
  { name: 'Career', icon: <Work />, status: 'Ready', color: '#22c55e' },
  { name: 'Campus', icon: <DirectionsBus />, status: 'Ready', color: '#f59e0b' },
]

export default function Dashboard() {
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>Dashboard</Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        {stats.map((stat, i) => (
          <Grid item xs={12} sm={6} md={3} key={i}>
            <Card sx={{ bgcolor: 'background.paper', border: '1px solid #334155' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: `${stat.color}20`, color: stat.color }}>{stat.icon}</Box>
                  <Box>
                    <Typography variant="body2" sx={{ color: '#94a3b8' }}>{stat.label}</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>{stat.value}</Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: 'background.paper', border: '1px solid #334155' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Agent Status</Typography>
              {agents.map((a, i) => (
                <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Box sx={{ color: a.color }}>{a.icon}</Box>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography>{a.name}</Typography>
                    <LinearProgress variant="determinate" value={a.status === 'Active' ? 100 : 80} sx={{ height: 4, borderRadius: 2, mt: 0.5 }} />
                  </Box>
                  <Chip label={a.status} size="small" sx={{ bgcolor: `${a.color}20`, color: a.color }} />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: 'background.paper', border: '1px solid #334155' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Notices</Typography>
              {notices.map((n, i) => (
                <ListItem key={i} sx={{ px: 0 }}>
                  <ListItemIcon><CalendarMonth sx={{ color: n.priority === 'high' ? '#ef4444' : '#94a3b8' }} /></ListItemIcon>
                  <ListItemText primary={n.title} secondary={n.date} />
                  <Chip label={n.priority} size="small" color={n.priority === 'high' ? 'error' : 'default'} />
                </ListItem>
              ))}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: 'background.paper', border: '1px solid #334155' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Upcoming Events</Typography>
              {upcoming.map((u, i) => (
                <Box key={i} sx={{ mb: 2, p: 2, borderRadius: 2, bgcolor: 'rgba(99,102,241,0.1)' }}>
                  <Typography sx={{ fontWeight: 600 }}>{u.title}</Typography>
                  <Typography variant="body2" sx={{ color: '#94a3b8' }}>{u.date} at {u.time}</Typography>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}