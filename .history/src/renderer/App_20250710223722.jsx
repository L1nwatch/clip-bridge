import React, { useState } from 'react';
import { AppBar, Toolbar, IconButton, Typography, Box, Paper, Divider, BottomNavigation, BottomNavigationAction, Stack } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import SettingsIcon from '@mui/icons-material/Settings';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import RefreshIcon from '@mui/icons-material/Refresh';
import FilterListIcon from '@mui/icons-material/FilterList';
import HistoryIcon from '@mui/icons-material/History';
import DevicesIcon from '@mui/icons-material/Devices';

import DeviceCard from './components/DeviceCard';

export default function App() {
  const [tab, setTab] = useState(0);

  const devices = [
    { name: 'PTOP-880OUEHO.china...', ip: '192.168.2.33' },
    { name: 'LAPTOP-12345.home', ip: '192.168.2.34' }
  ];

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <AppBar position="static">
        <Toolbar>
          <IconButton edge="start" color="inherit">
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1 }} align="center">
            Clipboard Remote
          </Typography>
          <IconButton color="inherit">
            <SettingsIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Box sx={{ p: 2, flexGrow: 1, overflow: 'auto' }}>
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="h5">React + Electron</Typography>
        </Paper>
        <Divider sx={{ my: 2, cursor: 'row-resize' }} />
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
            <IconButton size="small">
              <RefreshIcon />
            </IconButton>
            <IconButton size="small">
              <FilterListIcon />
            </IconButton>
          </Box>
          <Stack spacing={2}>
            {devices.map((d, idx) => (
              <DeviceCard key={idx} name={d.name} ip={d.ip} />
            ))}
          </Stack>
        </Box>
      </Box>

      <BottomNavigation value={tab} onChange={(_, v) => setTab(v)}>
        <BottomNavigationAction label="Clipboard" icon={<ContentCopyIcon />} />
        <BottomNavigationAction label="History" icon={<HistoryIcon />} />
        <BottomNavigationAction label="Devices" icon={<DevicesIcon />} />
      </BottomNavigation>
    </Box>
  );
}
