import sys, re, os
from time import sleep
from datetime import datetime, time, timedelta
import tkinter as tk
from tkinter import ttk

import pandas as pd
from bs4 import BeautifulSoup
import requests


def main():
    gui = MyGUI()


# get path to the program directory
def get_path():
    return os.path.dirname(os.path.realpath(__file__))


# check if df is valid detail df
def is_valid_df(df: pd.DataFrame):
    if not isinstance(df, pd.DataFrame):
        return False

    cols = [
        "Symbol",
        "Sector",
        "Market Price",
        "Book Value",
        "PBV",
        "EPS",
        "P/E Ratio",
        "avg_dvnd_rate",
        "avg_dvnd_prob",
        "avg_bonus_prob",
        "scrape_date",
    ]
    return all([(col in list(df.columns.values)) for col in cols])


# filter df using criteria dictionary
def filter(df: pd.DataFrame, criteria: dict):
    
    # making df filterable
    df["num_year_yield"] = df["1 Year Yield"].apply(lambda x: float(x.strip("%")))
    df["num_eps"] = df["EPS"].apply(lambda x: float(x.split()[0]))

    # converting applicable columns to float
    for col in list(df.keys()):
        try:
            df[col] = df[col].astype(float)
        except ValueError:
            pass

    # applying criteria
    for column, condition in criteria.items():
        df = df.query(f"`{column}` {condition}")

    # curate dataframe
    filtered = pd.DataFrame()
    filtered["Symbol"] = df["Symbol"]
    filtered["Sector"] = df["Sector"]
    filtered["Market Price"] = df["Market Price"]
    filtered["Book Value"] = df["Book Value"]
    filtered["PBV"] = df["PBV"]
    filtered["EPS"] = df["EPS"]
    filtered["P/E Ratio"] = df["P/E Ratio"]
    filtered["avg_dvnd_rate"] = df["avg_dvnd_rate"]
    filtered["avg_dvnd_prob"] = df["avg_dvnd_prob"]
    filtered["avg_bonus_rate"] = df["avg_bonus_prob"]
    filtered["avg_bonus_prob"] = df["avg_bonus_prob"]
    filtered["1 Year Yield"] = df["num_year_yield"]

    return filtered


# show popup window
def show_popup(win=None, msg="Popup Message"):
    
    # popup in new window, stops other tasks until destroyed
    if win == None:
        popup = tk.Tk()
        popup.title("Popup")
        tk.Label(popup, text=msg, font=("Helvetica")).pack(padx=10, pady=10, expand=True)
        tk.Button(popup, text="Done", font="Helvetica", command=popup.destroy).pack(padx=10, pady=10)
        popup.mainloop()

    # popup given window, continues the other tasks
    else:
        top = tk.Toplevel(win)
        top.title("Popup")
        tk.Label(top, text=msg, font=("Helvetica")).pack(padx=10, pady=10, expand=True)
        tk.Button(top, text="Done", font="Helvetica", command=top.destroy).pack(padx=10, pady=10)


