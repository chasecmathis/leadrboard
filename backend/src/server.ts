import express from 'express';
import dotenv from 'dotenv';
import connectDB from './config/db';
import gameRoutes from './routes/gameRoutes';
import userRoutes from './routes/userRoutes';

dotenv.config();

const app = express();
app.use(express.json());

connectDB();

app.use('/api/games', gameRoutes);
app.use('/api/users', userRoutes)

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
