import os

import pytest
from pandas import DataFrame

import project

def test_get_path():
    assert os.path.isfile(f"{project.get_path()}//test_project.py")

def test_filter():

    #model data
    data = {
        "Symbol": ["NTC"],
        "Sector": ["Others"],
        "Shares Outstanding": [180000000],
        "Market Price":[ "817"],
        "% Change": ["0 %"],
        "Last Traded On": ["2023/04/19 03:00:00"],
        "52 Weeks High - Low": ["1,081.00-791.00"],
        "120 Day Average": [842.82],
        "1 Year Yield": ["-20.91%"],
        "EPS":[ "47.28  (FY:079-080, Q:2)"],
        "P/E Ratio": [17.28],
        "Book Value": [512.92],
        "PBV": [1.59],
        "scrape_date": ["2023-04-19"],
        "avg_dvnd_rate": [36.33],
        "avg_dvnd_prob": [100],
        "avg_bonus_rate":[ 20],
        "avg_bonus_prob": [100]
        }
    
    df =DataFrame(data)
    assert isinstance(project.filter(df,criteria={"Sector": "== 'Others'"}), DataFrame)
    assert project.filter(df,criteria={}).shape[0] == 1
    assert project.filter(df, criteria={})["Market Price"].dtype == "float"

def test_is_valid_df():

    assert project.is_valid_df(["Market Price", 300, "EPS", 20]) == False #type: ignore

    #removed symbol and sector
    data1 = {
        "Shares Outstanding": [180000000],
        "Market Price":[ "817"],
        "% Change": ["0 %"],
        "Last Traded On": ["2023/04/19 03:00:00"],
        "52 Weeks High - Low": ["1,081.00-791.00"],
        "120 Day Average": [842.82],
        "1 Year Yield": ["-20.91%"],
        "EPS":[ "47.28  (FY:079-080, Q:2)"],
        "P/E Ratio": [17.28],
        "Book Value": [512.92],
        "PBV": [1.59],
        "scrape_date": ["2023-04-19"],
        "avg_dvnd_rate": [36.33],
        "avg_dvnd_prob": [100],
        "avg_bonus_rate":[ 20],
        "avg_bonus_prob": [100]
        }
    assert project.is_valid_df(DataFrame(data1)) == False

    #removed avg_dvnd_rate and avg_dvnd_prob
    data2 = {
        "Symbol": ["NTC"],
        "Sector": ["Others"],
        "Shares Outstanding": [180000000],
        "Market Price":[ "817"],
        "% Change": ["0 %"],
        "Last Traded On": ["2023/04/19 03:00:00"],
        "52 Weeks High - Low": ["1,081.00-791.00"],
        "120 Day Average": [842.82],
        "1 Year Yield": ["-20.91%"],
        "EPS":[ "47.28  (FY:079-080, Q:2)"],
        "P/E Ratio": [17.28],
        "Book Value": [512.92],
        "PBV": [1.59],
        "scrape_date": ["2023-04-19"],
        "avg_dvnd_prob": [100],
        "avg_bonus_prob": [100]
        }
    assert project.is_valid_df(DataFrame(data2)) == False

    # *just valid* dataframe
    data3 = {
        "Symbol": ["NTC"],
        "Sector": ["Others"],
        "Market Price":[ "817"],
        "% Change": ["0 %"],
        "1 Year Yield": ["-20.91%"],
        "EPS":[ "47.28  (FY:079-080, Q:2)"],
        "P/E Ratio": [17.28],
        "Book Value": [512.92],
        "PBV": [1.59],
        "scrape_date": ["2023-04-19"],
        "avg_dvnd_rate": [36.33],
        "avg_dvnd_prob": [100],
        "avg_bonus_rate":[ 20],
        "avg_bonus_prob": [100]
        }
    assert project.is_valid_df(DataFrame(data3))


# Testing NEPSE class
market = project.NEPSE()

def test_get_sectors():
    return_val = market.get_sectors()
    assert isinstance(return_val, list)
    assert ("Hydro Power" in return_val)

def test_get_companies():
    return_val = market.get_companies(sector_list = ["Hydro Power"])
    assert isinstance(return_val, list)
    assert ("API" in return_val)
    assert ("NBL" not in return_val)

def test_parse_date():
    assert market.parse_date(" 079-080") == (79, 80)
    with pytest.raises(ValueError):
        market.parse_date(" ll1-ll2 ")


#Testing Company class
def test_symbol_rejection():
    with pytest.raises(ValueError):
        project.Company("Non_existent")

def test_get_dfs():
    return_val = project.Company.get_dfs("NBL")
    assert isinstance(return_val, list)
    assert isinstance(return_val[0],DataFrame)

def test_details():
    details = project.Company("NBL").details
    assert "avg_dvnd_rate" in details.keys()
    assert "avg_bonus_rate" in details.keys()
