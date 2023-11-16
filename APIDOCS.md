
# API Documentation

## Get API Version

### Endpoint

GET /api/v

### Description

Access API version.

### Request

- Method: `GET`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {
        "version": "1.0.0"
      },
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```

## Get API Status

### Endpoint

GET /api/status

### Description

Access API status.

### Request

- Method: `GET`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {
        "api_status": "online"
      },
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```

## Create a Stripe Checkout Session

### Endpoint

POST /api/create-checkout-session

### Description

Creates a Stripe Checkout Session.

### Request

- Method: `POST`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": "Stripe Checkout Session object",
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```

## Register User

### Endpoint

POST /api/register

### Description

Registers a new user.

### Request

- Method: `POST`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {},
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```

## User Login

### Endpoint

POST /api/login

### Description

Logs in a user.

### Request

- Method: `POST`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {},
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```

## User Logout

### Endpoint

POST /api/logout

### Description

Logs out a user.

### Request

- Method: `POST`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {},
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```

## Get User

### Endpoint

GET /api/user/<int:user_id>

### Description

Get user information.

### Request

- Method: `GET`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {
        "user_id": 012345
      },
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```

## Add User

### Endpoint

POST /api/user/add

### Description

Add a new user.

### Request

- Method: `POST`
- Body: User data

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {},
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```

## Update User

### Endpoint

POST /api/user/update

### Description

Update user information.

### Request

- Method: `POST`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {},
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```

## Get User's Connected Exchanges

### Endpoint

GET /api/exchanges/<int:user_id>

### Description

Get the connected exchanges for a user.

### Request

- Method: `GET`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {
        "user_id": 012345
      },
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```

## Simulate GRID Trading Strategy on Historical Data

### Endpoint

POST /api/grid-trading/simulate

### Description

Simulate a GRID trading strategy on historical data.

### Request

- Method: `POST`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {},
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```

## Get Genetically Optimized Parameters from Backtesting

### Endpoint

GET /api/grid-trading/optimizations

### Description

Get genetically optimized parameters for a GRID trading bot.

### Request

- Method: `GET`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {},
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```

## Add a GRID Trading Bot

### Endpoint

POST /api/grid-trading/bots/add

### Description

Add a new GRID trading bot.

### Request

- Method: `POST`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {},
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```

## Start a GRID Trading Bot

### Endpoint

POST /api/grid-trading/bots/start

### Description

Start a GRID trading bot.

### Request

- Method: `POST`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {},
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
    "status": "failed",
    "message": "Internal Server Error: {error_message}",
    "code": 500
    }
    ```

## Pause a GRID Trading Bot

### Endpoint

POST /api/grid-trading/bots/pause

### Description

Pause a GRID trading bot.

### Request

- Method: `POST`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {},
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```

## Resume a GRID Trading Bot

### Endpoint

POST /api/grid-trading/bots/resume

### Description

Resume a GRID trading bot.

### Request

- Method: `POST`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {},
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```

## Stop a GRID Trading Bot

### Endpoint

POST /api/grid-trading/bots/stop

### Description

Stop a GRID trading bot.

### Request

- Method: `POST`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {},
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```

## Update a GRID Trading Bot

### Endpoint

PUT /api/grid-trading/bots/update

### Description

Update a GRID trading bot.

### Request

- Method: `PUT`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {},
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```

## Get a GRID Trading Bot

### Endpoint

GET /api/grid-trading/bots/<int:grid_bot_id>

### Description

Get information about a GRID trading bot.

### Request

- Method: `GET`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {
        "grid_bot_id": 012345
      },
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```

## Remove a GRID Trading Bot

### Endpoint

DELETE /api/grid-trading/bots/remove

### Description

Remove a GRID trading bot.

### Request

- Method: `DELETE`

### Response

- Success: 200 OK
  - Body:
    ```json
    {
      "status": "success",
      "data": {},
      "message": "",
      "code": 200,
      "meta": {}
    }
    ```
- Failure: 500 Internal Server Error
  - Body:
    ```json
    {
      "status": "failed",
      "message": "Internal Server Error: {error_message}",
      "code": 500
    }
    ```
