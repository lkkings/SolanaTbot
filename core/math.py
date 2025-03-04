# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/8 1:02
@Author     : lkkings
@FileName:  : math.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import math
from typing import List
from core.types.dex import SwapResult, SwapExactOutputResult


class Fraction:
    __slots__ = ['_numerator', '_denominator']

    def __init__(self, numerator: int, denominator: int):
        self._numerator = numerator
        self._denominator = denominator

    @property
    def numerator(self):
        return self._numerator

    @property
    def denominator(self):
        return self._denominator

    @property
    def value(self) -> int:
        return int(self.numerator / self.denominator)

    def __repr__(self):
        return f"Fraction({self.numerator}/{self.denominator})"


ZERO_FRACTION = Fraction(int(0), int(1))


def calculate_fee_amount(amount: int, fee_rate: Fraction) -> int:
    if fee_rate.numerator == 0 or amount == 0:
        return int(0)
    fee_amount = (amount * fee_rate.numerator) / fee_rate.denominator
    return int(1) if fee_amount == 0 else fee_amount


def ceiling_division(dividend: int, divisor: int) -> (int, int):
    # Compute the quotient and remainder
    quotient = dividend // divisor
    remainder = dividend % divisor

    if quotient == 0:
        return 0, 0

    if remainder > 0:
        quotient += 1
        new_divisor = dividend // quotient
        new_remainder = dividend % quotient

        if new_remainder > 0:
            new_divisor += 1
    else:
        new_divisor = divisor

    return quotient, new_divisor


