from json import load
import requests
import pandas as pd
import argparse
import re
from bs4 import BeautifulSoup
import usaddress
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_KEY = os.environ.get('ACCESS_KEY')

def get_payment_history(x, address, current_year):
    return f"The taxes for {address} in {current_year} were {x['Total Billed'][0]}"

def get_excemptions(x, address, current_year):
    return f"The excemptions for {address} in {current_year} are: {x['Exemption Type'][0]}"

def get_last_sale(x, address, current_year):
    current_sale_history = x
    last_sold_price = current_sale_history['Gross Price'][0]
    last_sold_sale_date = current_sale_history['Sale Date'][0]
    last_sold_sale_date = datetime.datetime.strptime(last_sold_sale_date, "%m/%d/%Y")
    last_sold_sale_date = datetime.datetime.strftime(last_sold_sale_date, "%Y/%m/%d")
    last_sold = f"{address} was last sold on {last_sold_sale_date} for {last_sold_price}"
    return last_sold

def get_property_tax_info(args):
    data = {
        "current_owner": "Unable to get current owner.",
        "tax_rate": "Unable to get tax rate.",
        "last_sold": "Unable to get sales data",
        "taxes": "Unable to get taxes.",
        "excemptions": "Unable to get excemptions."
    }


    columns = {
        "['Exemption Type', 'Requested Date', 'Granted Date', 'Renewal Date', 'Prorate Date', 'Requested Amount', 'Granted Amount']": 
            {'function': get_excemptions, 'key': 'excemptions'},
        "['Tax Year', 'Total Billed', 'Total Paid', 'Amount Unpaid']": 
            {'function':get_payment_history, 'key': 'taxes'},
        "['Year', 'Document #', 'Sale Type', 'Sale Date', 'Sold By', 'Sold To', 'Gross Price', 'Personal Property', 'Net Price']":
            {'function': get_last_sale, 'key': 'last_sold'}
    }
    
    
    r = requests.get('http://api.positionstack.com/v1/forward', params={
        'access_key': ACCESS_KEY,
        'query': args.address
    })
    

    house_number = r.json()['data'][0]['number']
    street_name = r.json()['data'][0]['street']
    county = r.json()['data'][0]['county'].replace(" County", "")

    d = {'property_list': '', 'house_number': house_number, 'street_name': street_name}

    r_current_year = requests.post(f"http://{county}il.devnetwedge.com/Search/ExecuteSearch", data=d)

    current_year = int(r_current_year.url.split("/")[-1])

    last_year = str(current_year - 1)
    r_last_year_url = r_current_year.url.split("/")
    r_last_year_url[-1] = last_year
    r_last_year_url = "/".join(r_last_year_url)

    r_last_year = requests.get(r_last_year_url)


    soup = BeautifulSoup(r_current_year.text, 'html.parser')
    current_owner = soup.find_all('table')[0].find_all('div', {"class": "inner-value"})[2].text.split("\n")[0].split(",")
    current_owner.reverse()
    current_owner = " ".join(current_owner).strip()
    data['current_owner'] = f"The current owner of {args.address} is {current_owner}."


    df_current = pd.read_html(r_current_year.text)
    df_last = pd.read_html(r_last_year.text)


    tax_rate = df_last[0][1][4].replace("Tax Rate", "").strip()
    data['tax_rate'] = f"The tax rate last year for {args.address} was {tax_rate}%."

    for df in df_current:
        if str(df.columns.tolist()) in columns:
            x = columns[str(df.columns.tolist())]
            data[x['key']] = x['function'](df, args.address, current_year)


    print(data[args.q])

if __name__ == "__main__":
   # Create the parser and add arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(dest='address', help="1600 w pennslyvania ave")
    parser.add_argument(dest='q', help="what data do you want")


    # Parse and print the results
    args = parser.parse_args()
    get_property_tax_info(args)