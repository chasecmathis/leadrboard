from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.models import Review
from typing import Sequence
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

class GameRecommendation:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _fetch_data(self):
        stmt = select(Review)
        result = await self.session.exec(stmt)
        reviews: Sequence[Review] = result.all()


        data = [{"user_id": r.user_id, "game_id": r.game_id, "rating": r.rating} for r in reviews]
        return pd.DataFrame(data)

    async def generate_recommendations(self, target_user_id: int, num_recommendations: int):
        df = await self._fetch_data()

        # Not enough data to generate recommendations
        if df.empty or target_user_id not in df["user_id"].values:
            return []

        # Create User-Item matrix (Pivot Table)
        # Rows = Users, Columns = Games, Values = Ratings
        user_game_matrix = df.pivot_table(index="user_id", columns="game_id", values="rating")
        # Fill missing ratings with 0 (they haven't rated that game)
        user_game_matrix_filled = user_game_matrix.fillna(0)

        # Create a square matrix comparing every user to every user (calculate similarity)
        user_similarity = cosine_similarity(user_game_matrix_filled)
        user_similarity_df = pd.DataFrame(user_similarity, index=user_game_matrix_filled.index, columns=user_game_matrix_filled.index)

        # Get similarity scores for the current user
        similar_users = user_similarity_df[target_user_id].drop(target_user_id).sort_values(ascending=False)

        # Select top 5 most similar users
        top_similar_users = similar_users.head(10).index.tolist()

        # Games the target user has already rated (to exclude them)
        user_rated_games = set(df[df['user_id'] == target_user_id]['game_id'])

        recommendations = {}
        for similar_user in top_similar_users:
            # Get high-rated games from this similar user
            top_games = df[
                (df['user_id'] == similar_user) &
                (df['rating'] >= 7.0)
                ]

            for _, row in top_games.iterrows():
                game_id = int(row['game_id'])
                if game_id not in user_rated_games:
                    # Simple scoring: Add similarity score to recommendation weight
                    # (This prioritizes games liked by *very* similar users)
                    sim_score = user_similarity_df.loc[target_user_id, similar_user] * row['rating']
                    recommendations[game_id] = recommendations.get(game_id, 0) + sim_score

        # Sort by weight and return Game IDs
        recommended_game_ids = sorted(recommendations, key=recommendations.get, reverse=True)[:num_recommendations]

        return recommended_game_ids


