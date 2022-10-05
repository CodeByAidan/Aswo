from bot import Aswo
import asyncio
import discord
import aiohttp
import config
from utils.osu import Osu
import os
import asyncpg

discord.utils.setup_logging()

async def main():
    async with aiohttp.ClientSession() as session, asyncpg.create_pool(config.POSTGRES_URI) as pool, Aswo(session=session, pool=pool, osu=Osu(client_id=config.OSU_CLIENT_ID, client_secret=config.OSU_CLIENT_SECRET, session=session)) as bot:
        await bot.load_extension("jishaku")
        exts = [
            f"cogs.{ext if not ext.endswith('.py') else ext[:-3]}"
            for ext in os.listdir("cogs")
            if not ext.startswith("_")
        ]
        for ext in exts:
            await bot.load_extension(ext)
        await bot.start(config.TOKEN, reconnect=True)

    

asyncio.run(main())