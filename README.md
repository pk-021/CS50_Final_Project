# Fundy Analyzer
#### Video Demo:  < https://youtu.be/TIkHS1dZ4Hs>
### Description:
The aim of Fundy Filter is to make the fundamental analysis of Nepali Stock Companies easier.
Fundy Filter is a **GUI python program** that scrapes the merolagani website and collects data on the Nepal
Share Market. After applying user-given filters, this program displays the data in a suitable format.

**All the functions and classes are implemented in project.py**
## Functions:


#### `get_path()`:
It gets the path of root folder(having project.py) as a string

#### `is_valid_df(df: pd.DataFrame)`:
checks if the provided df is non-empty `pd.DataFrame` object that has the columns to satisfy being a company-detail-datafrmae.

#### `filter(df: pd.DataFrame, criteria: dict)`:
Filters the given `Pandas.DataFrame` using the given criteria `dict` using queries.
Returns a dataframe with fixed columns and proper datatypes.

### `show_popup(win=None, msg="Popup Message")`:
Displays a popup with the given message.If a `tkinter` window is provided, attempts to dispaly at the top of window and doesn't pause program. If not provided, creates a new window and pauses the program till the popup isn't closed

## Classes:


### NEPSE
Represents the entire Nepali Sharemarket. It has tools to download and process data of many companies.

####  `NEPSE.sectors` :
>   sectors of nepali share market

#### `NEPSE.companies`:
>   dictionary where key: sector, value: list of symbols

#### `__init__(self)`:
>   visits <https://merolagani.com/CompanyList.aspx>, sets `NEPSE.sectors` and `NEPSE.  companies`.

#### `get_sectors(self)`:
>   returns `NEPSE.sectors`

#### `get_companies(self, sector_list=None)`:
>   if no sector list is provided, returns list of all symbols
    and if provided, returns the symbols of said sectors.

#### `parse_date(self, date_string)`:
>   parse date of format (FY: start_yr-end_yr) and return (start_year, end_year)

#### `process_companies(self, smbl_list=None)`:
>- gets the detail_df of companies in smbl_list if none is provided, uses `Nepse.      get_companies`.
>- check update status of companies
>- starts download of outdated companies
>- Desplays a popup to show the downloads
>- Merges the up-to-date and updated dataframes
>- Saves and returns the merged dataframe

#### `get_update_status(self, smbl_list: list)`:

>   Fetchs data.csv from root directory, if doesn't assumes entire smbl_list as
    outdated.Also assumes outdated if data.csv is invalid.If `data.csv`  is present and
    valid,uses the data to check smbl_list for outdated companies.Returns list of
    outdated symbols and up-to-date dataframe. If all are up-to-date,returns empty list
    and entie dataframe.

### `is_outdated(self, date)`:
>   checks for the date in `YY-MM-DD` format if it is outdated ticker scrape_date for
    Nepal taking current time and date as reference and returns a `bool`. It assumes share
    market opens on all days except saturday from 11 a.m. to 3 p.m.


### Company


Inherits from `NEPSE` class. Represents a company in Nepal Stock Exchange. It has tools to download
and process data of a listed company.

#### `Company.details`:
>   dictionary of details of companies

#### `__init__(self)`:
>   visits the company's `Merolagani` website, feteches the data, cleans and processes
    them and sets `Company.details`.

#### ClassMethod `get_dfs(symbol)`:
> visits the company's `Merolagani` webiste and returns the dataframes in a list.


### MyGUI


#### `__init__(self)`:

I have coded such that the `data.csv` is also accessed by this class for offline support.
> if offline, checks if the `data.csv` is present and valid and renders everything
    except download_frame. Download_frame renders if online.
    if offline and the `data.csv` is missing, it exits and shows a popup error.
    if online and the `data.csv` is missing, it shows a popup, filter is disabled.

Functions starting with `render` render the respective frames in the window

####    `update_selector_sector(self, df: pd.DataFrame)`:
>   updates the sector selector menu in the `filter_frame` to include all and only the
    sectors in the given df.

The rest of the functions in `MyGUI` handle the implementation of buttons and other background tasks.
