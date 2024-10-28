import mongoose, { Schema, Document } from "mongoose";

export interface IGame extends Document {
    title: string,
    description?: string,
    releaseDate?: Date,
    genre: string[],
    platform: string[],
    ratings: Array<{
        user: Schema.Types.ObjectId; 
        rating: number;
        subject: string;
        description: string;
    }>,
    averageRating?: number
}



const gameSchema: Schema = new Schema({
    title: {type: String, required: true},
    description: String,
    releaseDate: Date,
    genre: [String],
    platform: [String],
    ratings: [
        {
            user: { type: Schema.Types.ObjectId, ref: 'User', required: true },
            rating: { type: Number, required: true },
            subject: {type: String, required: true},
            description: {type: String, required: true}
        }
    ],
    averageRating: Number
}, { timestamps: true })

export const Game = mongoose.model<IGame>('Game', gameSchema)