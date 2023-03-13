# Get Strava Data Through Postman API Call
# https://towardsdatascience.com/using-the-strava-api-and-pandas-to-explore-your-activity-data-d94901d9bfde
# https://github.com/franchyze923/Code_From_Tutorials/blob/master/Strava_Api/strava_api.py

import requests
import urllib3
import pandas as pd
import duckdb as db
from pandas.io.json import json_normalize
import streamlit as st
from datetime import date, datetime
import plotly.express as px
import plotly.graph_objects as go

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# set api endpoint variables
auth_url = "https://www.strava.com/oauth/token"
activites_url = "https://www.strava.com/api/v3/athlete/activities"

# retrieve api secrets
# if the app is being run on streamlit prod, use streamlit cloud encrypted secrets
# else, the app is being run locally on dev, use secrets from the secrets.toml file

client_id = st.secrets.strava_api_secrets.client_id
client_secret = st.secrets.strava_api_secrets.client_secret
refresh_token = st.secrets.strava_api_secrets.refresh_token

payload = {
    'client_id': client_id,
    'client_secret': client_secret,
    'refresh_token': refresh_token,
    'grant_type': "refresh_token",
    'f': 'json'
}
res = requests.post(auth_url, data=payload, verify=False)

access_token = res.json()['access_token']
header = {'Authorization': 'Bearer ' + access_token}

# initialize pagination start and all activities list

@st.cache_data(show_spinner=False)
def get_strava_data():
    request_page_num = 1
    all_activities = []

    while True:
        param = {'per_page': 200, 'page': request_page_num}
        my_dataset = requests.get(activites_url, headers=header, params=param).json()

        if len(my_dataset) == 0:
            # no more activities to append
            break

        if all_activities:
            # the all_activities list already exists and we can add to it
            all_activities.extend(my_dataset)

        else:
            # the all_activities list doesn't exist yet and there is data to add
            all_activities = my_dataset
            
        request_page_num +=1

    # normalize data set
    df_all_activities = pd.json_normalize(all_activities)
    return df_all_activities

def get_available_activities_df(start_date, end_date):
    available_activities_query = f"""
    select distinct type 
    from df_all_activities
    where start_date_local between '{start_date}' and '{end_date}'
    """
    available_activities_df = db.query(available_activities_query).to_df()
    return available_activities_df

def get_activity_timeline():
    activity_timeline_query = f"""
    select
        min(start_date_local)::date as first_activity,
        max(start_date_local)::date as last_activity
    from df_all_activities
    """
    available_activities_df = db.query(activity_timeline_query).to_df()
    return available_activities_df

def create_date_spine(start_date, end_date):
    df = pd.DataFrame({"Date": pd.date_range(start_date, end_date)})
    return df

def metric_query(metric,aggregate,slice,date_grain,time_period=None,min_date=None,max_date=None):

  # create a select statement
  if slice != "":
    select_statement = f"""
    select
      date_trunc('{date_grain}', ds.date) as "date",
      a.{slice} as "{slice}",
      {aggregate}(coalesce({metric}, 0)) as "{aggregate}_{metric}"
    """
  
  else:
    select_statement = f"""
    select
      date_trunc('{date_grain}', ds.date) as "date",
      {aggregate}(coalesce({metric}, 0)) as "{aggregate}_{metric}"
    """
  
  # create a from statement
  from_statement = f"""
  from df_date_spine as ds
    left join df_all_activities as a
    on ds.date = a.start_date_local::date
  """

  # create a where statement
  if time_period == "year_to_date":
    where_statement = f"""
    where date_trunc('year', ds.date) = date_trunc('year', current_date())
    """

  elif time_period == "last_12_months":
    where_statement = f"""
    where ds.date > date_trunc('month', current_date()) - interval 12 month
    """

  elif time_period == "last_6_months":
    where_statement = f"""
    where ds.date > date_trunc('month', current_date()) - interval 6 month
    """

  elif time_period == "last_3_months":
    where_statement = f"""
    where ds.date > date_trunc('month', current_date()) - interval 3 month
    """

  elif time_period == "last_1_month":
    where_statement = f"""
    where ds.date > date_trunc('month', current_date()) - interval 1 month
    """

  else:
    where_statement = ""
  
  # create a group by statement start_date and end_date
  if slice != "":
    group_by_statement = """
    group by 1,2
    """
  else:
    group_by_statement = """
    group by 1
    """

  # order by statement -- static for now
  order_by_statement = """
  order by 1 desc
  """

  query_string = select_statement + from_statement + where_statement + group_by_statement + order_by_statement
  return query_string

