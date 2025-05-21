import React from 'react';
import { Box, Typography, Paper, List, ListItem, Divider, Chip, Button } from '@mui/material';
import { useTradeStream } from '../hooks/useTradeStream';
import { formatCurrency, formatTime } from '../utils/formatters';

const LiveTradesPanel: React.FC = () => {
  const { isConnected, trades, error, reconnect } = useTradeStream();

  return (
    <Paper elevation={1} sx={{ height: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, borderBottom: '1px solid rgba(0, 0, 0, 0.12)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" component="h2">
          Live Trades
        </Typography>
        <Box display="flex" alignItems="center" gap={1}>
          <Chip 
            size="small"
            label={isConnected ? 'Connected' : 'Disconnected'} 
            color={isConnected ? 'success' : 'error'} 
            variant="outlined"
          />
          {!isConnected && (
            <Button size="small" variant="outlined" onClick={reconnect}>
              Reconnect
            </Button>
          )}
        </Box>
      </Box>
      
      {error && (
        <Box sx={{ p: 2, bgcolor: 'error.light', color: 'error.contrastText' }}>
          <Typography variant="body2">{error}</Typography>
        </Box>
      )}
      
      {trades.length === 0 ? (
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body1" color="text.secondary">
            {isConnected ? 'Waiting for trades...' : 'Connect to see live trades'}
          </Typography>
        </Box>
      ) : (
        <List sx={{ 
          flex: 1, 
          overflow: 'auto', 
          padding: 0,
          '&::-webkit-scrollbar': {
            width: '0.4em'
          },
          '&::-webkit-scrollbar-track': {
            boxShadow: 'inset 0 0 6px rgba(0,0,0,0.1)',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'rgba(0,0,0,.2)',
            borderRadius: '4px',
          },
        }}>
          {trades.map((trade, index) => (
            <React.Fragment key={`${trade.data.timestamp}-${index}`}>
              <ListItem sx={{ 
                py: 1.5, 
                px: 2, 
                bgcolor: trade.data.side === 'buy' ? 'success.50' : 'error.50',
                '&:hover': {
                  bgcolor: trade.data.side === 'buy' ? 'success.100' : 'error.100',
                }
              }}>
                <Box sx={{ display: 'flex', width: '100%', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="subtitle2" component="span" sx={{ fontWeight: 'bold', mr: 1 }}>
                      {trade.data.symbol}
                    </Typography>
                    <Chip 
                      size="small" 
                      label={trade.data.side.toUpperCase()} 
                      color={trade.data.side === 'buy' ? 'success' : 'error'} 
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
                  </Box>
                  <Box textAlign="right">
                    <Typography variant="subtitle2" component="div" sx={{ fontWeight: 'medium' }}>
                      {formatCurrency(trade.data.price)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Vol: {trade.data.volume.toFixed(4)}
                    </Typography>
                  </Box>
                </Box>
              </ListItem>
              <Divider component="li" />
            </React.Fragment>
          ))}
        </List>
      )}
    </Paper>
  );
};

export default LiveTradesPanel; 