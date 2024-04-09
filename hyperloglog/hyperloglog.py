import json
import math

HLL_ALPHA_INF = 0.721347520444481703680  # /* constant for 0.5/ln(2) */


class HyperLogLog:
    def __init__(self, p=14):
        self.p = p
        self.q = 64 - self.p
        self.m = 1 << self.p
        self.registers = [0] * self.m

    def tau(self, x: float) -> float:
        if x == 0.0 or x == 1.0:
            return 0.0
        y = 1.0
        z = 1 - x
        while True:
            x = math.sqrt(x)
            zPrime = z
            y *= 0.5
            z -= ((1 - x) ** 2) * y
            if zPrime == z:
                break
        return z / 3.0

    def sigma(self, x: float) -> float:
        if x == 1.0:
            return math.inf
        y = 1
        z = x
        while True:
            x *= x
            zPrime = z
            z += x * y
            y += y
            if zPrime == z:
                break
        return z

    @staticmethod
    def murmurhash64A(key, seed):
        m = 0xc6a4a7935bd1e995
        r = 47
        data = bytearray(key)
        h = seed ^ (len(data) * m)
        h &= 0xffffffffffffffff  # to ensure unsigned behavior

        j = -8
        for i in range(0, len(data) - (len(data) % 8), 8):
            j = i
            k = data[i]
            k |= data[i + 1] << 8
            k |= data[i + 2] << 16
            k |= data[i + 3] << 24
            k |= data[i + 4] << 32
            k |= data[i + 5] << 40
            k |= data[i + 6] << 48
            k |= data[i + 7] << 56

            k *= m
            k &= 0xffffffffffffffff  # to ensure unsigned behavior
            k ^= k >> r
            k *= m
            k &= 0xffffffffffffffff  # to ensure unsigned behavior

            h ^= k
            h *= m
            h &= 0xffffffffffffffff  # to ensure unsigned behavior

        data = data[j + 8:]

        switch = len(data) & 7
        if switch >= 7:
            h ^= data[6] << 48
            switch -= 1
        if switch >= 6:
            h ^= data[5] << 40
            switch -= 1
        if switch >= 5:
            h ^= data[4] << 32
            switch -= 1
        if switch >= 4:
            h ^= data[3] << 24
            switch -= 1
        if switch >= 3:
            h ^= data[2] << 16
            switch -= 1
        if switch >= 2:
            h ^= data[1] << 8
            switch -= 1
        if switch >= 1:
            h ^= data[0]
            h *= m
            h &= 0xffffffffffffffff  # to ensure unsigned behavior

        h ^= h >> r
        h *= m
        h &= 0xffffffffffffffff  # to ensure unsigned behavior
        h ^= h >> r
        return h

    def add(self, element):
        x = self.murmurhash64A(element.encode(), 0xADC83B19)
        j = ((1 << self.p) - 1) & x
        x >>= self.p
        x |= (1 << self.q)
        bit = 1
        count = 1
        while (x & bit) == 0:
            count += 1
            bit <<= 1
        self.registers[j] = max(self.registers[j], count)

    def histogram(self):
        ret = [0] * (self.q + 2)  # 这里是 Q+2
        for r in self.registers:
            ret[r] += 1
        return ret

    def count(self):
        reghisto = self.histogram()
        z = self.m * self.tau((self.m - reghisto[self.q + 1]) / self.m)
        for j in range(self.q, 0, -1):
            z += reghisto[j]
            z *= 0.5
        z += self.m * self.sigma(reghisto[0] / self.m)
        E = HLL_ALPHA_INF * self.m * self.m / z
        return round(E)

    def dump(self):
        for i, v in enumerate(self.registers):
            if v > 0:
                print(f"{i}: {v}")

    def merge(self, other):
        assert self.m == other.m
        self.registers = [max(x, y) for x, y in zip(self.registers, other.registers)]


