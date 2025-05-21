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

interface Position {
  id: string;
  symbol: string;
  side: 'LONG' | 'SHORT';
  size: number;
  entry_price: number;
  current_price: number;
  pnl_usd: number;
  pnl_percent: number;
  timestamp: string;
  strategy_id: string;
}

interface ActivePositionsTableProps {
  positions: Position[];
  isLoading: boolean;
  error: unknown;
}

const ActivePositionsTable: React.FC<ActivePositionsTableProps> = ({ positions, isLoading, error }) => {
  if (isLoading) {
    return (
      <Card>
        <CardContent sx={{ textAlign: 'center', p: 3, minHeight: '150px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Box>
            <CircularProgress size={30} />
            <Typography variant="body2" sx={{ mt: 1 }}>
              Loading position data...
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
            Error loading position data
          </Typography>
        </CardContent>
      </Card>
    );
  }

  // If no positions are available, show a placeholder
  if (positions.length === 0) {
    return (
      <Card>
        <CardContent sx={{ minHeight: '150px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Typography variant="body1" color="text.secondary">
            No active positions found
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Active Positions
        </Typography>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Symbol</TableCell>
                <TableCell>Side</TableCell>
                <TableCell>Size</TableCell>
                <TableCell align="right">Entry Price</TableCell>
                <TableCell align="right">Current Price</TableCell>
                <TableCell align="right">P&L</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {positions.map((position) => (
                <TableRow key={position.id}>
                  <TableCell>{position.symbol}</TableCell>
                  <TableCell>
                    <Chip 
                      label={position.side} 
                      size="small" 
                      color={position.side === 'LONG' ? 'success' : 'error'}
                      sx={{ minWidth: '70px' }}
                    />
                  </TableCell>
                  <TableCell>{position.size}</TableCell>
                  <TableCell align="right">${position.entry_price.toFixed(2)}</TableCell>
                  <TableCell align="right">${position.current_price.toFixed(2)}</TableCell>
                  <TableCell align="right" sx={{ 
                    color: position.pnl_percent >= 0 ? 'success.main' : 'error.main' 
                  }}>
                    {position.pnl_percent >= 0 ? '+' : ''}{position.pnl_percent.toFixed(2)}%
                    <br />
                    <Typography variant="caption" component="span" sx={{ 
                      color: position.pnl_usd >= 0 ? 'success.main' : 'error.main' 
                    }}>
                      ${position.pnl_usd >= 0 ? '+' : ''}{position.pnl_usd.toFixed(2)}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
};

export default ActivePositionsTable; 