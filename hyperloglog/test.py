from hyperloglog import HyperLogLog
import unittest
from tools import gen_batch_elem_name, get_redis_conn, parse_dense_registers, dump_header, parse_sparse_registers


class TestAddNumbers(unittest.TestCase):

    def test_py_hll(self):
        hll = HyperLogLog()
        elem_names = gen_batch_elem_name("elem_", 100000)
        redis_conn = get_redis_conn()
        hll_key = "test_key"
        redis_conn.delete(hll_key)
        for elem_name in elem_names:
            hll.add(elem_name)
            redis_conn.pfadd(hll_key, elem_name)

        assert hll.registers == parse_dense_registers(hll_key)
        assert hll.count() == redis_conn.pfcount(hll_key)

    def test_py_hll_simple_insert(self):
        hll = HyperLogLog()
        hll.add("banana")
        hll.add("cherry")
        assert hll.count() == 2

        hll2 = HyperLogLog()
        hll2.add("banana")
        hll2.add("durian")
        hll2.add("elderberry")
        hll.merge(hll2)
        assert hll.count() == 4

    def test_show_redis_hll_header(self):
        redis_conn = get_redis_conn()
        hll_key = "test_key"
        redis_conn.delete(hll_key)
        redis_conn.pfadd(hll_key, "banana")
        dump_header(hll_key)
        print("-----------------")
        redis_conn.pfcount(hll_key)
        dump_header(hll_key)

    def test_parse_sparse_registers(self):
        redis_conn = get_redis_conn()
        hll_key = "test_key"
        redis_conn.delete(hll_key)
        redis_conn.pfadd(hll_key, "banana")
        parse_sparse_registers(hll_key)
