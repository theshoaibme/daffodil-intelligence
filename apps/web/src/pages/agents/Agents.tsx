import { Grid, Card, CardContent, Typography, Box, Chip, LinearProgress, Button } from '@mui/material'
import { School, LibraryBooks, DirectionsBus, Work, Code, Psychology, LocalHospital, AttachMoney, Visibility, Mic } from '@mui/icons-material'

const colors = {
  onSurface: '#e5e2e3',
  onSurfaceVariant: '#c3c6d1',
}

const agents = [
  { name: 'Academic Agent', icon: <School />, desc: 'CGPA, results, courses, syllabus', status: 'Active', color: '#8ab4f8', tools: 5 },
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
      <Typography sx={{ 
        mb: 3, 
        fontSize: '28px',
        fontWeight: 500,
        color: colors.onSurface,
        fontFamily: '"Roboto Flex", Roboto, sans-serif'
      }}>
        AI Agents
      </Typography>
      <Grid container spacing={3}>
        {agents.map((agent, i) => (
          <Grid item xs={12} sm={6} md={4} key={i}>
            <Card sx={{ 
              bgcolor: '#191A1F', 
              border: '1px solid #444746', 
              height: '100%',
              borderRadius: '28px'
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Box sx={{ p: 1.5, borderRadius: '16px', bgcolor: `${agent.color}20`, color: agent.color }}>{agent.icon}</Box>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography sx={{ 
                      fontSize: '16px',
                      fontWeight: 600,
                      color: colors.onSurface,
                      fontFamily: '"Roboto Flex", Roboto, sans-serif'
                    }}>
                      {agent.name}
                    </Typography>
                    <Typography sx={{ 
                      fontSize: '12px',
                      color: colors.onSurfaceVariant,
                      fontFamily: '"Roboto Flex", Roboto, sans-serif'
                    }}>
                      {agent.desc}
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography sx={{ 
                      fontSize: '12px',
                      color: colors.onSurfaceVariant,
                      fontFamily: '"Roboto Flex", Roboto, sans-serif'
                    }}>
                      Status
                    </Typography>
                    <Chip 
                      label={agent.status} 
                      size="small" 
                      sx={{ 
                        bgcolor: `${agent.color}20`, 
                        color: agent.color,
                        borderRadius: '9999px',
                        fontSize: '11px',
                        fontFamily: '"Roboto Flex", Roboto, sans-serif'
                      }} 
                    />
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography sx={{ 
                      fontSize: '12px',
                      color: colors.onSurfaceVariant,
                      fontFamily: '"Roboto Flex", Roboto, sans-serif'
                    }}>
                      Tools Available
                    </Typography>
                    <Typography sx={{ 
                      fontSize: '12px',
                      color: colors.onSurface,
                      fontFamily: '"Roboto Flex", Roboto, sans-serif'
                    }}>
                      {agent.tools}
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={agent.status === 'Active' ? 100 : 80} 
                    sx={{ 
                      height: 6, 
                      borderRadius: '16px', 
                      bgcolor: '#2a2a2b',
                      '& .MuiLinearProgress-bar': { bgcolor: agent.color }
                    }} 
                  />
                </Box>
                <Button 
                  fullWidth 
                  variant="outlined" 
                  sx={{ 
                    borderColor: agent.color, 
                    color: agent.color,
                    borderRadius: '16px',
                    fontWeight: 500,
                    fontSize: '14px',
                    fontFamily: '"Roboto Flex", Roboto, sans-serif',
                    textTransform: 'none',
                    '&:hover': { 
                      bgcolor: `${agent.color}15`,
                      borderColor: agent.color
                    }
                  }}
                >
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