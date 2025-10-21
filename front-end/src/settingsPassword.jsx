import React, { useState, useEffect } from 'react';
import { useApi } from './useApi';
import {
    Card,
    CardContent,
    TextField,
    Button,
    Typography,
    Stack,
    Divider,
    Box
} from '@mui/material';
import EmailIcon from '@mui/icons-material/Email';
import LockIcon from '@mui/icons-material/Lock';

const PasswordComponent = () => {
    const { api } = useApi();

    const [currentEmail, setCurrentEmail] = useState("");
    const [newEmail, setNewEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");

    useEffect(() => {
        api.getCurrentUser().then((result) => {
            setCurrentEmail(result.email)
        })
    }, [api])

    const passwordsMatch = password !== "" && password === confirmPassword;

    function publishPassword(e) {
        e.preventDefault();
        if (!passwordsMatch) return;

        api.updatePassword({ password })
            .then(() => {
                alert('Password successfully changed!');
                setPassword("");
                setConfirmPassword("");
            })
    }

    function publishEmail(e) {
        e.preventDefault();
        api.updateEmail({ email: newEmail })
            .then((result) => {
                return api.getCurrentUser();
            })
            .then((result) => {
                setCurrentEmail(result.email);
                setNewEmail("");
                alert('Email successfully changed!');
            })
    }

    return (
        <Card sx={{ height: '100%' }}>
            <CardContent>
                <Stack spacing={3} divider={<Divider />}>
                    {/* Email Section */}
                    <Box component="form" onSubmit={publishEmail}>
                        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <EmailIcon /> Email Settings
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            Current email: <strong>{currentEmail}</strong>
                        </Typography>
                        <Stack direction="row" spacing={2} alignItems="center">
                            <TextField
                                name="email"
                                type="email"
                                placeholder="Enter new email"
                                size="small"
                                fullWidth
                                value={newEmail}
                                onChange={(e) => setNewEmail(e.target.value)}
                            />
                            <Button
                                type="submit"
                                variant="contained"
                                color="primary"
                                disabled={!newEmail}
                            >
                                Change Email
                            </Button>
                        </Stack>
                    </Box>

                    {/* Password Section */}
                    <Box component="form" onSubmit={publishPassword}>
                        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <LockIcon /> Password Settings
                        </Typography>
                        <Stack spacing={2}>
                            <TextField
                                name="password"
                                type="password"
                                placeholder="Enter new password"
                                size="small"
                                fullWidth
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                            <TextField
                                name="confirmpassword"
                                type="password"
                                placeholder="Confirm password"
                                size="small"
                                fullWidth
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                error={confirmPassword !== "" && !passwordsMatch}
                                helperText={confirmPassword !== "" && !passwordsMatch ? "Passwords do not match" : ""}
                            />
                            <Button
                                type="submit"
                                variant="contained"
                                color="primary"
                                disabled={!passwordsMatch}
                                fullWidth
                            >
                                Change Password
                            </Button>
                        </Stack>
                    </Box>
                </Stack>
            </CardContent>
        </Card>
    );
};

export default PasswordComponent;