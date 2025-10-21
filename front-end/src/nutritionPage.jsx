import { useNavigate } from 'react-router';
import { Container, Typography, Box } from '@mui/material';

export default function Nutritionist() {
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
          NUTRITIONIST
        </Typography>
        <Typography variant="body1" gutterBottom>
          Welcome to the Nutritionist Interface page!
        </Typography>
        <Typography variant="body1">
          This is still under development, please come back later!
        </Typography>
      </Box>
    </Container>
  )
}
