import { useNavigate } from 'react-router';
import { Container, Typography, Box } from '@mui/material';

export default function Inventory() {
  const navigate = useNavigate();

  return (
    <Container maxWidth="md">
      <Box sx={{
        py: 8,
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh'
      }}>
        <Typography variant="h3" component="h1" gutterBottom>
          INVENTORY
        </Typography>
        <Typography variant="body1" gutterBottom>
          Welcome to the Inventory Interface page!
        </Typography>
        <Typography variant="body1">
          This is still under development, please come back later!
        </Typography>
      </Box>
    </Container>
  )
}
