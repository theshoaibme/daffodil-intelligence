import { Box, Typography, Card, CardContent, Table, TableBody, TableCell, TableHead, TableRow, Chip, Button, TextField, Tabs, Tab } from '@mui/material'
import { useState } from 'react'

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
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>Admin Panel</Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab label="Users" />
        <Tab label="System Logs" />
        <Tab label="Settings" />
      </Tabs>

      {tab === 0 && (
        <Card sx={{ bgcolor: 'background.paper', border: '1px solid #334155' }}>
          <CardContent>
            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
              <TextField size="small" placeholder="Search users..." sx={{ flexGrow: 1 }} />
              <Button variant="contained">Add User</Button>
            </Box>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Dept</TableCell>
                  <TableCell>Sem</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell>{u.id}</TableCell>
                    <TableCell>{u.name}</TableCell>
                    <TableCell>{u.email}</TableCell>
                    <TableCell>{u.dept}</TableCell>
                    <TableCell>{u.semester}</TableCell>
                    <TableCell>
                      <Chip label={u.status} size="small" color={u.status === 'active' ? 'success' : 'default'} />
                    </TableCell>
                    <TableCell>
                      <Button size="small">Edit</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {tab === 1 && (
        <Card sx={{ bgcolor: 'background.paper', border: '1px solid #334155' }}>
          <CardContent>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Time</TableCell>
                  <TableCell>Action</TableCell>
                  <TableCell>User</TableCell>
                  <TableCell>Agent</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {logs.map((l, i) => (
                  <TableRow key={i}>
                    <TableCell>{l.time}</TableCell>
                    <TableCell>{l.action}</TableCell>
                    <TableCell>{l.user}</TableCell>
                    <TableCell>{l.agent}</TableCell>
                    <TableCell>
                      <Chip label={l.status} size="small" color={l.status === 'success' ? 'success' : 'error'} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {tab === 2 && (
        <Card sx={{ bgcolor: 'background.paper', border: '1px solid #334155' }}>
          <CardContent>
            <Typography>System configuration coming soon...</Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  )
}