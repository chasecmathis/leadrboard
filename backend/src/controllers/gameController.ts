import { Response, Request } from "express";
import { Game } from "../models/Game";
import { AuthRequest } from "../middleware/authMiddleware";
import mongoose from "mongoose";
 

export const getGames = async(_: Request, res: Response) => {
    try {
        const game = await Game.find();
        res.json(game);
    } catch(err: any) {
        res.status(500).json({msg: err.message});
    }
}

export const getGameById = async(req: Request, res: Response) => {
    try {
        const game = await Game.findById(req.params.id);
        if (!game) return res.status(404).json({msg: 'Game not found'});

        res.json(game);
    } catch(err: any) {
        res.status(500).json({msg: err.message})
    }
}

export const addGameReview = async(req: AuthRequest, res: Response) => {
    if (!req.user) return res.status(400).json({msg: 'Invalid user'})

    const { rating, subject, description } = req.body;
    const gameId = req.params.id;
    const userId = new mongoose.Schema.Types.ObjectId(req.user);

    try {
        const game = await Game.findById(gameId);
        if (!game) return res.status(404).json({msg: 'Game not found'});

        const alreadyReviewed = game.ratings.find((r) => r.user.toString() == userId.toString());
        if (alreadyReviewed) return res.status(404).json({msg: 'Game already reviewed'});

        const newRating = {user: userId, rating, subject, description}
        game.ratings.push(newRating);
        game.averageRating = game.ratings.reduce((sum, item) => item.rating + sum, 0) / game.ratings.length;

        await game.save();
        res.status(201).json(game)
    } catch (err: any) {
        res.status(500).json({msg: err})
    }
}