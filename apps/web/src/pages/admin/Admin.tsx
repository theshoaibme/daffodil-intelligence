import { Box, Typography, Card, CardContent, Table, TableBody, TableCell, TableHead, TableRow, Chip, Button, TextField, Tabs, Tab } from '@mui/material'
import { useState } from 'react'

const colors = {
  onSurface: '#e5e2e3',
  onSurfaceVariant: '#c3c6d1',
  primary: '#8ab4f8',
}

const users = [
  { id: 1, name: 'John Doe', email: 'john@diu.edu', dept: 'CSE', semester: 6, status: 'active' },
  { id: 2, name: 'Jane Smith', email: 'jane@diu.edu', dept: 'CSE', semester: 4, status: 'active' },
  { id: 3, name: 'Bob Wilson', email: 'bob@diu.edu', dept: 'SWE', semester: 8, status: 'inactive' },
]

const logs = [
  { time: '2024-03-15 10:30', action: 'Chat Request', user: 'john@diu.edu', agent: 'Academic', status: 'success' },
  { time: '2024-03-15 10:25', action: 'Login', user: 'jane@diu.edu', agent: '-', status: 'success' },
  { time: '2024-03-15 10:20', action: 'Voice Call', user: 'bob@diu.edu', agent: 'Voice', status: 'failed' },
]