# class for nepali share market
class NEPSE:
    def __init__(self):
        # getting the company_list webpage (source: Merolagani)
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54",
            "referer": "https://www.google.com/",
        }
        response = requests.get("https://merolagani.com/CompanyList.aspx", headers=headers).text

        # parsing and setting sector names
        soup = BeautifulSoup(response, features="lxml")
        try:
            self.sectors = [
                name.get_text().strip()
                for name in soup.find_all(attrs={"class": "panel-title"})
            ]
        except TypeError:
            sys.exit(
                "No matching attribute was found while searching sector names in soup:merolagani"
            )   

        # parsing html for tables of sector data
        tables = pd.read_html(response)

        # setting the company symbols
        self.companies = {
            self.sectors[n]: df["Symbol"].to_list() for n, df in enumerate(tables)
        }

        # selecting only valid sectors
        self.sectors = self.sectors[: len(self.companies)]

    def get_sectors(self):
        return self.sectors

    def get_companies(self, sector_list=None):
        # defaulting and validating
        if sector_list == None:
            sector_list = self.sectors

        if not (isinstance(sector_list, list)):
            raise ValueError(
                "Please provide a class 'list' object to the function 'sector_list'."
            )

        return [smbl for sector in sector_list for smbl in self.companies[sector]]

    # parse date of format "(FY: start_yr-end_yr)"
    def parse_date(self, date_string):
        matches = re.search(r"(\d*)-(\d*)", date_string)
        try:
            return int(matches.group(1)), int(matches.group(2))  # type: ignore
        except AttributeError:
            print(date_string)
            raise ValueError("Invalid date_string")

    def process_companies(self, smbl_list=None) -> pd.DataFrame:
        if smbl_list == None:
            smbl_list = self.get_companies()

        outdated, updated = self.get_update_status(smbl_list)  # list of outdated comp_symbols, rest_df

        # terminating if all up-to-date
        if len(outdated) == 0:
            show_popup(msg="Selected companies up-to-date.")
            return updated  # type: ignore
        else:
            pass

        # handling progress_bar
        progress_popup = tk.Tk()
        progress_popup.title("Processing")
        progress_popup.geometry(f"650x100")
        bar = ttk.Progressbar(progress_popup, orient="horizontal", length=500)
        bar["value"] = 0
        bar["maximum"] = len(outdated)
        bar.pack(pady=10)

        current_smbl = tk.StringVar(progress_popup)
        label_current_smbl = tk.Label(progress_popup, textvariable=current_smbl, font=("Helvetica", 10))
        label_current_smbl.pack()

        progress = tk.StringVar(progress_popup)
        label_progress = tk.Label(progress_popup, textvariable=progress, font=("Helvetica", 8))
        label_progress.pack(pady=5)

        rows = []
        # creating the dataframe
        for comp_name in outdated:
            current_smbl.set(comp_name)
            bar.update()
            try:
                rows.append(Company(comp_name).details)
            except ValueError:
                continue

            # update progressbar
            bar["value"] += 1.0
            progress.set(f"{int(bar['value'])}/{len(outdated)}")
            bar.update()

        # updating popup after completed
        current_smbl.set("Completed")
        label_progress.destroy()
        tk.Button(
            progress_popup,
            text="Done",
            font=("Helvetica", 10),
            command=progress_popup.destroy,
        ).pack(pady=10)

        # handle return df
        updates_df = pd.DataFrame(rows)
        if isinstance(updated, pd.DataFrame):
            updates_df = pd.concat([updates_df, updated])

        updates_df.set_index("Symbol").to_csv(f"{get_path()}\\data.csv")
        return updates_df

    def get_update_status(self, smbl_list: list):
        try:
            full_df = pd.read_csv(f"{get_path()}\\data.csv")
        except FileNotFoundError:
            return smbl_list, None

        if not is_valid_df(full_df):  # type:ignore
            return smbl_list, None

        # setting index to make symbol searchable
        full_df["smbl"] = full_df["Symbol"]
        full_df.set_index("smbl", inplace=True)

        bool_outdated = full_df["scrape_date"].apply(self.is_outdated)
        outdated_df, updated_df = full_df[bool_outdated], full_df[~bool_outdated]

        df_smbls = []  # user given symbols present in the dataframe
        outdated = []  # outdated symbols to be returned

        for smbl in smbl_list:
            try:
                full_df.loc[smbl]
                df_smbls.append(smbl)
            except KeyError:
                outdated.append(smbl)

        if len(df_smbls) == 0:
            return smbl_list, full_df
        else:
            remaining = []
            for smbl in list(outdated_df.index.values):
                if smbl in df_smbls:
                    outdated.append(smbl)
                else:
                    remaining.append(outdated_df.loc[smbl])

            updated_df = pd.concat(
                [pd.DataFrame(remaining), updated_df]
            )  # all remaining as dataframe
            updated_df.reset_index(inplace=True, drop=True)  # resetting index

            # return: outdated smbl list, up-to-date dataframe + remaining
            return outdated, updated_df

    def is_outdated(self, date):  # date as a string in year-month-day format
        scrape_date = datetime.strptime(date, "%Y-%m-%d").date()
        present = datetime.now()
        nepse_end = time(15, 0)
        present_day = present.strftime("%A")

        if present_day == "Sunday":
            if present.time() > nepse_end:
                return present.date() > scrape_date
            else:
                return (present.date() - timedelta(days=2)) > scrape_date

        elif present_day == "Saturday":
            return (present.date() - timedelta(days=1)) > scrape_date

        else:
            if present.time() > nepse_end:
                return present.date() > scrape_date
            else:
                return (present.date() - timedelta(days=1)) > scrape_date


