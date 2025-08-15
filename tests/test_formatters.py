import pytest
from consolidate_data import format_cnic, format_mobile_number, format_date


def test_format_cnic_valid():
    assert format_cnic('42201-1234567-1') == '42201-1234567-1'
    assert format_cnic('4220112345671') == '42201-1234567-1'


def test_format_cnic_invalid():
    assert format_cnic('abc') == 'N/A'
    assert format_cnic('') == 'N/A'


def test_format_mobile_valid():
    assert format_mobile_number('03001234567') == '0300-1234567'
    assert format_mobile_number('3001234567') == '0300-1234567'


def test_format_mobile_invalid():
    assert format_mobile_number('123') == 'N/A'


def test_format_date_various():
    assert format_date('2025-01-15') == '15-Jan-2025'
    assert format_date('15/01/2025') == '15-Jan-2025'
    assert format_date('Jan 15, 2025') == '15-Jan-2025'


def test_format_date_invalid():
    assert format_date('notadate') == 'notadate' or format_date('notadate') == 'N/A'