class TokenSwapConstantProduct:
    def __init__(self, trader_fee: Fraction, owner_fee: Fraction, fees_on_input: bool = True):
        self.trader_fee = trader_fee
        self.owner_fee = owner_fee
        self.fees_on_input = fees_on_input

    def exchange(self, token_amounts: List[int], input_trade_amount: int, output_index: int) -> SwapResult:
        input_index = 1 if output_index == 0 else 0
        new_input_trade_amount = self.get_amount_less_fees(input_trade_amount) \
            if self.fees_on_input else input_trade_amount
        expected_output_amount = self.get_expected_output_amount(token_amounts, new_input_trade_amount, input_index,
                                                                 output_index)
        fees = self.get_fees(input_trade_amount) if self.fees_on_input else self.get_fees(expected_output_amount)

        if not self.fees_on_input:
            expected_output_amount = self.get_amount_less_fees(expected_output_amount)
        price_impact = self.get_price_impact(token_amounts, new_input_trade_amount, expected_output_amount,
                                             input_index, output_index)
        return SwapResult(price_impact=price_impact, fees=fees, expected_output_amount=expected_output_amount)

    def exchange_for_exact_output(self, token_amounts: List[int], output_trade_amount: int,
                                  output_index: int) -> SwapExactOutputResult:
        input_index = 1 if output_index == 0 else 0
        new_output_trade_amount = output_trade_amount if self.fees_on_input else self.get_amount_plus_fees(
            output_trade_amount)
        expected_input_amount = self.get_input_amount(token_amounts, new_output_trade_amount, input_index,
                                                      output_index)
        fees = self.get_fees(expected_input_amount) if self.fees_on_input else self.get_fees(output_trade_amount)

        if self.fees_on_input:
            expected_input_amount = self.get_amount_plus_fees(expected_input_amount)
        price_impact = self.get_price_impact_exact_output(token_amounts, expected_input_amount,
                                                          new_output_trade_amount, input_index, output_index)
        return SwapExactOutputResult(price_impact=price_impact, fees=fees, expected_input_amount=expected_input_amount)

    def get_price_impact(self, token_amounts: List[int], input_trade_amount: int,
                         expected_output_amount: int, input_index: int, output_index: int) -> int:
        if input_trade_amount == 0 or token_amounts[input_index] == 0 or token_amounts[output_index] == 0:
            return int(0)

        no_slippage_output_amount = self.get_expected_output_amount_with_no_slippage(token_amounts,
                                                                                     input_trade_amount,
                                                                                     input_index, output_index)
        impact = (no_slippage_output_amount - expected_output_amount) / no_slippage_output_amount
        return int(impact)

    def get_price_impact_exact_output(self, token_amounts: List[int], expected_input_trade_amount: int,
                                      output_amount: int, input_index: int, output_index: int) -> int:
        if output_amount == 0 or token_amounts[input_index] == 0 or token_amounts[output_index] == 0:
            return int(0)

        no_slippage_input_amount = self.get_expected_input_amount_with_no_slippage(token_amounts, output_amount,
                                                                                   input_index, output_index)
        impact = (expected_input_trade_amount - no_slippage_input_amount) / no_slippage_input_amount
        return int(impact)

    def get_fees(self, input_trade_amount: int) -> int:
        trading_fee = calculate_fee_amount(input_trade_amount, self.trader_fee)
        owner_fee = calculate_fee_amount(input_trade_amount, self.owner_fee)
        return trading_fee + owner_fee

    def get_expected_output_amount(self, token_amounts: List[int], input_trade_amount: int,
                                   input_index: int,
                                   output_index: int) -> int:
        return self.get_output_amount(token_amounts, input_trade_amount, input_index, output_index)

    def get_expected_input_amount_with_no_slippage(self, token_amounts: List[int], output_trade_amount: int,
                                                   input_index: int, output_index: int) -> int:
        if token_amounts[output_index] == 0:
            return token_amounts[input_index]

        expected_input_amount_with_no_slippage = int(
            (output_trade_amount * token_amounts[input_index]) / token_amounts[output_index])

        if self.fees_on_input:
            return self.get_amount_plus_fees(expected_input_amount_with_no_slippage)
        else:
            return expected_input_amount_with_no_slippage

    def get_expected_output_amount_with_no_slippage(self, token_amounts: List[int], input_trade_amount: int,
                                                    input_index: int, output_index: int) -> int:
        if token_amounts[input_index] == 0:
            return token_amounts[output_index]

        expected_output_amount_with_no_slippage = int(
                (input_trade_amount * token_amounts[output_index]) / token_amounts[input_index])

        if self.fees_on_input:
            return expected_output_amount_with_no_slippage
        else:
            return self.get_amount_less_fees(expected_output_amount_with_no_slippage)

    def get_amount_less_fees(self, trade_amount: int) -> int:
        return trade_amount - self.get_fees(trade_amount)

    def get_amount_plus_fees(self, trade_amount: int) -> int:
        return trade_amount + self.get_fees(trade_amount)

    def get_output_amount(self, token_amounts: List[int], input_trade_amount: int, input_index: int,
                          output_index: int) -> int:
        pool_input_amount = token_amounts[input_index]
        pool_output_amount = token_amounts[output_index]
        invariant = self.get_invariant(token_amounts)
        new_pool_output_amount, _ = ceiling_division(invariant, int(pool_input_amount + input_trade_amount))

        return pool_output_amount - new_pool_output_amount

    def get_input_amount(self, token_amounts: List[int], output_trade_amount: int, input_index: int,
                         output_index: int) -> int:
        pool_input_amount = token_amounts[input_index]
        pool_output_amount = token_amounts[output_index]
        invariant = self.get_invariant(token_amounts)

        if output_trade_amount >= pool_output_amount:
            raise ValueError("流动性不足，无法提供输出交易金额")

        new_pool_input_amount, _ = ceiling_division(invariant, int(pool_output_amount - output_trade_amount))

        return new_pool_input_amount - pool_input_amount

    def get_invariant(self, token_amounts: List[int]) -> int:
        scalar = 10 ** 8
        a = token_amounts[0] / scalar
        b = token_amounts[1] / scalar
        return int(a * b * scalar ** 2)


