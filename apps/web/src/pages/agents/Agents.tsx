import { Grid, Card, CardContent, Typography, Box, Chip, LinearProgress, Button } from '@mui/material'
import { School, LibraryBooks, DirectionsBus, Work, Code, Psychology, LocalHospital, AttachMoney, Visibility, Mic } from '@mui/icons-material'

const agents = [
  { name: 'Academic Agent', icon: <School />, desc: 'CGPA, results, courses, syllabus', status: 'Active', color: '#6366f1', tools: 5 },
  { name: 'Library Agent', icon: <LibraryBooks />, desc: 'Books, journals, PDFs', status: 'Ready', color: '#ec4899', tools: 4 },
  { name: 'Campus Agent', icon: <DirectionsBus />, desc: 'Shuttle, rooms, notices', status: 'Ready', color: '#22c55e', tools: 4 },
  { name: 'Career Agent', icon: <Work />, desc: 'Jobs, CV, roadmap', status: 'Ready', color: '#f59e0b', tools: 5 },
  { name: 'Coding Agent', icon: <Code />, desc: 'Debug, generate code', status: 'Ready', color: '#3b82f6', tools: 5 },
  { name: 'Research Agent', icon: <Psychology />, desc: 'Papers, thesis help', status: 'Ready', color: '#8b5cf6', tools: 5 },
  { name: 'Wellness Agent', icon: <LocalHospital />, desc: 'Mental health support', status: 'Ready', color: '#06b6d4', tools: 5 },
  { name: 'Finance Agent', icon: <AttachMoney />, desc: 'Fees, payments, waivers', status: 'Ready', color: '#ef4444', tools: 5 },
  { name: 'Vision Agent', icon: <Visibility />, desc: 'Image, PDF analysis', status: 'Ready', color: '#14b8a6', tools: 5 },
  { name: 'Voice Agent', icon: <Mic />, desc: 'Speech, voice chat', status: 'Ready', color: '#f97316', tools: 4 },
]

export default function Agents() {
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>AI Agents</Typography>
      <Grid container spacing={3}>
        {agents.map((agent, i) => (
          <Grid item xs={12} sm={6} md={4} key={i}>
            <Card sx={{ bgcolor: 'background.paper', border: '1px solid #334155', height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: `${agent.color}20`, color: agent.color }}>{agent.icon}</Box>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>{agent.name}</Typography>
                    <Typography variant="body2" sx={{ color: '#94a3b8' }}>{agent.desc}</Typography>
                  </Box>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="caption" sx={{ color: '#94a3b8' }}>Status</Typography>
                    <Chip label={agent.status} size="small" sx={{ bgcolor: `${agent.color}20`, color: agent.color }} />
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="caption" sx={{ color: '#94a3b8' }}>Tools Available</Typography>
                    <Typography variant="caption">{agent.tools}</Typography>
                  </Box>
                  <LinearProgress variant="determinate" value={agent.status === 'Active' ? 100 : 80} sx={{ height: 6, borderRadius: 3, bgcolor: '#334155' }} />
                </Box>
                <Button fullWidth variant="outlined" sx={{ borderColor: agent.color, color: agent.color }}>
                  Launch Agent
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}