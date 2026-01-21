import asyncio
import argparse
from fastapi import status, HTTPException
import requests
import time
from app.core.config import settings
from app.models import Game
from app.db.session import get_session
from datetime import datetime
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from pydantic import HttpUrl

igdb_auth_url = "https://id.twitch.tv"
igdb_api_url = "https://api.igdb.com"


def get_igdb_token(client_id: str, client_secret: str) -> str:
    """Get an OAuth token from IGDB."""
    query_params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    response = requests.post(f"{igdb_auth_url}/oauth2/token", params=query_params)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get IGDB token.",
        )
    return response.json()["access_token"]


def get_data_from_igdb(
    bearer_token: str, client_id: str, limit: int, offset: int, filters: str = ""
) -> list[dict]:
    """Fetch game data from IGDB API."""
    headers = {"Authorization": f"Bearer {bearer_token}", "Client-ID": client_id}
    body = (
        f"fields name, summary, cover.url, first_release_date, genres.name, platforms.name, "
        f"involved_companies.company.name, id; limit {limit}; offset {offset}; {filters};"
    )
    response = requests.post(f"{igdb_api_url}/v4/games", headers=headers, data=body)

    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized to reach IGDB game data.",
        )
    elif response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reach IGDB game data.",
        )

    return response.json()


def process_game_data(games: list[dict]) -> list[Game]:
    """Convert raw IGDB data to Game models."""
    game_models = []
    for game in games:
        # Build cover image URL
        cover_image = None
        if game.get("cover") and game["cover"].get("url"):
            cover_url = game["cover"]["url"].replace("t_thumb", "t_cover_big")
            cover_image = HttpUrl(url=f"https:{cover_url}")

        # Build game model
        game_models.append(
            Game(
                title=game["name"],
                summary=game.get("summary"),
                cover_image=cover_image,
                release_date=(
                    datetime.fromtimestamp(game["first_release_date"])
                    if game.get("first_release_date")
                    else None
                ),
                igdb_id=game["id"],
            )
        )
    return game_models


async def upsert_games(session: AsyncSession, games: list[Game]) -> int:
    """Insert or update games in the database."""
    inserted_count = 0

    for game in games:
        # Check if game already exists by igdb_id
        stmt = select(Game).where(Game.igdb_id == game.igdb_id)
        result = await session.exec(stmt)
        existing_game = result.one_or_none()

        if existing_game:
            # Update existing game
            existing_game.title = game.title
            existing_game.summary = game.summary
            existing_game.cover_image = game.cover_image
            existing_game.release_date = game.release_date
            session.add(existing_game)
        else:
            # Insert new game
            session.add(game)
            inserted_count += 1

    await session.commit()
    return inserted_count


class GameImporter:
    """Handles bulk import of games from IGDB."""

    def __init__(self):
        self.token: str = ""

    def _get_token(self) -> str:
        """Get or refresh the IGDB token."""
        if not self.token:
            self.token = get_igdb_token(
                settings.IGDB_CLIENT_ID, settings.IGDB_CLIENT_SECRET
            )
        return self.token

    async def fetch_and_store_games(
        self, session: AsyncSession, limit: int, offset: int
    ) -> int:
        """Fetch games from IGDB and store them in the database."""
        try:
            raw_game_data = get_data_from_igdb(
                self._get_token(),
                settings.IGDB_CLIENT_ID,
                limit,
                offset,
                "where rating_count > 10; sort rating_count desc;",
            )
        except HTTPException as exc:
            if exc.status_code == status.HTTP_401_UNAUTHORIZED:
                # Token expired, get a new one and retry
                self.token = ""
                raw_game_data = get_data_from_igdb(
                    self._get_token(),
                    settings.IGDB_CLIENT_ID,
                    limit,
                    offset,
                    "where rating_count > 10; sort rating_count desc;",
                )
            else:
                raise exc

        # Process and upsert games
        game_models = process_game_data(raw_game_data)
        inserted_count = await upsert_games(session, game_models)

        return inserted_count

    async def bulk_import(self, total_games: int, batch_size: int):
        """Import games in batches."""
        offset = 0
        total_inserted = 0

        print(f"Starting bulk import of {total_games} games...")

        # Get a proper database session using async for
        async for session in get_session():
            while offset < total_games:
                current_batch_size = min(batch_size, total_games - offset)

                print(
                    f"Fetching games {offset + 1} to {offset + current_batch_size}..."
                )

                inserted = await self.fetch_and_store_games(
                    session, current_batch_size, offset
                )

                total_inserted += inserted
                print(f"  → Inserted {inserted} new games ({total_inserted} total)")

                offset += current_batch_size

                # Rate limiting
                time.sleep(0.25)

        print(f"\nBulk import completed! Total new games: {total_inserted}")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="LeadrBoard Games Importer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app/import_games.py                          # Import 1000 games (default)
  python app/import_games.py --total-games 5000       # Import 5000 games
  python app/import_games.py --batch-size 50 --total-games 500  # Custom batch size
        """,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        help="Number of games to fetch per batch (default: 100)",
        default=100,
    )

    parser.add_argument(
        "--total-games",
        type=int,
        help="Total number of games to import (default: 1000)",
        default=1000,
    )

    return parser.parse_args()


async def main():
    """Main function for importing games."""
    args = parse_arguments()
    importer = GameImporter()
    await importer.bulk_import(total_games=args.total_games, batch_size=args.batch_size)


if __name__ == "__main__":
    asyncio.run(main())