class Company(NEPSE):
    def __init__(self, smbl):
        if not (dfs := Company.get_dfs(smbl)):
            raise ValueError("Invalid symbol or broken webpage")

        # setting the details
        detail_df = dfs[0].iloc[0:12]
        self.details = detail_df.set_index(0).to_dict()[1]
        self.details = {"Symbol": smbl, **self.details}

        today = datetime.today()
        if today.strftime("%A") == "Saturday":
            self.details["scrape_date"] = str(
                datetime.today().date() - timedelta(days=1)
            )
        else:
            self.details["scrape_date"] = str(datetime.today().date())

        # dividends
        if dfs[1].empty:
            self.details["avg_dvnd_rate"], self.details["avg_dvnd_prob"] = 0, 0
        else:
            self.dividends = self.process_benefit(
                value_df=dfs[1]["Fiscal Year"], year_df=dfs[1]["Value"]
            )
            (
                self.details["avg_dvnd_rate"],
                self.details["avg_dvnd_prob"],
            ) = self.describe_benefit(self.dividends)

        # bonus
        if dfs[2].empty:
            self.details["avg_bonus_rate"], self.details["avg_bonus_prob"] = 0, 0
        else:
            self.bonus = self.process_benefit(
                value_df=dfs[2]["Value"], year_df=dfs[2]["Fiscal Year"]
            )
            (
                self.details["avg_bonus_rate"],
                self.details["avg_bonus_prob"],
            ) = self.describe_benefit(self.bonus)

    @classmethod
    def get_dfs(cls, symbol):
        try:
            dfs = pd.read_html(
                f"https://merolagani.com/CompanyDetail.aspx?symbol={symbol.replace(' ', '%')}"
            )
            sleep(0.3)

            if len(dfs) < 4:
                print(f"not all tables found for {symbol}, check webpage")
                return None
        except ValueError:
            print(f"no table found for {symbol} , check webpage")
            return None
        return dfs

    def process_benefit(self, year_df, value_df):  # get suitable datframe of dividend/bonus
        
        # setting the dividend values
        df = pd.DataFrame()
        df[["start_yr", "end_yr"]] = year_df.apply(
            lambda x: pd.Series(super(Company, self).parse_date(x))
        )
        df[["percent"]] = value_df.apply(
            lambda x: pd.Series(float(x.strip("%").replace(",", "")))
        )
        df.sort_values("percent", inplace=True, ascending=False)
        return df.drop_duplicates(
            subset=["start_yr", "end_yr"], ignore_index=True, keep="first"
        )

    def describe_benefit(self, benefit_df: pd.DataFrame):
        start, end, n = (
            benefit_df["start_yr"].min(),
            benefit_df["end_yr"].max(),
            benefit_df.shape[0],
        )
        rate = round(benefit_df["percent"].sum() / (end - start), 2)
        probability = round(n / (end - start) * 100, 2)
        return rate, probability


