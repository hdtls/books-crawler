import time

last_timestamp = -1


def snowflake(data_center_id=0, worker_id=0):
    """generate a twitter-snowflake id, based on
    https://github.com/twitter/snowflake/blob/master/src/main/scala/com/twitter/service/snowflake/IdWorker.scala
    :param: timestamp_ms time since UNIX epoch in milliseconds"""

    # twitter's snowflake parameters
    twepoch = 1288834974657
    sequence = 0
    data_center_id_bits = 5
    worker_id_bits = 5
    sequence_id_bits = 12
    sequence_mask = 1 << sequence_id_bits
    worker_id_shift = sequence_id_bits
    data_center_id_shift = sequence_id_bits + worker_id_bits
    timestamp_left_shift = sequence_id_bits + worker_id_bits + data_center_id_bits

    timestamp = _timestamp()

    global last_timestamp

    if last_timestamp > timestamp:
        raise Exception("Refusing to generate id for %i milliseocnds" % last_timestamp)

    if last_timestamp == timestamp:
        sequence = (sequence + 1) & sequence_mask
        if sequence == 0:
            timestamp = _till_next_millis(last_timestamp)
    else:
        sequence = 0

    last_timestamp = timestamp

    sid = (
        ((timestamp - twepoch) << timestamp_left_shift)
        | (data_center_id << data_center_id_shift)
        | (worker_id << worker_id_shift)
        | sequence
    )
    return sid


def _timestamp():
    return int(time.time() * 1000)


def _till_next_millis(last_timestamp):
    timestamp = _timestamp()
    while timestamp <= last_timestamp:
        timestamp = _timestamp()

    return timestamp


if __name__ == "__main__":
    print(snowflake())
