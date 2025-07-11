import React from 'react';
import PropTypes from 'prop-types';
import { Card, CardContent, Typography, IconButton, Stack, Chip } from '@mui/material';
import ContentPasteGoIcon from '@mui/icons-material/ContentPaste';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import GridViewIcon from '@mui/icons-material/GridView';

export default function DeviceCard({ name, ip, status = 'unknown' }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'success';
      case 'disconnected': return 'error';
      case 'connecting': return 'warning';
      default: return 'default';
    }
  };

  return (
    <Card variant="outlined">
      <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <GridViewIcon />
        <Stack sx={{ flexGrow: 1 }}>
          <Typography variant="subtitle1">{name}</Typography>
          <Typography variant="caption" color="text.secondary">{ip}</Typography>
        </Stack>
        <Chip 
          label={status} 
          color={getStatusColor(status)}
          size="small"
          sx={{ minWidth: 80 }}
        />
        <IconButton size="small" aria-label="copy" disabled={status !== 'connected'}>
          <ContentCopyIcon />
        </IconButton>
        <IconButton size="small" aria-label="paste" disabled={status !== 'connected'}>
          <ContentPasteGoIcon />
        </IconButton>
      </CardContent>
    </Card>
  );
}

DeviceCard.propTypes = {
  name: PropTypes.string.isRequired,
  ip: PropTypes.string.isRequired,
  status: PropTypes.oneOf(['connected', 'disconnected', 'connecting', 'unknown']),
};
