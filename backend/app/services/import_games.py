import asyncio
import argparse
import httpx
from datetime import datetime
from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.db.session import get_async_engine  # Import the engine directly
from app.models import Game, Genre, Platform


class GameImporter:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url="https://api.igdb.com/v4")
        self.auth_client = httpx.AsyncClient(base_url="https://id.twitch.tv/oauth2")
        self.token: Optional[str] = None

    async def _get_token(self):
        if not self.token:
            print("🔑 Fetching new IGDB Access Token...")
            resp = await self.auth_client.post(
                "/token",
                params={
                    "client_id": settings().IGDB_CLIENT_ID,
                    "client_secret": settings().IGDB_CLIENT_SECRET,
                    "grant_type": "client_credentials",
                },
            )
            resp.raise_for_status()
            self.token = resp.json()["access_token"]
        return self.token

    async def fetch_igdb_data(self, query) -> List[dict]:
        token = await self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Client-ID": settings().IGDB_CLIENT_ID,
        }

        response = await self.client.post("/games", headers=headers, data=query)

        if response.status_code == 401:
            self.token = None
            return await self.fetch_igdb_data(query)

        if response.status_code != 200:
            print(f"❌ IGDB Error {response.status_code}: {response.text}")
            response.raise_for_status()
        return response.json()

    @staticmethod
    async def bulk_upsert_metadata(
        session: AsyncSession, model_class, items: List[dict]
    ):
        if not items:
            return {}

        ids = [i["id"] for i in items]
        stmt = select(model_class).where(model_class.id.in_(ids))
        result = await session.exec(stmt)
        existing = {obj.id: obj for obj in result.all()}

        added_count = 0
        for item in items:
            if item["id"] not in existing:
                new_obj = model_class(id=item["id"], name=item["name"])
                session.add(new_obj)
                existing[item["id"]] = new_obj
                added_count += 1

        if added_count > 0:
            await session.flush()  # Send to DB but don't commit yet
        return existing

    async def process_batch(self, session: AsyncSession, raw_games: List[dict]) -> int:
        # Extract and Upsert Genres/Platforms
        all_genres = {}
        all_platforms = {}
        print(raw_games)
        for g in raw_games:
            for gen in g.get("genres", []):
                all_genres[gen["id"]] = gen
            for plat in g.get("platforms", []):
                all_platforms[plat["id"]] = plat

        genre_map = await self.bulk_upsert_metadata(
            session, Genre, list(all_genres.values())
        )
        platform_map = await self.bulk_upsert_metadata(
            session, Platform, list(all_platforms.values())
        )

        # Bulk fetch existing games
        igdb_ids = [g["id"] for g in raw_games]
        stmt = select(Game).where(Game.igdb_id.in_(igdb_ids))
        result = await session.exec(stmt)
        existing_games = {g.igdb_id: g for g in result.all()}

        new_count = 0
        for data in raw_games:
            cover_url = None
            if "cover" in data and "url" in data["cover"]:
                url = data["cover"]["url"].replace("t_thumb", "t_cover_big")
                cover_url = f"https:{url}"

            game_fields = {
                "title": data["name"],
                "summary": data.get("summary"),
                "cover_image": cover_url,
                "release_date": (
                    datetime.fromtimestamp(data["first_release_date"])
                    if "first_release_date" in data
                    else None
                ),
                "igdb_id": data["id"],
            }

            if data["id"] in existing_games:
                game_obj = existing_games[data["id"]]
                for key, val in game_fields.items():
                    setattr(game_obj, key, val)
            else:
                game_obj = Game(**game_fields)
                session.add(game_obj)
                new_count += 1

            # Update M2M Relationships
            game_obj.genres = [
                genre_map[gen["id"]]
                for gen in data.get("genres", [])
                if gen["id"] in genre_map
            ]
            game_obj.platforms = [
                platform_map[plat["id"]]
                for plat in data.get("platforms", [])
                if plat["id"] in platform_map
            ]

        await session.commit()
        return new_count

    async def run_import(self, total: Optional[int] = None, batch_size: int = 100):
        imported_so_far = 0

        print(f"🚀 Starting Import (Target: {'All' if total is None else total})")

        # Use a direct AsyncSession context manager for standalone scripts
        async with AsyncSession(get_async_engine()) as session:
            while True:
                limit = (
                    batch_size
                    if total is None
                    else min(batch_size, total - imported_so_far)
                )
                if limit <= 0:
                    break

                # Query formatting is critical for IGDB
                query = (
                    f"fields name, summary, cover.url, first_release_date, genres.name, platforms.name, id; "
                    f"limit {limit}; "
                    f"offset {imported_so_far}; "
                    f"sort rating_count desc;"
                )

                print(f"📡 Fetching batch after {imported_so_far} games...")
                batch = await self.fetch_igdb_data(query)

                if not batch:
                    print("Empty batch received. Ending import.")
                    break

                new_games_count = await self.process_batch(session, batch)
                imported_so_far += len(batch)

                print(
                    f"✅ Processed {len(batch)} games ({new_games_count} were new). Total: {imported_so_far}"
                )

                if total and imported_so_far >= total:
                    break

                # Respect rate limits (4 requests per second for Free Tier)
                await asyncio.sleep(0.25)

        print("🏁 Import Complete!")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--all", action="store_true", help="Pull every single game from IGDB"
    )
    parser.add_argument(
        "--count", type=int, default=1000, help="Number of games to pull if not --all"
    )
    args = parser.parse_args()

    importer = GameImporter()
    target = None if args.all else args.count
    try:
        await importer.run_import(total=target)
    finally:
        # Clean up clients
        await importer.client.aclose()
        await importer.auth_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
