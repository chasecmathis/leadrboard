import {  Router } from 'express';
import { registerUser, loginUser } from '../controllers/authController';

const router = Router();

// POST /api/users/register: Register a new user
router.post('/register', registerUser);

// POST /api/users/login: Log in a user
router.post('/login', loginUser);

export default router;
