from aiohttp import ClientSession, web
from aiojobs.aiohttp import get_scheduler_from_app, setup
from asyncio import sleep
from orjson import dumps
import ocfr
import ocso
import scso


headers = {'Content-Security-Policy': 'object-src \'none\'; frame-ancestors \'none\';'}
ocfr_calls: list[ocfr.Call] = []
ocso_calls: list[ocso.Call] = []
scso_calls: list[scso.Call] = []
orjson_encoder = lambda x: dumps(x, default=str).decode('utf-8')
routes = web.RouteTableDef()
session = web.AppKey('session', ClientSession)


# Signals

async def on_startup(app: web.Application):
    app[session] = ClientSession(
        json_serialize=orjson_encoder,
    )
    
    scheduler = get_scheduler_from_app(app)
    assert scheduler is not None

    await scheduler.spawn(get_active_calls_loop(app))


async def on_cleanup(app: web.Application):
    await app[session].close()


# Background tasks

async def get_active_calls_loop(app: web.Application):
    global ocfr_calls, ocso_calls, scso_calls

    while True:
        try:
            ocfr_calls = await ocfr.get_active_calls(app[session])
            app.logger.info('Fetched list of active OCFR calls (%d)', len(ocfr_calls))

            ocso_calls = await ocso.get_active_calls(app[session])
            app.logger.info('Fetched list of active OCSO calls (%d)', len(ocso_calls))

            scso_calls = await scso.get_active_calls(app[session])
            app.logger.info('Fetched list of active SCSO calls (%d)', len(scso_calls))
        except Exception:
            app.logger.exception('Failed to fetch active calls')

        await sleep(120)

# Routes

@routes.get('/')
async def get_index(request: web.Request) -> web.FileResponse:
    return web.FileResponse('./static/index.html', headers=headers)

@routes.get('/active-calls')
async def active_calls(request: web.Request) -> web.Response:
    global ocfr_calls, ocso_calls

    return web.json_response(
        {
            'ocfr': ocfr_calls,
            'ocso': ocso_calls,
            'scso': scso_calls,
        },
        dumps=orjson_encoder,
    )


# Init

def init(*args, **kwargs) -> web.Application:
    app = web.Application()

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    app.add_routes(routes)
    app.router.add_static('/', './static')

    setup(app)

    return app


async def init_async() -> web.Application:
    # async `init` wrapper for gunicorn
    return init()


if __name__ == '__main__':
    web.run_app(init_async(), port=3000)