export default function Admin() {
  const [tab, setTab] = useState(0)

  return (
    <Box>
      <Typography sx={{ 
        mb: 3, 
        fontSize: '28px',
        fontWeight: 500,
        color: colors.onSurface,
        fontFamily: '"Roboto Flex", Roboto, sans-serif'
      }}>
        Admin Panel
      </Typography>
      
      <Tabs 
        value={tab} 
        onChange={(_, v) => setTab(v)} 
        sx={{ 
          mb: 3,
          '& .MuiTab-root': {
            color: colors.onSurfaceVariant,
            fontFamily: '"Roboto Flex", Roboto, sans-serif',
            fontSize: '14px',
            textTransform: 'none',
            fontWeight: 500,
            minHeight: 48,
          },
          '& .Mui-selected': {
            color: colors.primary,
          },
          '& .MuiTabs-indicator': {
            bgcolor: colors.primary,
          }
        }}
      >
        <Tab label="Users" />
        <Tab label="System Logs" />
        <Tab label="Settings" />
      </Tabs>

      {tab === 0 && (
        <Card sx={{ 
          bgcolor: '#191A1F', 
          border: '1px solid #444746',
          borderRadius: '28px'
        }}>
          <CardContent>
            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
              <TextField 
                size="small" 
                placeholder="Search users..."
                sx={{ 
                  flexGrow: 1,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: '28px',
                    bgcolor: 'transparent',
                    '& fieldset': { borderColor: '#444746' },
                    '&:hover fieldset': { borderColor: '#8d919b' },
                    '&.Mui-focused fieldset': { borderColor: '#8ab4f8', borderWidth: '2px' },
                  },
                  '& input': { 
                    color: colors.onSurface,
                    fontSize: '14px',
                    fontFamily: '"Roboto Flex", Roboto, sans-serif'
                  },
                }}
              />
              <Button 
                variant="contained"
                sx={{
                  bgcolor: colors.primary,
                  color: '#131314',
                  borderRadius: '28px',
                  fontWeight: 500,
                  fontSize: '14px',
                  fontFamily: '"Roboto Flex", Roboto, sans-serif',
                  textTransform: 'none',
                  '&:hover': { bgcolor: '#a8c8ff' }
                }}
              >
                Add User
              </Button>
            </Box>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: colors.onSurfaceVariant, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '12px', fontWeight: 500, borderBottom: '1px solid #444746' }}>ID</TableCell>
                  <TableCell sx={{ color: colors.onSurfaceVariant, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '12px', fontWeight: 500, borderBottom: '1px solid #444746' }}>Name</TableCell>
                  <TableCell sx={{ color: colors.onSurfaceVariant, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '12px', fontWeight: 500, borderBottom: '1px solid #444746' }}>Email</TableCell>
                  <TableCell sx={{ color: colors.onSurfaceVariant, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '12px', fontWeight: 500, borderBottom: '1px solid #444746' }}>Dept</TableCell>
                  <TableCell sx={{ color: colors.onSurfaceVariant, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '12px', fontWeight: 500, borderBottom: '1px solid #444746' }}>Sem</TableCell>
                  <TableCell sx={{ color: colors.onSurfaceVariant, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '12px', fontWeight: 500, borderBottom: '1px solid #444746' }}>Status</TableCell>
                  <TableCell sx={{ color: colors.onSurfaceVariant, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '12px', fontWeight: 500, borderBottom: '1px solid #444746' }}>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell sx={{ color: colors.onSurface, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '14px', borderBottom: '1px solid #444746' }}>{u.id}</TableCell>
                    <TableCell sx={{ color: colors.onSurface, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '14px', borderBottom: '1px solid #444746' }}>{u.name}</TableCell>
                    <TableCell sx={{ color: colors.onSurface, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '14px', borderBottom: '1px solid #444746' }}>{u.email}</TableCell>
                    <TableCell sx={{ color: colors.onSurface, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '14px', borderBottom: '1px solid #444746' }}>{u.dept}</TableCell>
                    <TableCell sx={{ color: colors.onSurface, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '14px', borderBottom: '1px solid #444746' }}>{u.semester}</TableCell>
                    <TableCell sx={{ borderBottom: '1px solid #444746' }}>
                      <Chip 
                        label={u.status} 
                        size="small" 
                        color={u.status === 'active' ? 'success' : 'default'}
                        sx={{ 
                          bgcolor: u.status === 'active' ? 'rgba(158, 242, 194, 0.12)' : 'rgba(255, 255, 255, 0.04)',
                          color: u.status === 'active' ? '#9ef2c2' : colors.onSurfaceVariant,
                          borderRadius: '9999px',
                          fontSize: '11px',
                          fontFamily: '"Roboto Flex", Roboto, sans-serif'
                        }} 
                      />
                    </TableCell>
                    <TableCell sx={{ borderBottom: '1px solid #444746' }}>
                      <Button 
                        size="small"
                        sx={{
                          color: colors.primary,
                          fontFamily: '"Roboto Flex", Roboto, sans-serif',
                          fontSize: '12px',
                          textTransform: 'none'
                        }}
                      >
                        Edit
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {tab === 1 && (
        <Card sx={{ 
          bgcolor: '#191A1F', 
          border: '1px solid #444746',
          borderRadius: '28px'
        }}>
          <CardContent>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: colors.onSurfaceVariant, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '12px', fontWeight: 500, borderBottom: '1px solid #444746' }}>Time</TableCell>
                  <TableCell sx={{ color: colors.onSurfaceVariant, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '12px', fontWeight: 500, borderBottom: '1px solid #444746' }}>Action</TableCell>
                  <TableCell sx={{ color: colors.onSurfaceVariant, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '12px', fontWeight: 500, borderBottom: '1px solid #444746' }}>User</TableCell>
                  <TableCell sx={{ color: colors.onSurfaceVariant, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '12px', fontWeight: 500, borderBottom: '1px solid #444746' }}>Agent</TableCell>
                  <TableCell sx={{ color: colors.onSurfaceVariant, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '12px', fontWeight: 500, borderBottom: '1px solid #444746' }}>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {logs.map((l, i) => (
                  <TableRow key={i}>
                    <TableCell sx={{ color: colors.onSurface, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '14px', borderBottom: '1px solid #444746' }}>{l.time}</TableCell>
                    <TableCell sx={{ color: colors.onSurface, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '14px', borderBottom: '1px solid #444746' }}>{l.action}</TableCell>
                    <TableCell sx={{ color: colors.onSurface, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '14px', borderBottom: '1px solid #444746' }}>{l.user}</TableCell>
                    <TableCell sx={{ color: colors.onSurface, fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '14px', borderBottom: '1px solid #444746' }}>{l.agent}</TableCell>
                    <TableCell sx={{ borderBottom: '1px solid #444746' }}>
                      <Chip 
                        label={l.status} 
                        size="small" 
                        color={l.status === 'success' ? 'success' : 'error'}
                        sx={{ 
                          bgcolor: l.status === 'success' ? 'rgba(158, 242, 194, 0.12)' : 'rgba(255, 180, 171, 0.12)',
                          color: l.status === 'success' ? '#9ef2c2' : '#ffb4ab',
                          borderRadius: '9999px',
                          fontSize: '11px',
                          fontFamily: '"Roboto Flex", Roboto, sans-serif'
                        }} 
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {tab === 2 && (
        <Card sx={{ 
          bgcolor: '#191A1F', 
          border: '1px solid #444746',
          borderRadius: '28px'
        }}>
          <CardContent>
            <Typography sx={{ 
              color: colors.onSurfaceVariant,
              fontFamily: '"Roboto Flex", Roboto, sans-serif',
              fontSize: '14px'
            }}>
              System configuration coming soon...
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  )
}