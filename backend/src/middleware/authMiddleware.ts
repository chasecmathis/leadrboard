import { NextFunction, Request, Response } from "express";
import jwt from 'jsonwebtoken'

export interface AuthRequest extends Request {
    user?: string
}

export const authMiddleware = (req: AuthRequest, res: Response, next: NextFunction) => {
    const token = req.header('x-auth-token');
    if (!token) return res.status(401).json({msg: 'No token, authorization denied'});

    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET as string) as {id: string}
        req.user = decoded.id
    } catch(err) {
        res.status(401).json({msg: 'Invalid token'})
    }
}