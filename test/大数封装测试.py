# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/18 0:32
@Author     : lkkings
@FileName:  : 大数封装测试.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""


class BigNumber:
    def __init__(self, value):
        self.value = str(value)

    def __str__(self):
        return self.value

    def _add_digits(self, a, b, carry):
        result = a + b + carry
        return result % 10, result // 10

    def add(self, other):
        num1 = self.value[::-1]
        num2 = other.value[::-1]
        max_len = max(len(num1), len(num2))

        num1 = num1.ljust(max_len, '0')
        num2 = num2.ljust(max_len, '0')

        carry = 0
        result = []

        for i in range(max_len):
            digit1 = int(num1[i])
            digit2 = int(num2[i])
            sum_digit, carry = self._add_digits(digit1, digit2, carry)
            result.append(str(sum_digit))

        if carry:
            result.append(str(carry))

        return BigNumber(''.join(result[::-1]))

    def subtract(self, other):
        num1 = self.value
        num2 = other.value

        if len(num1) < len(num2) or (len(num1) == len(num2) and num1 < num2):
            raise ValueError("Subtraction would result in a negative number.")

        num1 = num1[::-1]
        num2 = num2[::-1].ljust(len(num1), '0')

        borrow = 0
        result = []

        for i in range(len(num1)):
            digit1 = int(num1[i])
            digit2 = int(num2[i])
            if digit1 < digit2 + borrow:
                digit1 += 10
                result_digit = digit1 - digit2 - borrow
                borrow = 1
            else:
                result_digit = digit1 - digit2 - borrow
                borrow = 0

            result.append(str(result_digit))

        while result[-1] == '0' and len(result) > 1:
            result.pop()

        return BigNumber(''.join(result[::-1]))

    def multiply(self, other):
        num1 = self.value
        num2 = other.value
        len1, len2 = len(num1), len(num2)
        result = [0] * (len1 + len2)

        for i in range(len1 - 1, -1, -1):
            carry = 0
            for j in range(len2 - 1, -1, -1):
                prod = (int(num1[i]) * int(num2[j])) + result[i + j + 1] + carry
                carry = prod // 10
                result[i + j + 1] = prod % 10
            result[i + j] += carry

        result_str = ''.join(map(str, result)).lstrip('0')
        return BigNumber(result_str if result_str else '0')

    def divide(self, other):
        num1 = self.value
        num2 = other.value

        if num2 == '0':
            raise ZeroDivisionError("division by zero")

        result = []
        remainder = ''

        for digit in num1:
            remainder += digit
            quotient = 0
            while BigNumber(remainder).subtract(BigNumber(num2)).value[0] != '-':
                remainder = BigNumber(remainder).subtract(BigNumber(num2)).value
                quotient += 1
            result.append(str(quotient))

        result_str = ''.join(result).lstrip('0')
        return BigNumber(result_str if result_str else '0')


# 示例用法
a = BigNumber("123456789123456789")
b = BigNumber("987654321987654321")

print("Add:", a.add(b))
print("Subtract:", a.subtract(b))
print("Multiply:", a.multiply(b))
print("Divide:", a.divide(b))