def main():
    
    # page configs
    st.set_page_config(
        page_title="[Strava Metrics App](https://github.com/jgarbier/strava-data-app)",
    )
    st.header('Strava Metrics App')
    st.caption('Created by [James Garbier](https://github.com/jgarbier)')
    
    how_to_string = f"""
        1. Pick your `Metric`
        2. Choose how to `Aggregate` your metric
        3. `Slice` your metric by a specific dimension, or leave as a total
        4. Pick the `Date Grain` for your time series chart
        5. Select the `Time Period` to measure the metric over
        6. If you've selected a `Slice`, toggle between `Stacked or Grouped` bars
    """
    
    with st.expander('How to Use'):
      st.markdown(how_to_string)

    # first, retrieve strava data
    with st.spinner('Loading Activities...'):
        df_all_activities = get_strava_data()

    first_activity = get_activity_timeline()["first_activity"]
    last_activity = get_activity_timeline()["last_activity"]
    first_activity_str = first_activity.dt.strftime("%Y-%m-%d").to_string(index=False)
    last_activity_str = last_activity.dt.strftime("%Y-%m-%d").to_string(index=False)
    df_date_spine = create_date_spine(first_activity_str, last_activity_str)

    # input dictionaries

    metric_dict = {
      "Miles": "distance/1609",
      "Time (Minutes)": "moving_time/60",
      "Activities": "id",
      "Kudos": "kudos_count",
      "Elevation": "total_elevation_gain"
    }

    aggregation_dict = {
      "Total": "sum", 
      "Average": "avg",
      "Max": "max",
      "Min": "min",
      "Count": "count"
    }

    slice_dict = {
      "None": "", 
      "by Activity Type": "type",
    }

    date_grain_dict = {
      "Daily": "day",
      "Weekly": "week",
      "Monthly": "month",
      "Yearly": "year"
    }

    time_period_dict = {
      "Year to Date": "year_to_date",
      "Last 12 Months": "last_12_months",
      "Last 6 Months": "last_6_months",
      "Last 3 Months": "last_3_months",
      "Last Month": "last_1_month",
      "All Time": "all_time"
    }
    
    # inputs
    with st.sidebar:

      metric_input = st.selectbox(
        "Metric",
        list(metric_dict.keys())
        )

      aggregate_input = st.selectbox(
        "Aggregation",
        list(aggregation_dict.keys())
        )

      slice_input = st.selectbox(
        "Slice",
        list(slice_dict.keys())
        )

    col1, col2, col3 = st.columns(3)

    with col1:

      date_grain_input = st.selectbox(
        "Date Grain",
        list(date_grain_dict.keys())
        )

    with col2:

      time_period_input = st.selectbox(
        "Time Period",
        list(time_period_dict.keys())
        )

    with col3:
      chart_style = st.radio(
        "Stack or Group",
        ('Stack', 'Group')
        )

    metric_query_input = (
      metric_query(
        metric=metric_dict[metric_input],
        aggregate=aggregation_dict[aggregate_input],
        slice=slice_dict[slice_input],
        date_grain=date_grain_dict[date_grain_input],
        time_period=time_period_dict[time_period_input]
      )
    )

    df = db.query(metric_query_input).to_df()

    metric_name = aggregation_dict[aggregate_input] + '_' + metric_dict[metric_input]
    chart_slice = slice_dict[slice_input]

    
    if chart_slice != "" and chart_style == "Stack":
      plotly_fig = px.bar(
        df,
        x='date',
        y=metric_name,
        color=chart_slice,
        barmode='stack'
        )

    elif chart_slice != "" and chart_style == "Group":
      plotly_fig = px.bar(
        df,
        x='date',
        y=metric_name,
        color=chart_slice,
        barmode='group'
        )
        
    else:
      plotly_fig = px.bar(
        df,
        x='date',
        y=metric_name,
        )
    
    st.plotly_chart(plotly_fig)

    see_df = st.checkbox(
      "Show Raw Data"
    )

    if see_df:
      st.table(
        data=df
        )
    
    see_query = st.checkbox(
      "Show Query"
      )

    if see_query:
      st.code(
        metric_query_input,
        'sql'
      )
    
    st.subheader('Powered by Strava Data and Streamlit')

main()
