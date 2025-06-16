# price-tracker

A FastAPI service that fetches real-time stock prices from Yahoo Finance, persists raw prices in a SQLite database, and publishes enriched price events to Kafka. A separate consumer computes a 5-point moving average for each symbol and stores the results.

## Features

* **GET `/prices/latest`**: Fetch the latest daily close for a symbol
* **POST `/prices/poll`**: Submit polling jobs (symbols, interval, provider) → `202 Accepted`
* **SQLite** tables:

  * `raw_prices` (raw fetches)
  * `processed_prices` (each event with `source` & `raw_response_id`)
  * `moving_averages` (5-point MA)
  * `job_configs` (polling jobs)
* **Kafka** integration:

  * Producer publishes to `price-events` topic:

    ```json
    {
      "symbol":"AAPL",
      "price":172.45,
      "timestamp":"2025-06-16T12:34:28.123456Z",
      "source":"yahoo_finance",
      "raw_response_id":17
    }
    ```
  * Consumer reads from `price-events`, computes/upserts MA
* **Docker Compose** for local Kafka & Zookeeper

## Prerequisites

* Python 3.10+
* Docker & Docker Compose (Compose plugin)
* Git

## Setup

1. **Clone** the repo:

   ```bash
   git clone https://github.com/ismail-ansari/price-tracker.git
   cd price-tracker
   ```
2. **Create & activate** a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # macOS/Linux
   # .venv\Scripts\Activate.ps1 # Windows PowerShell
   ```
3. **Install** dependencies:

   ```bash
   pip install --upgrade pip
   pip install fastapi uvicorn[standard] yfinance sqlalchemy kafka-python pydantic
   ```
4. **Bring up** Kafka & Zookeeper:

   ```bash
   docker compose up -d
   ```
5. **Start** the API server:

   ```bash
   uvicorn main:app --reload
   ```

## API Endpoints

### GET `/prices/latest?symbol={symbol}`

Fetch the most recent daily close.

```bash
curl "http://127.0.0.1:8000/prices/latest?symbol=AAPL"
```

**Response** (`200 OK`):

```json
{
  "symbol":"AAPL",
  "price":172.45,
  "timestamp":"2025-06-16T12:34:28.123456Z",
  "provider":"yahoo_finance"
}
```

### POST `/prices/poll`

Submit a polling job configuration.

```bash
curl -i -X POST http://127.0.0.1:8000/prices/poll \
  -H "Content-Type: application/json" \
  -d '{
    "symbols":["AAPL","MSFT"],
    "interval":60,
    "provider":"yahoo_finance"
  }'
```

**Response** (`202 Accepted`):

```json
{
  "job_id":"poll_1",
  "status":"accepted",
  "config":{"symbols":["AAPL","MSFT"],"interval":60}
}
```

## Inspecting the Database

### Raw Prices

```bash
python show_raw.py
```

### Processed Prices

```bash
python show_processed.py
```

Prints each `ProcessedPrice` with fields:

* `symbol`, `price`, `timestamp`, `source`, `raw_response_id`

### Moving Averages

```bash
python show_ma.py
```

### Job Configs

```bash
python show_jobs.py
```

## Kafka Console Consumer

To replay enriched events:

```bash
docker compose exec kafka \
  kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic price-events \
    --from-beginning \
    --property print.value=true
```
## Architecture Diagram

```mermaid
flowchart LR
  subgraph API
    A[FastAPI\n(GET/POST)]
  end
  subgraph DB
    B[SQLite\nraw_prices]
    F[SQLite\nmoving_averages]
    G[SQLite\nprocessed_prices]
    H[SQLite\njob_configs]
  end
  subgraph KafkaCluster
    C[Producer]
    D[price-events Topic]
    E[Consumer]
  end

  A -->|writes raw→DB| B
  A -->|publishes→Producer| C
  C -->|to topic| D
  D -->|consumes→Consumer| E
  E -->|upserts MA→DB| F
  E -->|logs processed→DB| G
  A -->|accepts poll→DB| H