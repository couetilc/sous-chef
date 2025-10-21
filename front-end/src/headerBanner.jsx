import { useNavigate, useLocation } from 'react-router';
import SousChefLogo from './souschef-logo.png';
import {
  AppBar,
  Toolbar,
  IconButton,
  Box,
  Typography,
  useMediaQuery,
  useTheme
} from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import LocalDiningIcon from '@mui/icons-material/LocalDining';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import InventoryIcon from '@mui/icons-material/Inventory';
import SettingsIcon from '@mui/icons-material/Settings';
import LogoutIcon from '@mui/icons-material/Logout';

  //find the url path at which the user is at, so that the navigation banner
  //can be hidden on login pages: "/login" and "/" ("/" redirects to login component)

export default function HeaderBanner() {
  const curLocation = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Show only logo on auth pages
  if ( curLocation.pathname.localeCompare("/") == 0 ||
       curLocation.pathname.localeCompare("/login/") == 0 ||
       curLocation.pathname.localeCompare("/create-account/") == 0 ) {
    return (
      <Box sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        py: 6,
        px: 2
      }}>
        <img
          src={SousChefLogo}
          style={{ maxWidth: '300px', width: '100%', height: 'auto' }}
          alt="Sous Chef Logo"
        />
      </Box>
    )
  }

  const navItems = [
    { icon: <HomeIcon />, label: 'Home', path: '/home' },
    { icon: <RestaurantIcon />, label: 'Sous Chef', path: '/sous-chef' },
    { icon: <LocalDiningIcon />, label: 'Nutritionist', path: '/nutritionist' },
    { icon: <MenuBookIcon />, label: 'Recipes', path: '/recipes' },
    { icon: <InventoryIcon />, label: 'Inventory', path: '/inventory' },
  ];

  // Navigation bar for authenticated pages
  return (
    <AppBar position="sticky" color="primary" elevation={0}>
      <Toolbar sx={{ minHeight: { xs: 56, sm: 64 }, px: { xs: 2, sm: 3 } }}>
        {/* Logo */}
        <Box
          component="a"
          href="/home"
          sx={{
            display: 'flex',
            alignItems: 'center',
            textDecoration: 'none',
            mr: { xs: 2, md: 4 }
          }}
        >
          <img
            src={SousChefLogo}
            style={{ height: '40px', width: 'auto' }}
            alt="Sous Chef"
          />
          {!isMobile && (
            <Typography
              variant="h6"
              sx={{
                ml: 1.5,
                color: 'white',
                fontWeight: 700,
                letterSpacing: '-0.01em'
              }}
            >
              Sous Chef
            </Typography>
          )}
        </Box>

        {/* Main Navigation */}
        <Box sx={{ display: 'flex', gap: 0.5, flex: 1 }}>
          {navItems.map((item) => (
            <IconButton
              key={item.path}
              href={item.path}
              size="small"
              sx={{
                color: 'white',
                borderRadius: 2,
                px: { xs: 1, md: 1.5 },
                '&:hover': {
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                },
                display: 'flex',
                flexDirection: { xs: 'column', md: 'row' },
                gap: { xs: 0, md: 0.5 },
              }}
            >
              {item.icon}
              <Typography
                variant="caption"
                sx={{
                  fontSize: { xs: '0.65rem', md: '0.75rem' },
                  fontWeight: 500,
                  display: { xs: 'block', sm: 'block' }
                }}
              >
                {item.label}
              </Typography>
            </IconButton>
          ))}
        </Box>

        {/* Right side actions */}
        <Box sx={{ display: 'flex', gap: 0.5, ml: 2 }}>
          <IconButton
            href="/settings"
            size="small"
            sx={{
              color: 'white',
              '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.1)' },
            }}
          >
            <SettingsIcon fontSize="small" />
          </IconButton>
          <IconButton
            href="/logout"
            size="small"
            sx={{
              color: 'white',
              '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.1)' },
            }}
          >
            <LogoutIcon fontSize="small" />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  )
}
