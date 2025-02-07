from motor.motor_asyncio import AsyncIOMotorClient
from config import get_settings

settings = get_settings()


class Database:
    client: AsyncIOMotorClient = None

    def get_db(self):
        return self.client[settings.database_name]

    def connect_to_db(self):
        self.client = AsyncIOMotorClient(settings.mongodb_url)

    def close_db_connection(self):
        self.client.close()


db = Database()
