import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useForm } from 'react-hook-form';
import { useApi } from './useApi.jsx';
import './style.css';

export default function CreateAccount(props) {
  const navigate = useNavigate();
  const api = useApi();
  const [serverError, setServerError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
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

  const formDiv = {
    border: '5px solid black',
    backgroundColor: 'goldenrod',
    textAlign: 'center',
    padding: '20px'
  };

  const errorStyle = {
    color: 'darkred',
    fontSize: '0.9em',
    marginTop: '5px'
  };

  return (
    <div className="centered-div">
      <div style={formDiv}>
        <h1>Create Account</h1>

        {serverError && (
          <div style={{ ...errorStyle, marginBottom: '15px' }}>
            {serverError}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)}>
          <div style={{ marginBottom: '15px' }}>
            <label>
              Username: *
              <br />
              <input
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
                style={{ marginTop: '5px' }}
              />
            </label>
            {errors.username && <div style={errorStyle}>{errors.username.message}</div>}
          </div>

          <div style={{ marginBottom: '15px' }}>
            <label>
              Email: *
              <br />
              <input
                type="email"
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
                style={{ marginTop: '5px' }}
              />
            </label>
            {errors.email && <div style={errorStyle}>{errors.email.message}</div>}
          </div>

          <div style={{ marginBottom: '15px' }}>
            <label>
              Password: *
              <br />
              <input
                type="password"
                {...register('password', {
                  required: 'Password is required',
                  minLength: {
                    value: 8,
                    message: 'Password must be at least 8 characters'
                  }
                })}
                style={{ marginTop: '5px' }}
              />
            </label>
            {errors.password && <div style={errorStyle}>{errors.password.message}</div>}
          </div>

          <div style={{ marginBottom: '15px' }}>
            <label>
              Confirm Password: *
              <br />
              <input
                type="password"
                {...register('password_confirm', {
                  required: 'Please confirm your password',
                  validate: value =>
                    value === password || 'Passwords do not match'
                })}
                style={{ marginTop: '5px' }}
              />
            </label>
            {errors.password_confirm && <div style={errorStyle}>{errors.password_confirm.message}</div>}
          </div>

          <div style={{ fontSize: '0.9em', marginBottom: '15px' }}>
            * Required fields
          </div>

          <div className="inline-div">
            <button
              className="button"
              type="button"
              style={{ backgroundColor: 'gray', color: 'white' }}
              onClick={() => navigate('/login')}
              disabled={isSubmitting}
            >
              Back to Login
            </button>
            <div style={{ width: '10px' }}></div>
            <button
              className="button"
              type="submit"
              style={{ backgroundColor: 'green', color: 'white' }}
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Creating Account...' : 'Create Account'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
