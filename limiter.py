import os
import time

from dotenv import load_dotenv

load_dotenv()
MAX_RPM = int(os.getenv("MAX_RPM", "10"))
min_gap_seconds = 60 / MAX_RPM
last_call_time = 0.0
call_count = 0

def wait_for_slot():
    global last_call_time, call_count
    elapsed = time.time() - last_call_time
    remaining = min_gap_seconds - elapsed
    if remaining > 0:
        time.sleep(remaining)
    last_call_time = time.time()

    call_count += 1

