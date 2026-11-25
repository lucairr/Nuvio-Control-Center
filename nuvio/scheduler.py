"""Tiny portable daily scheduler for Docker (systemd/launchd/Task Scheduler elsewhere).
This process executes ONLY the safe, pre-defined `auto` updater action.
"""
import datetime
import os
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from . import core


def timezone():
    name = os.getenv('TZ', 'UTC')
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        raise SystemExit(f'Invalid TZ={name!r}. Use an IANA timezone such as Europe/Rome.')


def should_run(now, last_date):
    return (now.hour == 19 and now.minute == 30 and last_date != now.date())


def main():
    tz = timezone()
    print('Nuvio daily scheduler ready (19:30, timezone ' + str(tz) + ')', flush=True)
    last_date = None
    while True:
        current = datetime.datetime.now(tz)
        if should_run(current, last_date):
            last_date = current.date()
            try:
                core.perform('auto')
            except Exception as exc:
                print('Daily check failed: ' + str(exc)[:300], flush=True)
        time.sleep(10)

if __name__ == '__main__':
    main()
