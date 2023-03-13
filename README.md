### Strava BI Tool

## About
This is a lightweight BI tool built with [Streamlit](https://streamlit.io/) and [DuckDB](https://duckdb.org/)
to analyze [Strava data](https://www.strava.com/athletes/50151776).

<b>Strava</b> is a social media app that connects athletes. It's where individuals can upload and track activity data.
This app connects to [Strava's API](https://developers.strava.com/) to analyze my my personal activity logs.

<b>Streamlit</b> is a Python library for creating data applications.

<b>DuckBD</b> is a serverless SQL query engine, designed for OLAP workloads

## How to use
1. Pick your `Metric`
2. Choose how to `Aggregate` your metric
3. `Slice` your metric by a specific dimension, or leave as a total
4. Pick the `Date Grain` for your time series chart
5. Select the `Time Period` to measure the metric over
6. If you've selected a `Slice`, toggle between `Stacked or Grouped` bars

## Want to run analysis locally for your own activities?
1. Clone this `/strava-data-app` repo to your local machine
2. Spin up the virtual environment at the root of the directory
  ```bash
  pipenv shell
  ```
3. Create a `.streamlit` file with API credentials
  ```
  client_id = {your_client_id}
  client_secret = '{your_secret_key}'
  refresh_token = '{your_refresh_token}'
  ```
  - [Instructions](https://developers.strava.com/docs/getting-started/) on how to retrieve API credentials
4. Run the streamlit app
  ```bash
  streamlit run main.py
  ```