class Curve:
    def __init__(self, number_of_currencies, amplification_factor, target_prices):
        self.number_of_currencies = number_of_currencies
        self.amplification_factor = amplification_factor
        self.target_prices = target_prices

    def exchange(self, token_amounts, input_index, output_index, amount, minus_one=True):
        if len(token_amounts) != self.number_of_currencies:
            raise ValueError('Number of currencies does not match')

        xp = self.xp(token_amounts)
        dx = amount * self.target_prices[input_index]
        x = xp[input_index] + dx
        y = self.compute_y(token_amounts, input_index, output_index, x)
        dy = xp[output_index] - y

        if minus_one:
            dy -= 1

        return dy // self.target_prices[output_index]

    def compute_base_y(self, token_amounts, input_index, output_index, amount):
        d = self.compute_d(token_amounts)
        xp = self.xp(token_amounts)
        nn = self.number_of_currencies ** self.number_of_currencies
        sum_xp = sum(xp)
        product_xp = self.multiply_array(xp)

        k = (self.amplification_factor * nn * sum_xp + d +
             self.amplification_factor * d * nn)
        b = (self.amplification_factor * nn * nn * product_xp)
        c = nn * product_xp * k
        numerator = b + c // xp[input_index]
        denominator = b + c // xp[output_index]

        input_factor = math.log10(self.target_prices[input_index])
        output_factor = math.log10(self.target_prices[output_index])
        factor = abs(output_factor - input_factor)

        if input_factor >= output_factor:
            return (numerator * amount // denominator) * (10 ** factor)
        else:
            return (numerator * amount // denominator) // (10 ** factor)

    def compute_y(self, token_amounts, input_index, output_index, new_total_amount):
        d = self.compute_d(token_amounts)
        xx = self.xp(token_amounts)
        xx[input_index] = new_total_amount
        xx.pop(output_index)

        ann = self.amplification_factor * self.number_of_currencies
        c = d

        for _ in range(MAX_ITERATIONS):
            y_prev = d
            c = (c * d) // (xx[0] * self.number_of_currencies)  # Simplified for loop

            c = (c * d) // (self.number_of_currencies * ann)
            b = sum(xx) + d // ann - d
            y = d

            # Iteratively approximate the value of y
            for _ in range(MAX_ITERATIONS):
                y_prev = y
                y = (y ** 2 + c) // (2 * y + b)

                if abs(y - y_prev) <= 1:
                    break

        return y

    def compute_d(self, token_amounts):
        d_prev = 0
        xp = self.xp(token_amounts)
        sum_xp = sum(xp)
        d = sum_xp
        ann = self.amplification_factor * self.number_of_currencies

        for _ in range(MAX_ITERATIONS):
            d_prev = d
            d_p = d

            for x in xp:
                d_p = d_p * d // (self.number_of_currencies * x)

            numerator = (ann * sum_xp + d_p * self.number_of_currencies) * d
            denominator = ((ann - 1) * d + (self.number_of_currencies + 1) * d_p)
            d = numerator // denominator

            if abs(d - d_prev) <= 1:
                break

        return d

    def xp(self, token_amounts):
        return [amount * price for amount, price in zip(token_amounts, self.target_prices)]

    def set_amplification_factor(self, amplification_factor):
        self.amplification_factor = amplification_factor

    def multiply_array(self, arr):
        product = 1
        for x in arr:
            product *= x
        return product


# 常量定义和最大迭代次数
MAX_ITERATIONS = 100
ZERO = 0


class Stable:
    def __init__(self, number_of_currencies: int, amp: int, target_prices: List[int], trader_fee: Fraction):
        self.target_prices = target_prices
        self.trader_fee = trader_fee
        self.curve = Curve(number_of_currencies, amp, self.target_prices)

    def exchange(self, token_amounts, input_trade_amount, input_index, output_index):
        output_amount_without_fees = self.get_output_amount(token_amounts, input_trade_amount, input_index, output_index)
        fees = self.get_fees(output_amount_without_fees)
        expected_output_amount = output_amount_without_fees - fees

        return {
            'priceImpact': self.get_price_impact(token_amounts, input_trade_amount, expected_output_amount, input_index, output_index),
            'fees': fees,
            'expectedOutputAmount': expected_output_amount
        }

    def get_price_impact(self, token_amounts, input_trade_amount, expected_output_amount, input_index, output_index):
        if input_trade_amount == 0 or token_amounts[input_index] == 0 or token_amounts[output_index] == 0:
            return 0.0

        no_slippage_output_amount = self.get_output_amount_with_no_slippage(token_amounts, input_trade_amount, input_index, output_index)
        impact = (no_slippage_output_amount - expected_output_amount) / no_slippage_output_amount
        return impact

    def get_fees(self, output_amount_without_fees):
        if self.trader_fee.numerator == 0:
            return 0
        return (output_amount_without_fees * self.trader_fee.numerator) // self.trader_fee.denominator

    def get_output_amount(self, token_amounts, input_trade_amount, input_index, output_index):
        return self.curve.exchange(token_amounts, input_index, output_index, input_trade_amount)

    def get_output_amount_with_no_slippage(self, token_amounts, input_trade_amount, input_index, output_index):
        return self.curve.compute_base_y(token_amounts, input_index, output_index, input_trade_amount)

    def set_amp(self, amp):
        self.curve.set_amplification_factor(amp)

    def set_trader_fee(self, trader_fee):
        self.trader_fee = trader_fee

# 假设 Curve 类已经定义
