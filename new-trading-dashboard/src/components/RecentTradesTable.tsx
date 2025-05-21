import React from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  CircularProgress, 
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip
} from '@mui/material';

interface Trade {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  size: number;
  price: number;
  cost: number;
  timestamp: string;
  strategy_id: string;
  order_type: 'MARKET' | 'LIMIT' | 'STOP';
}

interface RecentTradesTableProps {
  trades: Trade[];
  isLoading: boolean;
  error: unknown;
}

const RecentTradesTable: React.FC<RecentTradesTableProps> = ({ trades, isLoading, error }) => {
  if (isLoading) {
    return (
      <Card>
        <CardContent sx={{ textAlign: 'center', p: 3, minHeight: '150px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Box>
            <CircularProgress size={30} />
            <Typography variant="body2" sx={{ mt: 1 }}>
              Loading trade data...
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent sx={{ minHeight: '150px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Typography color="error" variant="body1">
            Error loading trade data
          </Typography>
        </CardContent>
      </Card>
    );
  }

  // If no trades are available, show a placeholder
  if (trades.length === 0) {
    return (
      <Card>
        <CardContent sx={{ minHeight: '150px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Typography variant="body1" color="text.secondary">
            No recent trades found
          </Typography>
        </CardContent>
      </Card>
    );
  }

  // Format the time for display
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Recent Trades
        </Typography>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Time</TableCell>
                <TableCell>Symbol</TableCell>
                <TableCell>Side</TableCell>
                <TableCell align="right">Size</TableCell>
                <TableCell align="right">Price</TableCell>
                <TableCell align="right">Total</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {trades.map((trade) => (
                <TableRow key={trade.id}>
                  <TableCell>{formatTime(trade.timestamp)}</TableCell>
                  <TableCell>{trade.symbol}</TableCell>
                  <TableCell>
                    <Chip 
                      label={trade.side} 
                      size="small" 
                      color={trade.side === 'BUY' ? 'success' : 'error'}
                      sx={{ minWidth: '60px' }}
                    />
                  </TableCell>
                  <TableCell align="right">{trade.size}</TableCell>
                  <TableCell align="right">${trade.price.toFixed(2)}</TableCell>
                  <TableCell align="right">${trade.cost.toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
};

export default RecentTradesTable; 