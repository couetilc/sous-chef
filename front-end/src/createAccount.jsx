import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useForm, Controller } from 'react-hook-form';
import { useApi } from './useApi.jsx';
import {
  Box,
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Stack,
  Alert,
  Link
} from '@mui/material';
import PersonAddIcon from '@mui/icons-material/PersonAdd';

export default function CreateAccount(props) {
  const navigate = useNavigate();
  const { api } = useApi();
  const [serverError, setServerError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    control,
    formState: { errors }
  } = useForm();

  const password = watch('password');

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    setServerError('');

    try {
      const response = await api.register({
        username: data.username,
        email: data.email,
        password: data.password,
        password_confirm: data.password_confirm,
      });

      // If registration successful, redirect to login page
      alert('Account created successfully! Please log in with your new credentials.');
      navigate('/login');
    } catch (error) {
      console.error('Registration error:', error);

      // Handle different error types
      if (error.data && typeof error.data === 'object') {
        // Backend validation errors - format nicely
        const errorMessages = Object.entries(error.data)
          .map(([field, messages]) => {
            const fieldLabel = field.charAt(0).toUpperCase() + field.replace('_', ' ').slice(1);
            const messageText = Array.isArray(messages) ? messages.join(' ') : messages;
            return `${fieldLabel}: ${messageText}`;
          })
          .join('\n');
        setServerError(errorMessages);
      } else if (error.message) {
        // Network or other errors
        setServerError(error.message);
      } else {
        setServerError('Registration failed. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

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
            Create Account
          </Typography>
          <Typography
            variant="body2"
            align="center"
            color="text.secondary"
            sx={{ mb: 3 }}
          >
            Join Sous Chef to get started
          </Typography>

          {serverError && (
            <Alert severity="error" sx={{ mb: 2, whiteSpace: 'pre-line' }}>
              {serverError}
            </Alert>
          )}

          <form onSubmit={handleSubmit(onSubmit)}>
            <Stack spacing={2}>
              <TextField
                label="Username"
                fullWidth
                error={!!errors.username}
                helperText={errors.username?.message}
                {...register('username', {
                  required: 'Username is required',
                  maxLength: {
                    value: 150,
                    message: 'Username must be 150 characters or less'
                  },
                  pattern: {
                    value: /^[\w.@+-]+$/,
                    message: 'Username can only contain letters, digits, and @/./+/-/_'
                  }
                })}
              />

              <TextField
                label="Email"
                type="email"
                fullWidth
                error={!!errors.email}
                helperText={errors.email?.message}
                {...register('email', {
                  required: 'Email is required',
                  maxLength: {
                    value: 254,
                    message: 'Email must be 254 characters or less'
                  },
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Invalid email address'
                  }
                })}
              />

              <TextField
                label="Password"
                type="password"
                fullWidth
                error={!!errors.password}
                helperText={errors.password?.message || 'Minimum 8 characters'}
                {...register('password', {
                  required: 'Password is required',
                  minLength: {
                    value: 8,
                    message: 'Password must be at least 8 characters'
                  }
                })}
              />

              <TextField
                label="Confirm Password"
                type="password"
                fullWidth
                error={!!errors.password_confirm}
                helperText={errors.password_confirm?.message}
                {...register('password_confirm', {
                  required: 'Please confirm your password',
                  validate: value =>
                    value === password || 'Passwords do not match'
                })}
              />

              <Button
                variant="contained"
                color="primary"
                type="submit"
                size="large"
                fullWidth
                endIcon={<PersonAddIcon />}
                disabled={isSubmitting}
                sx={{ mt: 2 }}
              >
                {isSubmitting ? 'Creating Account...' : 'Create Account'}
              </Button>

              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Already have an account?{' '}
                  <Link
                    component="button"
                    type="button"
                    variant="body2"
                    onClick={() => navigate('/login')}
                    disabled={isSubmitting}
                    sx={{
                      textDecoration: 'none',
                      fontWeight: 600,
                      color: 'secondary.main',
                      '&:hover': { textDecoration: 'underline' }
                    }}
                  >
                    Sign in
                  </Link>
                </Typography>
              </Box>
            </Stack>
          </form>
        </Paper>
      </Box>
    </Container>
  );
}
