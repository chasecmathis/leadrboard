import { Request, Response } from "express";
import { User } from "../models/User";
import bcrypt from 'bcryptjs'
import jwt from 'jsonwebtoken'

export const registerUser = async(req: Request, res: Response) => {
    const { username, password } = req.body;
    try {
        let user = await User.findOne({username});
        if (user) return res.status(401).json({msg: 'User already exists'});

        const hashedPassword = await bcrypt.hash(password, 10);
        user = new User({username, password: hashedPassword});
        await user.save();

        const token = jwt.sign({id: user._id}, process.env.JWT_SECRET as string, {expiresIn: '1h'});
        res.json({token, user: {id: user._id, username}});
    } catch(err: any) {
        res.status(500).json({msg: err.message});
    }
}

export const loginUser = async(req: Request, res: Response) => {
    const {username, password} = req.body;
    try {
        let user = await User.findOne({username});
        if (!user) return res.status(400).json({msg: 'Invalid credentials'});

        const isMatch = await bcrypt.compare(user.password, password);
        if(!isMatch) return res.status(400).json({msg: 'Invalid credentials'});

        const token = jwt.sign({id: user._id}, process.env.JWT_SECRET as string, {expiresIn: '1h'});
        res.json({token, user: {id: user._id, username}});
    } catch(err: any) {
        res.status(500).json({msg: err.message});
    }
}