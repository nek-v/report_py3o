# -*- coding: utf-8 -*-

from decimal import Decimal

def get_digits(value):
    frac = str(Decimal(str(abs(value))) % 1)
    decimal = 0
    if frac not in ['0.0', '0']:
        decimal = len(str(frac).split('.')[1])
    return decimal