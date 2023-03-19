import os
import secrets
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

ENV: str = os.getenv('ENV', 'production').lower()
if ENV not in ('production', 'development', 'testing'):
    raise ValueError(
        f'ENV={ENV} is not valid. ' "It should be 'production', 'development' or 'testing'"
    )
DEBUG: bool = ENV != 'production'
TESTING: bool = ENV == 'testing'

LOG_LEVEL: str = os.getenv('LOG_LEVEL') or (DEBUG and 'DEBUG') or 'INFO'
os.environ['LOGURU_DEBUG_COLOR'] = '<fg #777>'

DB_PASSWORD = os.environ['DB_PASSWORD']
DB_HOST = os.environ['DB_HOST']
DB_PORT = os.environ['DB_PORT']
DB_NAME = (TESTING and 'test_' or '') + os.environ['DB_NAME']
DATABASE_URL = f'postgresql://postgres:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_URL = os.getenv('REDIS_URL') or f'redis://{REDIS_HOST}:{REDIS_PORT}'

SECRET_KEY = bytes(os.getenv('SECRET_KEY', ''), 'utf-8') or secrets.token_bytes(32)
SESSION_ID_LENGTH = int(os.getenv('SESSION_ID_LENGTH', 16))  # noqa: PLW1508
SESSION_LIFETIME = int(timedelta(days=7).total_seconds())

PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', 15))  # noqa: PLW1508
PASSWORD_MIN_VARIETY = int(os.getenv('PASSWORD_MIN_VARIETY', 5))  # noqa: PLW1508
