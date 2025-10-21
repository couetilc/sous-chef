import React from 'react';
import PasswordComponent from './settingsPassword';
import DeleteComponent from './settingsDeleteAccount';
import DietComponent from './settingsDietPreference';
import { Container, Typography, Box, Grid } from '@mui/material';

const SettingsPage = () => {
    return (
        <Container maxWidth="lg">
            <Box sx={{ py: 3 }}>
                <Typography
                    variant="h5"
                    component="h1"
                    sx={{
                        fontWeight: 600,
                        color: 'text.primary',
                        mb: 3
                    }}
                >
                    Account Settings
                </Typography>

                <Grid container spacing={2.5}>
                    <Grid item xs={12} md={4}>
                        <DietComponent />
                    </Grid>
                    <Grid item xs={12} md={8}>
                        <Grid container spacing={2.5}>
                            <Grid item xs={12}>
                                <PasswordComponent />
                            </Grid>
                            <Grid item xs={12}>
                                <DeleteComponent />
                            </Grid>
                        </Grid>
                    </Grid>
                </Grid>
            </Box>
        </Container>
    );
}

export default SettingsPage;
