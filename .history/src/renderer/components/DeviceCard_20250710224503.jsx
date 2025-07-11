import React from 'react';
import PropTypes from 'prop-types';
import { Card, CardContent, Typography, IconButton, Stack } from '@mui/material';
import ContentPasteGoIcon from '@mui/icons-material/ContentPaste';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import GridViewIcon from '@mui/icons-material/GridView';

export default function DeviceCard({ name, ip }) {
  return (
    <Card variant="outlined">
      <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <GridViewIcon />
        <Stack sx={{ flexGrow: 1 }}>
          <Typography variant="subtitle1">{name}</Typography>
          <Typography variant="caption" color="text.secondary">{ip}</Typography>
        </Stack>
        <IconButton size="small" aria-label="copy">
          <ContentCopyIcon />
        </IconButton>
        <IconButton size="small" aria-label="paste">
          <ContentPasteGoIcon />
        </IconButton>
      </CardContent>
    </Card>
  );
}
