import { useState } from 'react'
import { Box, Card, CardContent, Typography, TextField, Button, Grid, Chip, Select, MenuItem, FormControl, InputLabel, IconButton, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material'
import { Add, Delete, Edit, Star, PlayArrow } from '@mui/icons-material'

const TEMPLATES = [
  { id: 'study_buddy', name: 'Study Buddy', desc: 'Friendly study companion', icon: '📚' },
  { id: 'teaching_assistant', name: 'Teaching Assistant', desc: 'Formal course help', icon: '👨‍🏫' },
  { id: 'career_counselor', name: 'Career Counselor', desc: 'Job & career guidance', icon: '💼' },
  { id: 'research_advisor', name: 'Research Advisor', desc: 'Thesis & papers', icon: '🔬' },
  { id: 'code_mentor', name: 'Code Mentor', desc: 'Programming help', icon: '💻' },
  { id: 'wellness_coach', name: 'Wellness Coach', desc: 'Mental support', icon: '🧘' },
]

const tones = [
  { value: 'friendly', label: 'Friendly' },
  { value: 'formal', label: 'Formal' },
  { value: 'casual', label: 'Casual' },
  { value: 'technical', label: 'Technical' },
  { value: 'supportive', label: 'Supportive' },
]

interface CustomAgent {
  id: string
  name: string
  description: string
  template: string
  tone: string
  systemPrompt: string
  isPublic: boolean
  usageCount: number
  rating: number
}

export default function AgentBuilder() {
  const [agents, setAgents] = useState<CustomAgent[]>([])
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editAgent, setEditAgent] = useState<CustomAgent | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    template: 'study_buddy',
    tone: 'friendly',
    systemPrompt: '',
    isPublic: false
  })

  const handleCreate = () => {
    const newAgent: CustomAgent = {
      id: Date.now().toString(),
      name: formData.name,
      description: formData.description,
      template: formData.template,
      tone: formData.tone,
      systemPrompt: formData.systemPrompt || `You are ${formData.name}. ${formData.description}`,
      isPublic: formData.isPublic,
      usageCount: 0,
      rating: 0
    }
    setAgents([...agents, newAgent])
    setDialogOpen(false)
    resetForm()
  }

  const handleDelete = (id: string) => {
    setAgents(agents.filter(a => a.id !== id))
  }

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      template: 'study_buddy',
      tone: 'friendly',
      systemPrompt: '',
      isPublic: false
    })
    setEditAgent(null)
  }

  const openEdit = (agent: CustomAgent) => {
    setEditAgent(agent)
    setFormData({
      name: agent.name,
      description: agent.description,
      template: agent.template,
      tone: agent.tone,
      systemPrompt: agent.systemPrompt,
      isPublic: agent.isPublic
    })
    setDialogOpen(true)
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>Agent Builder</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={() => setDialogOpen(true)}>
          Create Agent
        </Button>
      </Box>

      <Typography variant="h6" sx={{ mb: 2 }}>Templates</Typography>
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {TEMPLATES.map(t => (
          <Grid item xs={12} sm={6} md={4} key={t.id}>
            <Card sx={{ cursor: 'pointer', '&:hover': { borderColor: 'primary.main' } }}
              onClick={() => { setFormData({ ...formData, template: t.id }); setDialogOpen(true) }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="h4">{t.icon}</Typography>
                <Box>
                  <Typography sx={{ fontWeight: 600 }}>{t.name}</Typography>
                  <Typography variant="body2" sx={{ color: '#94a3b8' }}>{t.desc}</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {agents.length > 0 && (
        <>
          <Typography variant="h6" sx={{ mb: 2 }}>Your Custom Agents</Typography>
          <Grid container spacing={2}>
            {agents.map(agent => (
              <Grid item xs={12} sm={6} md={4} key={agent.id}>
                <Card sx={{ bgcolor: 'background.paper', border: '1px solid #334155' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography sx={{ fontWeight: 600 }}>{agent.name}</Typography>
                      <Box>
                        <IconButton size="small" onClick={() => openEdit(agent)}><Edit fontSize="small" /></IconButton>
                        <IconButton size="small" onClick={() => handleDelete(agent.id)}><Delete fontSize="small" /></IconButton>
                      </Box>
                    </Box>
                    <Typography variant="body2" sx={{ color: '#94a3b8', mb: 2 }}>{agent.description}</Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                      <Chip label={agent.tone} size="small" />
                      <Chip label={agent.template} size="small" variant="outlined" />
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Star sx={{ fontSize: 16, color: '#f59e0b' }} />
                        <Typography variant="body2">{agent.rating.toFixed(1)}</Typography>
                        <Typography variant="body2" sx={{ color: '#64748b' }}>({agent.usageCount} uses)</Typography>
                      </Box>
                      <IconButton sx={{ bgcolor: '#6366f1', color: 'white', '&:hover': { bgcolor: '#4f46e5' } }}>
                        <PlayArrow />
                      </IconButton>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </>
      )}

      <Dialog open={dialogOpen} onClose={() => { setDialogOpen(false); resetForm() }} maxWidth="sm" fullWidth>
        <DialogTitle>{editAgent ? 'Edit Agent' : 'Create New Agent'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField label="Agent Name" value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} fullWidth />
            <TextField label="Description" value={formData.description} onChange={e => setFormData({ ...formData, description: e.target.value })} fullWidth multiline rows={2} />
            <FormControl fullWidth>
              <InputLabel>Template</InputLabel>
              <Select value={formData.template} label="Template" onChange={e => setFormData({ ...formData, template: e.target.value })}>
                {TEMPLATES.map(t => <MenuItem key={t.id} value={t.id}>{t.name} - {t.desc}</MenuItem>)}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Tone</InputLabel>
              <Select value={formData.tone} label="Tone" onChange={e => setFormData({ ...formData, tone: e.target.value })}>
                {tones.map(t => <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>)}
              </Select>
            </FormControl>
            <TextField label="System Prompt (optional)" value={formData.systemPrompt} onChange={e => setFormData({ ...formData, systemPrompt: e.target.value })} fullWidth multiline rows={4} helperText="Custom instructions for your agent" />
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Button variant={formData.isPublic ? 'contained' : 'outlined'} onClick={() => setFormData({ ...formData, isPublic: !formData.isPublic })}>
                {formData.isPublic ? 'Public' : 'Private'}
              </Button>
              <Typography variant="body2" sx={{ color: '#94a3b8' }}>{formData.isPublic ? 'Anyone can use this agent' : 'Only you can use'}</Typography>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setDialogOpen(false); resetForm() }}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate} disabled={!formData.name || !formData.description}>
            {editAgent ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}