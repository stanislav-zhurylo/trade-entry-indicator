import calendar

from datetime import datetime, timedelta, timezone

from enums import TimeFrame

def __previous_moment(seconds: int) -> datetime:
    now_date_time = datetime.now(timezone.utc)
    min_date_time = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    seconds_since_epoch = (now_date_time - min_date_time).total_seconds()
    seconds_since_epoch -= (seconds_since_epoch % seconds)
    return min_date_time + timedelta(seconds=seconds_since_epoch)

def seconds(time_frame: TimeFrame) -> int:
    match time_frame:
        case TimeFrame.MIN_3:
            return 3 * 60
        case TimeFrame.MIN_5:
            return 5 * 60
        case TimeFrame.MIN_10:
            return 10 * 60
        case TimeFrame.MIN_15:
            return 15 * 60
        case TimeFrame.MIN_30:
            return 30 * 60
        case TimeFrame.HOUR_1:
            return 60 * 60
        case _:
            return 60

def previous_moment(time_frame: TimeFrame) -> datetime:
    return __previous_moment(seconds(time_frame))

def unix_millis(date_time: datetime) -> int:
    if date_time.tzinfo is None:
        date_time = dt.replace(tzinfo=timezone.utc) 
    return int(date_time.timestamp() * 1000)