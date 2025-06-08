# OCSO Active Calls Map

A simple full-stack web application that periodically fetches a list of [Dispatched Calls for Service](https://www.ocso.com/en-us/calls-for-service) from the Orange County, FL Sheriff's Office.
Results are then displayed on a map.

## Development

```sh
python3 -m pip install -r requirements.txt -U
python3 -m pip install aiohttp-devtools
GOOGLE_MAPS_API_KEY="..." python -m aiohttp.web -P 3000 main:init
```

## Production

```sh
python3 -m pip install -r requirements.txt -U
python3 -m pip install uvloop
GOOGLE_MAPS_API_KEY="..." gunicorn main:init_async -b 0.0.0.0:3000 --worker-class aiohttp.GunicornUVLoopWebWorker
```

## With Docker

```sh
docker build -t zspri/ocso-active-calls-map .
docker run -p 3000 zspri/ocso-active-calls-map
```
