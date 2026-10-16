# Config precedence API

## What it does

The API starts with built-in defaults and applies configuration in this order:

1. `main.py` defaults
2. `config.<environment>.yaml` (development is the default environment)
3. `.env`
4. Operating-system environment variables beginning with `APP_`
5. `set=key=value` query parameters

The `NUM_WORKERS` variable in `.env` is an alias for `workers`. The API key is
always masked in responses. CORS is enabled so a browser-based grader can call
the endpoint from a different website.

## Run it locally

1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Install the packages with `pip install -r requirements.txt`.
4. Start the service with `uvicorn main:app --reload --port 8001`.
5. Visit <http://127.0.0.1:8001/effective-config>.

With only the files in this folder, the YAML layer sets port `8654` and log
level `debug`; `.env` sets workers to `5` and debug to `false`. To check the
assigned OS environment layer locally too, start the service with:

```sh
APP_PORT=8543 APP_LOG_LEVEL=error APP_API_KEY=local-test-key uvicorn main:app --reload
```

Then the resolved values are port `8543`, workers `5`, debug `false`, and log
level `error`.

Try overrides such as:

`http://127.0.0.1:8001/effective-config?set=port=9000&set=debug=true`

The query parameters override any configured value. The API key is returned as
`"****"` regardless of its configured value.

## Deploy to Render

1. Put these project files in a GitHub repository. Do not add `.env`; it is
   excluded by `.gitignore`.
2. In Render, choose **New +** → **Blueprint** and connect that repository.
3. Render reads `render.yaml`, installs the dependencies, and starts the API.
4. Copy the service's public URL and append `/effective-config`. That is the
   URL to submit. For example, if Render gives the service
   `https://config-precedence-api.onrender.com`, submit
   `https://config-precedence-api.onrender.com/effective-config`.
5. Test fresh overrides by adding
   `?set=port=9000&set=debug=true` to that URL.