class MyGUI:
    def __init__(self):
        ## self.detail_df: all information , self.filtered_df:visible information ##
        self.is_online = True
        self.detail_df = None
        self.has_downloaded = False
        self.df_visible = False

        try:
            self.market = NEPSE()
        except requests.exceptions.ConnectionError:
            self.is_online = False

        # window
        self.window = tk.Tk()
        self.window.geometry(
            "%dx%d"
            % (self.window.winfo_screenwidth(), self.window.winfo_screenheight())
        )
        self.window.title("Fundy Filter")

        if self.is_online:
            self.render_download_frame()

        self.render_filter()
        self.render_order_frame()

        self.window.mainloop()

    def render_download_frame(self):
        self.download_frame = tk.Frame(self.window, bg="ivory4", bd=5, relief="flat")

        self.download_label = tk.Label(
            self.download_frame, text="Select Sector", font=("Helvetica", 10)
        )
        self.download_label.grid(row=0, column=0, pady=5, sticky="NEWS")

        self.download_sector = tk.StringVar(self.download_frame)
        self.download_sector.set("All")
        self.drop_sector = tk.OptionMenu(
            self.download_frame, self.download_sector, "All", *self.market.get_sectors()
        )
        self.drop_sector.grid(row=0, column=1, padx=5, pady=5, sticky="NEWS")

        self.download_btn = tk.Button(
            self.download_frame,
            text="Download",
            font=("Helvetica", 10),
            command=self.download_detail_df,
        )
        self.download_btn.grid(row=1, column=1, padx=5, sticky="NEWS")

        self.download_frame.pack(padx=10, pady=10)

    def render_filter(self):
        try:
            self.detail_df = pd.read_csv(f"{get_path()}//data.csv")

        except FileNotFoundError:
            # prompt to download data if online
            if self.is_online:
                show_popup(win=self.window, msg="Please Download Data")

            # exit showing the error msg if offline
            else:
                print( "please ignore the following error: \n\n")  
                self.window.destroy()
                show_popup(msg="Please get online and download data")
                sys.exit()

        # check if detail_df is valid
        if isinstance(self.detail_df, pd.DataFrame) and not(is_valid_df(self.detail_df)):  # type:ignore
            show_popup(win=self.window, msg="The saved data.csv file is invalid.")
            self.detail_df = None

        self.filter_band = tk.Frame(self.window, bg="ivory4", bd=10, relief="flat")
        self.filter_frame = tk.Frame(
            self.filter_band, bg="ivory3", bd=10, relief="flat"
        )

        # filter:sector
        self.query_sector = tk.StringVar(self.filter_frame)
        self.query_sector.set("No data found")  # set as No data found till updated
        tk.Label(self.filter_frame, text="Sector").grid(
            row=0, column=0, padx=2, sticky="NEWS"
        )
        self.selector_sector = tk.OptionMenu(
            self.filter_frame, self.query_sector, "No data found"
        )
        self.selector_sector.grid(row=1, column=0, padx=2, sticky="NEWS")

        # filter:price
        tk.Label(self.filter_frame, text="Price\n<").grid(
            row=0, column=1, padx=2, sticky="NEWS"
        )
        self.selector_price = tk.Entry(self.filter_frame, width=8)
        self.selector_price.grid(row=1, column=1, padx=2, sticky="NEWS")

        # filter:book_val
        tk.Label(self.filter_frame, text="Book_value\n<").grid(
            row=0, column=2, padx=2, sticky="NEWS"
        )
        self.selector_book_val = tk.Entry(self.filter_frame, width=8)
        self.selector_book_val.grid(row=1, column=2, padx=2, sticky="NEWS")

        # filter:pbv
        tk.Label(self.filter_frame, text="PBV\n<").grid(
            row=0, column=3, padx=2, sticky="NEWS"
        )
        self.selector_PBV = tk.Entry(self.filter_frame, width=8)
        self.selector_PBV.grid(row=1, column=3, padx=2, sticky="NEWS")

        # filter:eps
        tk.Label(self.filter_frame, text="EPS\n>").grid(
            row=0, column=4, padx=2, sticky="NEWS"
        )
        self.selector_eps = tk.Entry(self.filter_frame, width=8)
        self.selector_eps.grid(row=1, column=4, padx=2, sticky="NEWS")

        # filter:PE ratio
        tk.Label(self.filter_frame, text="PE ratio\n<").grid(
            row=0, column=5, padx=2, sticky="NEWS"
        )
        self.selector_PE = tk.Entry(self.filter_frame, width=8)
        self.selector_PE.grid(row=1, column=5, padx=2, sticky="NEWS")

        # filter:dvnd_rate
        tk.Label(self.filter_frame, text="dvnd %\n>").grid(
            row=0, column=6, padx=2, sticky="NEWS"
        )
        self.selector_dvnd_rate = tk.Entry(self.filter_frame, width=8)
        self.selector_dvnd_rate.grid(row=1, column=6, padx=2, sticky="NEWS")

        # filter:dvnd_probability
        tk.Label(self.filter_frame, text="dvnd prob.\n% >").grid(
            row=0, column=7, padx=2, sticky="NEWS"
        )
        self.selector_dvnd_prob = tk.Entry(self.filter_frame, width=8)
        self.selector_dvnd_prob.grid(row=1, column=7, padx=2, sticky="NEWS")

        # filter:bonus_rate
        tk.Label(self.filter_frame, text="Bonus %\n >").grid(
            row=0, column=8, padx=2, sticky="NEWS"
        )
        self.selector_bonus_rate = tk.Entry(self.filter_frame, width=8)
        self.selector_bonus_rate.grid(row=1, column=8, padx=2, sticky="NEWS")

        # filter:bonus_probability
        tk.Label(self.filter_frame, text="Bonus prob.\n% >").grid(
            row=0, column=9, padx=2, sticky="NEWS"
        )
        self.selector_bonus_prob = tk.Entry(self.filter_frame, width=8)
        self.selector_bonus_prob.grid(row=1, column=9, padx=2, sticky="NEWS")

        # filter:year_change
        tk.Label(self.filter_frame, text="Year Change %\n <, >, =").grid(
            row=0, column=10, padx=2, sticky="NEWS"
        )
        self.selector_year_change = tk.Entry(self.filter_frame, width=8)
        self.selector_year_change.grid(row=1, column=10, padx=2, sticky="NEWS")

        # filterbutton
        self.button_filter = tk.Button(
            self.filter_frame, width=8, text="Filter", command=self.apply_fitler
        )
        self.button_filter.grid(
            row=0, column=11, padx=2, pady=15, sticky="NEWS", rowspan=2
        )

        self.filter_frame.pack()
        self.filter_band.pack(fill="x")

        try:  # if data.csv exists
            self.update_selector_sector(self.detail_df)  # type: ignore
        except TypeError:  # detail_df is None type
            pass

    def render_order_frame(self):
        # show count and get sort order
        self.order_frame = tk.Frame(self.window)
        self.order_label = tk.Label(self.order_frame, text=f"Sort Order: ")
        self.order_label.pack(pady=5, side="left")

        # setting options
        self.order = tk.StringVar(self.order_frame)
        self.order.set("Ascending")
        tk.OptionMenu(self.order_frame, self.order, "Ascending", "Descending").pack(
            pady=5, side="right"
        )

        self.order_frame.pack()

    def render_df(self, df: pd.DataFrame):
        # show count in the order_label
        self.order_label.config(text=f"COUNT: {df.shape[0]}     Sort Order:")

        # rows and columns
        cols = list(df.keys())
        rows = df.values.tolist()

        # destroy to avoid duplicates
        if self.df_visible:
            self.df_frame.destroy()

        # Frame
        self.df_frame = ttk.Frame(self.window)
        tree = ttk.Treeview(self.df_frame, columns=cols, show="headings", height=20)
        tree.grid(row=0, column=0)

        # styling
        style = ttk.Style(self.df_frame)
        style.theme_use("clam")

        # adding vertical scrollbar-vsb
        vsb = ttk.Scrollbar(self.df_frame, orient="vertical", command=tree.yview)
        vsb.grid(row=0, column=1, sticky="news")
        tree.configure(yscrollcommand=vsb.set)

        # set column
        for col in tree["columns"]:
            tree.column(col, width=100, anchor="center")
        tree.column("EPS", width=135, anchor="center")

        # display headings
        for col in cols:
            tree.heading(col, text=col, command=lambda coln=col: self.my_sort(coln))

        # display rows
        for row in rows:
            tree.insert(parent="", index=tk.END, values=row)

        self.df_frame.pack(expand=False, pady=5)
        self.df_visible = True
        self.df_frame.update()

    def update_selector_sector(self, df: pd.DataFrame):
        # get new options
        options = set(df["Sector"].values)

        # clear options
        self.selector_sector["menu"].delete(0, "end")

        # adding "All" option
        self.selector_sector["menu"].add_command(
            label="All", command=tk._setit(self.query_sector, "All")
        )

        # add new options
        for option in options:
            self.selector_sector["menu"].add_command(
                label=option, command=tk._setit(self.query_sector, option)
            )
        self.query_sector.set("All")

    def download_detail_df(self):
        # download all if sector is not specified
        if self.download_sector.get() == "All":
            self.detail_df = self.market.process_companies()
        else:
            self.detail_df = self.market.process_companies(
                self.market.get_companies([self.download_sector.get()])
            )

        # updating variables
        self.has_downloaded = True
        self.update_selector_sector(self.detail_df)

    def apply_fitler(self):
        while True:
            # disable filter if self.detail_df != dataframe
            if not isinstance(self.detail_df, pd.DataFrame):
                break
            # makes sector blank so that get_sector returns all
            elif self.query_sector.get() == "All":
                criteria = {}  
            else:
                criteria = {"Sector": f"== '{self.query_sector.get()}'"}

            num_criteria = {
                    "Market Price": "< " + self.selector_price.get(),
                    "Book Value": "< " + self.selector_book_val.get(),
                    "PBV": "< " + self.selector_PBV.get(),
                    "num_eps": "> " + self.selector_eps.get(),
                    "P/E Ratio": "< " + self.selector_PE.get(),
                    "avg_dvnd_rate": "> " + self.selector_dvnd_rate.get(),
                    "avg_dvnd_prob": "> " + self.selector_dvnd_prob.get(),
                    "avg_bonus_rate": "> " + self.selector_bonus_rate.get(),
                    "avg_bonus_prob": "> " + self.selector_bonus_prob.get(),
                    "num_year_yield": self.selector_year_change.get(),
                }

            # deleting blank criteria and stripping trailing whitespaces
            num_criteria = {
                key: value.strip()
                for key, value in num_criteria.items()
                if value.strip() not in ("", "<", ">", "=")
            }
            criteria.update(num_criteria)

            # validating user input
            try:
                for value in num_criteria.values():
                    float(re.sub("[><=]", "", value))
            except ValueError:
                break

            # get filtered df
            self.filtered_df = filter(self.detail_df, criteria)  # type: ignore
            
            # render filtered_df
            self.render_df(self.filtered_df)
            break

    def my_sort(self, col: str):
        if self.order.get() == "Ascending":
            is_ascending = True
        else:
            is_ascending = False

        self.filtered_df.sort_values(by=[col], ascending=is_ascending, inplace=True)
        self.render_df(self.filtered_df)


if __name__ == "__main__":
    main()
