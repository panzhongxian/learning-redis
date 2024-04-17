#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define HLL_P 14 /* The greater is P, the smaller the error. */
#define HLL_Q                                                   \
  (64 - HLL_P) /* The number of bits of the hash value used for \
                  determining the number of leading zeros. */
#define HLL_REGISTERS (1 << HLL_P)     /* With P=14, 16384 registers. */
#define HLL_P_MASK (HLL_REGISTERS - 1) /* Mask to index register. */

static uint64_t de_bruijn64 = 0x03f79d71b4ca8b09;

static int de_bruijn_64_lookup[64] = {
    0,  1,  56, 2,  57, 49, 28, 3,  61, 58, 42, 50, 38, 29, 17, 4,
    62, 47, 59, 36, 45, 43, 51, 22, 53, 39, 33, 30, 24, 18, 12, 5,
    63, 55, 48, 27, 60, 41, 37, 16, 46, 35, 44, 21, 52, 32, 23, 11,
    54, 26, 40, 15, 34, 20, 31, 10, 25, 14, 19, 9,  13, 8,  7,  6,
};

static int rightmostIndex64DeBruijn(uint64_t b) {
  b &= -b;
  b *= de_bruijn64;
  b >>= 58;
  return de_bruijn_64_lookup[b] + 1;
}

static int rightmostIndex64BitShift(uint64_t b) {
  uint64_t bit = 1;
  int count = 1; /* Initialized to 1 since we count the "00000...1" pattern. */
  while ((b & bit) == 0) {
    count++;
    bit <<= 1;
  }
  return count;
}

uint64_t generateRandom64Bit() {
  uint64_t randomNum = 0;
  for (int i = 0; i < 4; i++) {
    randomNum = (randomNum << 15) | (rand() & 0x7FFF);
  }

  return randomNum;
}

int main() {
  uint64_t ret = 0;
  clock_t start = clock();
  srand(0);
  int stat[64] = {0};

  for (int64_t n = 0; n < 400000000; ++n) {
    uint64_t num = (generateRandom64Bit() >> HLL_P) | ((uint64_t)1 << HLL_Q);

#ifdef RANDOM
    ret += num;
#elif DEBRUIJN
    ret += rightmostIndex64DeBruijn(num);
#elif BITSHIFT
    ret += rightmostIndex64BitShift(num);
#elif CHECK
    num = (num << (n % 50)) | ((uint64_t)1 << 50);
    int len1 = rightmostIndex64BitShift(num);
    int len2 = rightmostIndex64DeBruijn(num);
    if (len1 != len2) {
      printf("[%lld]0x%llx, %d, %d\n", n, num, len1, len2);
      assert(0);
    }
    stat[len1] += 1;
#endif
  }
  printf("time consume: %f seconds\n",
         ((double)(clock() - start)) / CLOCKS_PER_SEC);
#ifdef CHECK
  for (int i = 0; i <= 52; i++) {
    printf("%2d: %d\n", i, stat[i]);
  }
#endif

  printf("ret: 0x%llx\n", ret);
  return ret;
}
