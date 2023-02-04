from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from . import config
from .resources import shutdown, startup
from .routers import hello, organization, repository, user

routers = [
    hello.router,
    user.router,
    organization.router,
    repository.router,
]

app = FastAPI(
    title='GitClub FastAPI',
    debug=config.DEBUG,
    default_response_class=ORJSONResponse,
    on_startup=(startup,),
    on_shutdown=(shutdown,),
)

for router in routers:
    app.include_router(router)
