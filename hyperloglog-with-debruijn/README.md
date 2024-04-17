## Preparing to replace bit-shift  `hllPatLen` with De Bruijn method

I learned there is a method counting the trailing zero [here](https://github.com/golang/go/blob/master/src/runtime/internal/sys/intrinsics.go#L53). The redis hyperloglog use bit shift method in `hllPatLen()`, which is called everytime the `PFADD` is called. So, if the De Bruijn counting method is more effective than bit-shift, replacing it make sense.

I wrote a program to test whether it's more effective. Let me try to explain the test cases and the result.

There are 4 `define` cases in the program:

- `RANDOM`:  just generate random uint64_t. This is a base time cost when the next two cases is run.
- `DEBRUIJN`: counting the trailing zeros of the random numbers with De Bruijn method.
- `BITSHIFT`: counting the trailing zeros of the random numbers with bit shift method.
- `CHECK`: call two functions and compare their results; print out the distribution of tailing zeros length.

More explainations:

- `ret` storing the sum of trailing zeros length, is use to void skipping the process when `-O2` flag is used.
- It is less posible to get a longer trailing zeros. To make the `CHECK` case can cover more long trailing zeros numbers, I left-shift the random number: `num = (num << (n % 50)) | ((uint64_t)1 << 51);`

Now let me show the result:

### 1. Run first 3 cases and compare the time

The result is as following:

```bash
> gcc -DRANDOM -O2 comparison.c && ./a.out
time consume: 10.820000 seconds
ret: 0xfa55d526137dcde3

> gcc -DBITSHIFT -O2 comparison.c && ./a.out
time consume: 14.440000 seconds
ret: 0x2fb03566

> gcc -DDEBRUIJN -O2 comparison.c && ./a.out
time consume: 10.960000 seconds
ret: 0x2fb03566
```

After removing the random number generating costs, we got this(much faster):

| random generation | Bit Shift | De Bruijn |
| :---------------: | :-------: | :-------: |
|      include      |  14.44 s  |  10.96 s  |
|      exclude      |  3.62 s   |  0.14 s   |

Meanwhile the `ret` of two cases is the same on. This means the correction of the new method.

### 2. Run check case

As mentioned before,  I left shifted the number. The result of two different counting method for each random number is same. And the distribution of trailing zeros length is as following:

```
> gcc -DCHECK -O2 comparison.c && ./a.out
time consume: 19.620000 seconds
 0: 0
 1: 3999773
 2: 6001116
 3: 6998319
 4: 7499012
 5: 7752334
 6: 7874867
 7: 7940717
 8: 7967613
 9: 7979342
10: 7995361
11: 7994381
12: 8001097
13: 7998487
14: 7998411
15: 8001045
16: 7998618
17: 7996643
18: 8000381
19: 8002905
20: 7994363
21: 8001226
22: 8004708
23: 8000645
24: 7996479
25: 8002017
26: 7996515
27: 8003087
28: 7999442
29: 7995457
30: 8002225
31: 8000386
32: 8000367
33: 7997993
34: 8001343
35: 7998145
36: 8006298
37: 7999528
38: 8000649
39: 7999591
40: 7998841
41: 7998956
42: 7997533
43: 7997693
44: 7998085
45: 8004006
46: 8000330
47: 8001280
48: 7998936
49: 8001060
50: 8000476
51: 8001918
```

### 3. Conclusion

The De Bruijn counting method is correct in our case and much more effective than raw bit shift.

A replacement will bring a significant help.

### 4. external benchmark

Using the redis-benchmark tool, it also show the new method is faster. To avoid one element's hash is to specific, here I using 32 elem to insert.

```bash
./src/redis-benchmark -n 10000000 PFADD key 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32
```

benchmark result with bit shift version redis-server:

```
> ./src/redis-benchmark -n 10000000 PFADD key 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32
====== PFADD key 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 ======
  10000000 requests completed in 98.64 seconds
  50 parallel clients
  272 bytes payload
  keep alive: 1
  host configuration "save": 3600 1 300 100 60 10000
  host configuration "appendonly": no
  multi-thread: no
Summary:
  throughput summary: 101379.78 requests per second
  latency summary (msec):
          avg       min       p50       p95       p99       max
        0.452     0.096     0.439     0.631     0.679     1.527
```

benchmark result with De Bruijn version redis-server:

```
> ./src/redis-benchmark -n 10000000 PFADD key 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32
====== PFADD key 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 ======
  10000000 requests completed in 91.91 seconds
  50 parallel clients
  272 bytes payload
  keep alive: 1
  host configuration "save": 3600 1 300 100 60 10000
  host configuration "appendonly": no
  multi-thread: no
Summary:
  throughput summary: 108799.72 requests per second
  latency summary (msec):
          avg       min       p50       p95       p99       max
        0.421     0.096     0.407     0.551     0.583     2.535
```



### Referrence

- <https://github.com/golang/go/blob/master/src/runtime/internal/sys/intrinsics.go#L53>
- <https://en.wikipedia.org/wiki/De_Bruijn_sequence#Finding_least-_or_most-significant_set_bit_in_a_word>
