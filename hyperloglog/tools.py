import redis


def get_redis_conn():
    return redis.Redis(host="localhost", port=6379)


def gen_batch_elem_name(elem_prefix, elem_cnt):
    keys = []
    for i in range(elem_cnt):
        keys.append(f"{elem_prefix}{i}")
    return keys


def batch_add(key, value_prefix, value_cnt):
    r = get_redis_conn()
    for i in range(value_cnt):
        v = f"{value_prefix}{i}"
        r.pfadd(key, v)


def dump_header(key):
    r = get_redis_conn()
    v = r.getrange(key, 0, 15)
    magic, encoding, card = v[:4], v[4], v[8:]
    print(f"magic: {magic.decode()}")
    print(f"encoding: {encoding} - {'HLL_DENSE' if encoding == 0 else 'HLL_SPARSE'}")
    print(f"card: {card}")
    valid_cache = card[7] & (1 << 7) == 0
    print(f"- valid_cache: {valid_cache}")
    if valid_cache:
        card_val = card[0] | card[1] << 8 | card[2] << 16 | card[3] << 24 | card[4] << 32 | card[5] << 40 | \
                   card[6] << 48 | card[7] << 56
        print(f"- cached_number: {card_val}")


def parse_dense_registers(key):
    r = get_redis_conn()
    v = r.getrange(key, 16, -1)

    def bytes_to_registers(b):
        assert len(b) % 3 == 0
        ints = []
        for i in range(0, len(b), 3):
            ints.append(b[i] & 0b00111111)
            ints.append((b[i] >> 6) | (b[i + 1] & 0b00001111) << 2)
            ints.append((b[i + 1] >> 4) | ((b[i + 2] & 0b11) << 4))
            ints.append(b[i + 2] >> 2)
        return ints

    return bytes_to_registers(v)


def parse_sparse_registers(key):
    r = get_redis_conn()
    v = r.get(key)
    v = v[16:]
    i = 0
    while True:
        flag = (v[i] & 0b11000000) >> 6
        if flag == 0b00:
            print("ZERO:", v[i] & 0b00111111 + 1)
            i += 1
        elif flag == 0b01:
            print("XZERO:", ((v[i] & 0b00111111) << 8) | v[i + 1] + 1)
            i += 2
        else:
            print("VAL:", ((v[i] & 0b01111100) >> 2) + 1, (v[i] & 0b11) + 1)
            i += 1
        if i >= len(v):
            break
