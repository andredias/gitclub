import asyncio

from databases import Database
from loguru import logger
from redis.asyncio import Redis
from tenacity import RetryError, retry, stop_after_delay, wait_exponential

from . import config

db = Database(config.DATABASE_URL, force_rollback=config.TESTING)
redis = Redis.from_url(config.REDIS_URL)


async def startup() -> None:
    show_config()
    await asyncio.gather(connect_redis(), connect_database(db))
    logger.info('started...')


async def shutdown() -> None:
    await asyncio.gather(disconnect_redis(), db.disconnect())
    logger.info('...shutdown')


def show_config() -> None:
    config_vars = {key: getattr(config, key) for key in sorted(dir(config)) if key.isupper()}
    logger.debug(config_vars)
    return


async def connect_database(database: Database) -> None:
    @retry(stop=stop_after_delay(3), wait=wait_exponential(multiplier=0.2))
    async def _connect_to_db() -> None:
        logger.debug('Connecting to the database...')
        await database.connect()

    try:
        await _connect_to_db()
    except RetryError:
        logger.error('Could not connect to the database.')
        raise


async def connect_redis() -> None:

    # test redis connection
    @retry(stop=stop_after_delay(3), wait=wait_exponential(multiplier=0.2))
    async def _connect_to_redis() -> None:
        logger.debug('Connecting to Redis...')
        await redis.set('test_connection', '1234')
        await redis.delete('test_connection')

    try:
        await _connect_to_redis()
    except RetryError:
        logger.error('Could not connect to Redis')
        raise
    return


async def disconnect_redis() -> None:
    if config.TESTING:
        await redis.flushdb()
    await redis.close()
    return
