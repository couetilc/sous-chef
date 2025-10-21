// /src/login
import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useUser } from './useUser.jsx';
import { Box, Container, Paper, TextField, Button, Typography, Stack, Link } from '@mui/material';
import LoginIcon from '@mui/icons-material/Login';

export default function Login(props) {
  const navigate = useNavigate();
  const { login } = useUser();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  async function checkLogin(e) {
    e.preventDefault();

    if (username === '') {
      alert("Please enter your username!");
      return;
    }

    if (password === '') {
      alert("Please enter your password!");
      return;
    }

    try {
      await login({ username, password });
      navigate("/home/");
    } catch (error) {
      alert("Invalid Credentials!");
    }
  }

  return (
    <Container maxWidth="xs">
      <Box sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 'calc(100vh - 450px)',
        py: 4
      }}>
        <Paper
          elevation={2}
          sx={{
            p: 4,
            width: '100%',
            bgcolor: 'background.paper',
          }}
        >
          <Typography
            variant="h4"
            component="h1"
            gutterBottom
            align="center"
            sx={{ fontWeight: 700, color: 'text.primary', mb: 1 }}
          >
            Welcome Back
          </Typography>
          <Typography
            variant="body2"
            align="center"
            color="text.secondary"
            sx={{ mb: 4 }}
          >
            Sign in to continue to Sous Chef
          </Typography>

          <Box component="form" onSubmit={checkLogin}>
            <Stack spacing={2.5}>
              <TextField
                label="Username"
                variant="outlined"
                fullWidth
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoFocus
              />

              <TextField
                label="Password"
                type="password"
                variant="outlined"
                fullWidth
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />

              <Button
                type="submit"
                variant="contained"
                color="primary"
                size="large"
                fullWidth
                endIcon={<LoginIcon />}
                sx={{ mt: 1 }}
              >
                Sign In
              </Button>

              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Don't have an account?{' '}
                  <Link
                    component="button"
                    type="button"
                    variant="body2"
                    onClick={() => navigate("/create-account")}
                    sx={{
                      textDecoration: 'none',
                      fontWeight: 600,
                      color: 'secondary.main',
                      '&:hover': { textDecoration: 'underline' }
                    }}
                  >
                    Create one
                  </Link>
                </Typography>
              </Box>
            </Stack>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}
