import requests
import pandas as pd
import argparse
import re
from bs4 import BeautifulSoup
import usaddress
import datetime


def get_property_tax_info(args):
    addr = usaddress.tag(args.address)
    house_number = addr[0]['AddressNumber']
    street_name = addr[0]['StreetName']
    street_suffix = addr[0]['StreetNamePostType'].replace(".", "")

    d = {'property_list': '', 'house_number': house_number, 'street_name': street_name, 'street_suffix': street_suffix}
    r_current_year = requests.post(f"http://{args.county}il.devnetwedge.com/Search/ExecuteSearch", data=d)

    last_year = str(int(r_current_year.url.split("/")[-1]) - 1)
    r_last_year_url = r_current_year.url.split("/")
    r_last_year_url[-1] = last_year
    r_last_year_url = "/".join(r_last_year_url)

    r_last_year = requests.get(r_last_year_url)


    soup = BeautifulSoup(r_current_year.text, 'html.parser')
    current_owner = soup.find_all('table')[0].find_all('div', {"class": "inner-value"})[2].text.split("\n")[0].split(",")
    current_owner.reverse()
    current_owner = " ".join(current_owner).strip()


    df_current = pd.read_html(r_current_year.text)
    current_taxes = df_current[1]['Total Billed'][0]
    current_excemptions = df_current[3]['Exemption Type'][0]
    if 0 <= 4 < len(df_current):
        current_sale_history = df_current[4]
        last_sold_price = current_sale_history['Gross Price'][0]
        last_sold_sale_date = current_sale_history['Sale Date'][0]
        last_sold_sale_date = datetime.datetime.strptime(last_sold_sale_date, "%m/%d/%Y")
        last_sold_sale_date = datetime.datetime.strftime(last_sold_sale_date, "%Y/%m/%d")
        last_sold = f"{args.address} was last sold on {last_sold_sale_date} for {last_sold_price}",
    else:
        last_sold = f"There is no sales data for {args.address}"

    df_last = pd.read_html(r_last_year.text)
    tax_rate = df_last[0][1][4].replace("Tax Rate", "").strip()


    data = {
        "current_owner": f"The current owner of {args.address} is {current_owner}.",
        "tax_rate": f"The tax rate last year for {args.address} was {tax_rate}%.",
        "last_sold": last_sold,
        "taxes": f"The taxes last year for {args.address} were {current_taxes}",
        "excemptions": f"The excemptions for {args.address} are: {current_excemptions}"
    }

    print(data[args.q])

if __name__ == "__main__":
   # Create the parser and add arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(dest='county', help="County where property is located")
    parser.add_argument(dest='address', help="1600 w pennslyvania ave")
    parser.add_argument(dest='q', help="what data do you want")


    # Parse and print the results
    args = parser.parse_args()
    get_property_tax_info(args)