# -*- coding: utf-8 -*-
"""Stockscreener_try1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1V8tOtPdPZp6ljXP2rNP-n-tdg5zie9Qn
"""

#!pip install yfinance
#!pip install beautifulsoup4 requests
#!pip install requests-cache #for caching Yahoo finance data
#!pip install dash

#General Imports

import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

def get_available_fields(symbol):
    try:
        # Create a Yahoo Finance Ticker object for the specified stock symbol
        ticker = yf.Ticker(symbol)

        # Get the info attribute, which contains available fields
        info = ticker.info
        # Convert the info dictionary to a Pandas DataFrame with fields as columns
        df = pd.DataFrame([info])

        return df

    except Exception as e:
        print(f"Error fetching data for {symbol}: {str(e)}")

stock_symbol = 'AAPL'
stock_data = get_available_fields(stock_symbol)
columns = pd.DataFrame()
if stock_data is not None:
    columns['columns'] = (stock_data.columns)
columns

import requests
from bs4 import BeautifulSoup

# Define the URL of the Wikipedia page for SPY
wiki_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'

# Send an HTTP GET request to the Wikipedia page
response = requests.get(wiki_url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the table containing the list of stock symbols
    symbol_table = soup.find("table", {"id": "constituents"})

    if symbol_table:
        # Extract the stock symbols from the table
        symbols = []
        for row in symbol_table.find_all("tr")[1:]:
            columns = row.find_all("td")
            if len(columns) >= 2:
                symbol = columns[0].text.strip()
                symbols.append(symbol)

        # Print the list of stock symbols
        #print("List of stock symbols in SPY:")
        #for symbol in symbols:
        #   print(symbol)
    else:
        print("Table with stock symbols not found on the Wikipedia page.")
else:
    print("Failed to retrieve the Wikipedia page.")

# Use the extracted symbols to create the list of all_stocks
all_stocks = [f'{symbol}' for symbol in symbols]

# Only run once a day to confirm the sector list.
# Set to store unique sectors
def unique_sectors():
      unique_sectors = set()

      for symbol in all_stocks:
          stock = yf.Ticker(symbol)
          info = stock.info
          if "sector" in info:
              sector = info["sector"]
              unique_sectors.add(sector)

      # Convert the set of unique sectors to a list if needed
      #unique_sectors_list = list(unique_sectors)
      return unique_sectors_list


unique_sectors_list = [
    'Consumer Cyclical',
    'Industrials',
    'Utilities',
    'Technology',
    'Real Estate',
    'Communication Services',
    'Healthcare',
    'Basic Materials',
    'Financial Services',
    'Energy',
    'Consumer Defensive'
]


# Define the market cap size categories and their thresholds
market_cap_categories = {
    'Micro-Cap': (0, 300),    # In millions
    'Small-Cap': (300, 2000), # In millions
    'Mid-Cap': (2000, 10000), # In millions
    'Large-Cap': (10000, float('inf')),  # In millions
    'Mega-Cap': (50000, float('inf'))   # In millions (adjust threshold as needed)
}

# Create a list of labels for the slider
market_cap_labels = list(market_cap_categories.keys())
# Create a list of dollar values corresponding to each market cap category
market_cap_dollar_values = [' Micro-Cap ($0M - $300M)', 'Small-Cap ($300M - $2B)', 'Mid-Cap ($2B - $10B)', 'Large-Cap ($10B - $50B)', 'Mega-Cap ($50B+)']

# Create a list of marks for the slider based on the labels
slider_marks = {i: label for i, label in enumerate(market_cap_dollar_values)}

# Print the unique sectors
print("Unique Sectors:")
for sector in unique_sectors_list:
    print(sector)

market_cap_map_min = {0: '0M', 1: '300M', 2: '2B', 3: '10B', 4: '50B'}
market_cap_map_max = {0: '300M', 1: '2B', 2: '10B', 3: '50B', 4:'inf'}
print(slider_marks)

# Convert market cap string to numeric value
def market_cap_to_numeric(market_cap_str):
    if market_cap_str.lower() =='inf':
        return float('inf')
    elif "B" in market_cap_str:
        return float(market_cap_str.replace("B", "").strip()) * 1e9  # Convert to numerical value in dollars
    elif "M" in market_cap_str:
        return float(market_cap_str.replace("M", "").strip()) * 1e6  # Convert to numerical value in dollars
    else:
        return 0

# Define a function to format market cap
def market_cap_to_nonumeric(market_cap):
    if market_cap >= 1_000_000_000:  # Billion
        return f'{market_cap / 1_000_000_000:.2f} B'
    elif market_cap >= 1_000_000:  # Million
        return f'{market_cap / 1_000_000:.2f} M'
    else:
        return f'{market_cap:.2f}'

#Add caching to speed up the requests to Yahoo finance
import requests_cache

# Enable caching and specify the cache file name
cache_filename = 'yahoo_finance_cache'
expire_after = 3600  # Cache data for 1 hour (adjust as needed)

# Configure requests to use the cache
requests_cache.install_cache(cache_filename, expire_after=expire_after)

# Filter stocks based on your criteria
def filter_stocks(sector, market_cap_min, market_cap_max):

    max_pe_ratio = 15
    min_market_cap = market_cap_to_numeric(market_cap_min)
    max_market_cap = market_cap_to_numeric(market_cap_max)
    print(min_market_cap,'-', max_market_cap)
    filtered_stocks = []
    for stock_symbol in all_stocks:
        stock = yf.Ticker(stock_symbol)
        info = stock.info
        if isinstance(info, dict):
            #Check if sector exists
            sector_info = info.get('sector', None)
            if sector_info is None:
                continue
            #Check if marketCap exists
            market_cap = info.get('marketCap', None)
            if market_cap is None or not isinstance(market_cap, (int, float)):
                # Skip this stock if 'marketCap' is missing or not a valid number
                continue
            # Check if 'trailingPE' exists and is a valid number
            trailing_pe = info.get('trailingPE', None)
            if trailing_pe is None or not isinstance(trailing_pe, (int, float)):
                # Skip this stock if 'trailingPE' is missing or not a valid number
                continue
            if (
                  info['sector'] == sector
                  and info.get('marketCap', 0) >= min_market_cap
                  and info.get('marketCap', 0) <= max_market_cap
                  and info['trailingPE'] <= max_pe_ratio
              ):
                  filtered_stocks.append(stock)
        else:
           print(f"Error processing stock {stock_symbol}: Invalid 'info' data")


    stock_info_list = []
    for stock in filtered_stocks:
      # Get stock info as a dictionary
      stock_info = stock.info
      # Append the stock info dictionary to the list
      stock_info_list.append(stock_info)
    #Convert to a data frame
    filtered_stocks_df = pd.DataFrame(stock_info_list)

    #Add some columms for easier reading
    filtered_stocks_df['formattedMarketCap'] = filtered_stocks_df.apply(lambda row: market_cap_to_nonumeric(row['marketCap']) if 'marketCap' in row else None, axis=1)


    return filtered_stocks_df

"""1. Consumer Cyclical
2. Industrials
3. Utilities
4. Technology
5. Real Estate
6. Communication Services
7. Healthcare
8. Basic Materials
9. Financial Services
10. Energy
11. Consumer Defensive

market_cap_map_min = {0: '0M', 1: '300M', 2: '2B', 3: '10B', 4: '50B'}

market_cap_map_max = {0: '300M', 1: '2B', 2: '10B', 3: '50B', 4:'inf'}
"""

#selected_sector = 'Financial Services'
##selected_sector = 'Technology'
##filtered_stocks_df = filter_stocks(selected_sector, '2B', '10B')

len(filtered_stocks_df)

# Create a TreeMap using Plotly with the dark theme
if filtered_stocks_df.empty:
    fig = px.scatter(title='No matching stocks found')
else:
    fig = px.treemap(
        filtered_stocks_df,
        path=['symbol'],
        values='marketCap',
        title='Stock Market Capitalization',
        template="plotly_dark"  # Set the dark theme
    )

    # Customize the appearance of the TreeMap
    fig.update_traces(
        text= '<br>Market Cap: $' +  filtered_stocks_df['formattedMarketCap'] + '<br>P/E Ratio: ' + filtered_stocks_df['trailingPE'].astype(str),
        textinfo="label+text",
        hoverinfo="label+text",
    )

    fig.update_traces(
        marker=dict(
            colors=filtered_stocks_df['trailingPE'],
            colorbar=dict(title='Trailing P/E'),
            colorscale='ylorrd',  # Use the "Plasma_r" color scale
            line=dict(width=2, color='black')
        )
    )

# Show the TreeMap
fig.show()

import dash
from dash import dcc, html, Input, Output, callback

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# Create a Dash app
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
# Define the app layout
app.layout = html.Div([

#Sector selection dropdown

    dcc.Dropdown(
        id='sector-dropdown',
        options=[{'label': sector, 'value': sector} for sector in unique_sectors_list],
        value=unique_sectors_list[0] if unique_sectors_list else None  # Default sector if available
    ),

#Treemap component
    dcc.Graph(
        id='treemap',
        config={'displayModeBar': False},  # Hide the Plotly mode bar
    ),

# Min Market Cap Slider
    #html.H6("Select Min Market Cap Filter"),
    dcc.Slider(
        id='min-market-cap-slider',
        min=0,  # Minimum market cap value
        max=len(market_cap_labels) - 1,  # Maximum market cap value
        step=1,  # Step size
        value=2,  # Initial value
        marks=slider_marks,  # Custom marks for labels
        tooltip={'placement': 'bottom', 'always_visible': True},
        ),

# Max Market Cap Slider
    #html.H6("Select Max Market Cap Filter"),
    dcc.Slider(
        id='max-market-cap-slider',
        min=0,  # Minimum market cap value
        max=len(market_cap_labels) - 1,  # Maximum market cap value
        step=1,  # Step size
        value=2,  # Initial value
        marks=slider_marks,  # Custom marks for labels
        tooltip={'placement': 'bottom', 'always_visible': True},
        ),
])



# Define a callback to update the treemap based on the selected sector
@callback(
    Output('treemap', 'figure'),
    Input('sector-dropdown', 'value'),
    Input('min-market-cap-slider', 'value'),
    Input('max-market-cap-slider', 'value')
)
def update_treemap(selected_sector, min_slider_value, max_slider_value):

    #market_cap_min = market_cap_map_min[slider_value]
    #market_cap_max = market_cap_map_max[slider_value]
    #filtered_stocks_df = filter_stocks(selected_sector, market_cap_min, market_cap_max)
    market_cap_min = market_cap_map_min[min_slider_value]
    market_cap_max = market_cap_map_max[max_slider_value]
    filtered_stocks_df = filter_stocks(selected_sector, market_cap_min, market_cap_max)

    if filtered_stocks_df.empty:
        # Handle the case where there are no matching stocks
        # You can display a message or a placeholder graph
        fig = px.scatter(title='No matching stocks found')
    else:
        # Create a TreeMap using Plotly
        fig = px.treemap(
            filtered_stocks_df,
            path=['symbol'],
            values='marketCap',
            title=f'Stock Market Capitalization - {selected_sector}',
            template="plotly_dark"  # Set the dark theme
        )

        # Customize the appearance of the TreeMap (similar to previous code)
        fig.update_traces(
            text= '<br>Market Cap: $' +  filtered_stocks_df['formattedMarketCap'] + '<br>P/E Ratio: ' + filtered_stocks_df['trailingPE'].astype(str),
            textinfo="label+text",
            hoverinfo="label+text",
        )

        # Color scale with P/E
        fig.update_traces(
            marker=dict(
                colors=filtered_stocks_df['trailingPE'],
                colorbar=dict(title='Trailing P/E'),
                colorscale='ylorrd',
                line=dict(width=2, color="white")
            )
        )

    return fig



# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
