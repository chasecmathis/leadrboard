import { Router } from 'express';
import { addGameReview } from '../controllers/gameController';
import { authMiddleware } from '../middleware/authMiddleware';

const router = Router();


router.post('/:id/review', authMiddleware, addGameReview);  // Add a review

export default router;
