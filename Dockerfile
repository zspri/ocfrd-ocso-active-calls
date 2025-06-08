FROM "python:3.12"
ADD . /app
WORKDIR /app
RUN pip3 install -r /app/requirements.txt -U
RUN pip3 install uvloop
CMD ["gunicorn", "main:init_async", "-b", "0.0.0.0:3000", "--worker-class", "aiohttp.GunicornUVLoopWebWorker"]
