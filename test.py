from collections.abc import Iterable
import os
import sys
import random
import asyncio
from functools import reduce


#几种注释
#* 1
#todo 2
#? 3
#!4
#// 5
class Test(object):

    def test_iterator(self):
        #列表生成器
        print("列表生成器")
        print([x * x for x in range(1, 11) if x % 2 == 0])
        print([d for d in os.listdir('.')])
        print([x + 1 if x % 2 == 0 else -x for x in range(1, 11)])
        #生成器
        print("生成器")
        for x in (y * y for y in range(6)):
            print(x)

        print("生成器函数")

        def fib(max):
            n, a, b = 0, 0, 1
            while n < max:
                yield b
                a, b = b, a + b
                n = n + 1
            return 'done'

        for n in fib(6):
            print(n)

        #计算素数的一个方法是埃氏筛法
        def _odd_iter():
            n = 1
            while True:
                n = n + 2
                yield n

        def _not_divisible(n):
            return lambda x: x % n > 0

        def primes():
            yield 2
            it = _odd_iter()
            while True:
                n = next(it)
                yield n
                it = filter(_not_divisible(n), it)

        for n in primes():
            if n < 100:
                print(n)
            else:
                break

    def test_high_fun(self):
        #高阶函数
        def fn(x, y):
            return x * 10 + y

        print(reduce(fn, [1, 2, 3, 4]))

    def test_debug2(self):
        a = random.randint(0, 100)
        b = random.randint(0, 100)
        print(a * b)
        pass

    def test_debug(self):
        a = random.randint(0, 100)
        b = random.randint(0, 100)
        print(a * b)
        self.test_debug2()
        pass

    def test_asyncio(self):
        asyncio.gather()
        pass


Test().test_debug()
