import React from 'react';
import { useNavigate, Navigate } from 'react-router';
import ChefHat from './chefhat.png';
import Nutrition from './nutrition.png';
import Recipe from './recipe.png';
import Inventory from './inventory.png';
import { useUser } from './useUser.jsx';
import {
  Container,
  Typography,
  Box,
  Card,
  CardActionArea,
  CardMedia,
  CardContent,
  Button,
  Grid
} from '@mui/material';

// home page, only accessed after a user has logged in

export default function Home(props) {
  const navigate = useNavigate();
  const { user } = useUser();

  // if user is null, no user is logged in, redirect to the login page
  if (!user) {
    return <Navigate to="/login" />
  }

  const navigationItems = [
    { title: 'AI Sous Chef', image: ChefHat, path: '/sous-chef' },
    { title: 'Nutritionist', image: Nutrition, path: '/nutritionist' },
    { title: 'Recipes', image: Recipe, path: '/recipes' },
    { title: 'Inventory', image: Inventory, path: '/inventory' }
  ];

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 3 }}>
        <Typography
          variant="h5"
          sx={{
            fontWeight: 600,
            color: 'text.primary',
            mb: 3
          }}
        >
          Welcome back, {user.username}
        </Typography>

        <Grid container spacing={2.5}>
          {navigationItems.map((item) => (
            <Grid item xs={12} sm={6} md={3} key={item.path}>
              <Card
                sx={{
                  position: 'relative',
                  height: 200,
                  overflow: 'hidden',
                  transition: 'all 0.3s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    '& .overlay': {
                      opacity: 0.95,
                    },
                    '& .title': {
                      transform: 'scale(1.05)',
                    }
                  }
                }}
              >
                <CardActionArea
                  onClick={() => navigate(item.path)}
                  sx={{ height: '100%' }}
                >
                  <CardMedia
                    component="img"
                    image={item.image}
                    alt={item.title}
                    sx={{
                      height: '100%',
                      objectFit: 'cover',
                      filter: 'brightness(0.7)',
                    }}
                  />
                  <Box
                    className="overlay"
                    sx={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      bgcolor: 'rgba(245, 158, 11, 0.88)', // Yellow/gold overlay
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      opacity: 0.9,
                      transition: 'opacity 0.3s ease-in-out',
                    }}
                  >
                    <Typography
                      className="title"
                      variant="h6"
                      sx={{
                        color: 'white',
                        fontWeight: 700,
                        textAlign: 'center',
                        transition: 'transform 0.3s ease-in-out',
                        px: 2,
                      }}
                    >
                      {item.title}
                    </Typography>
                  </Box>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
    </Container>
  )
}
