import React, { useState } from 'react';
import { useNavigate } from 'react-router';
import { useApi } from './useApi';
import {
    Card,
    CardContent,
    Button,
    Typography,
    TextField,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Stack,
    Alert
} from '@mui/material';
import DeleteForeverIcon from '@mui/icons-material/DeleteForever';

const DeleteComponent = () => {
    const navigate = useNavigate();
    const { api } = useApi();
    const [dialogOpen, setDialogOpen] = useState(false);
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");

    function handleDelete(e) {
        e.preventDefault();

        api.deleteUser({ username, password })
            .then((result) => {
                alert("Successfully deleted account!");
                navigate("/login");
            })
            .catch((error) => {
                alert("Invalid Credentials! Could not delete account!");
                console.log(error);
            })
            .finally(() => {
                setDialogOpen(false);
                setUsername("");
                setPassword("");
            });
    }

    function showDeleteDialog(e) {
        e.preventDefault();
        setDialogOpen(true);
    }

    function handleCancel() {
        setDialogOpen(false);
        setUsername("");
        setPassword("");
    }

    return (
        <Card sx={{ height: '100%' }}>
            <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 4 }}>
                <Button
                    variant="contained"
                    color="error"
                    size="large"
                    startIcon={<DeleteForeverIcon />}
                    onClick={showDeleteDialog}
                >
                    Delete Account
                </Button>

                <Dialog open={dialogOpen} onClose={handleCancel} maxWidth="xs" fullWidth>
                    <DialogTitle>Delete Account</DialogTitle>
                    <DialogContent>
                        <Alert severity="warning" sx={{ mb: 2 }}>
                            This action cannot be undone. Please confirm your credentials to delete your account.
                        </Alert>
                        <Stack spacing={2} component="form" onSubmit={handleDelete}>
                            <TextField
                                name="user"
                                label="Username"
                                placeholder="Enter Username"
                                fullWidth
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                autoFocus
                            />
                            <TextField
                                name="password"
                                label="Password"
                                type="password"
                                placeholder="Enter Password"
                                fullWidth
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </Stack>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={handleCancel} color="inherit">
                            Cancel
                        </Button>
                        <Button
                            onClick={handleDelete}
                            color="error"
                            variant="contained"
                            disabled={!username || !password}
                        >
                            Delete Account
                        </Button>
                    </DialogActions>
                </Dialog>
            </CardContent>
        </Card>
    );
};

export default DeleteComponent;
