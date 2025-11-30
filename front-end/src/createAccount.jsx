import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useForm } from 'react-hook-form';
import { useApi } from './useApi.jsx';
import SousChefLogo from './souschef-logo.png';

export default function CreateAccount(props) {
  const navigate = useNavigate();
  const { api } = useApi();
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
        // Check if it's a validation error object
        if (error.data.error) {
          // Single error message
          setServerError(error.data.error);
        } else if (error.data.details) {
          // Error with details (from non-JSON response)
          setServerError(`Server Error: ${error.data.details}`);
        } else {
          // Backend validation errors - format nicely
          const errorMessages = Object.entries(error.data)
            .map(([field, messages]) => {
              const fieldLabel = field.charAt(0).toUpperCase() + field.replace('_', ' ').slice(1);
              const messageText = Array.isArray(messages) ? messages.join(' ') : messages;
              return `${fieldLabel}: ${messageText}`;
            })
            .join('\n');
          setServerError(errorMessages);
        }
      } else if (error.message) {
        // Network or other errors
        setServerError(error.message);
      } else {
        setServerError('Registration failed. Please check your connection and try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="create-account-page">
      <img className="sous-chef-logo" src={SousChefLogo} width="150px"/>

      <div className="create-account-box">
        <h1>Create Account</h1>

        {serverError && (
          <div className="errors">
            {serverError}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)}>
          <div>
            <label>
              Username: *
            </label>
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
            />
            {errors.username && <div className="errors">{errors.username.message}</div>}
          </div>

          <div>
            <label>
              Email: *
            </label>
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
            />
            {errors.email && <div className="errors">{errors.email.message}</div>}
          </div>

          <div>
            <label>
              Password: *
            </label>
            <input
              type="password"
              {...register('password', {
                required: 'Password is required',
                minLength: {
                  value: 8,
                  message: 'Password must be at least 8 characters'
                }
              })}
            />
            {errors.password && <div className="errors">{errors.password.message}</div>}
          </div>

          <div>
            <label>
              Confirm Password: *
            </label>
            <input
              type="password"
              {...register('password_confirm', {
                required: 'Please confirm your password',
                validate: value =>
                  value === password || 'Passwords do not match'
              })}
            />
            {errors.password_confirm && <div className="errors">{errors.password_confirm.message}</div>}
          </div>

          <div style={{textAlign: 'center'}}>
            * Required fields
          </div>

          <div>
            <button
              className="button-blue"
              type="button"
              onClick={() => navigate('/login')}
              disabled={isSubmitting}
            >
              Back to Login
            </button>
            <button
              className="button"
              type="submit"
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
