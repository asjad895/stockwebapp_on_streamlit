import time

import streamlit as st
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup, NavigableString
import pandas as pd
import plotly
import plotly.express as px
import streamlit_authenticator as stauth
import json  # for graph plotting in website
# NLTK VADER for sentiment analysis
from streamlit_lottie import st_lottie
import requests
from PIL import Image
import nltk
import database as db
import base64
from nltk.sentiment.vader import SentimentIntensityAnalyzer

nltk.downloader.download('vader_lexicon')
# authentication
if 'key' not in st.session_state:
    st.session_state['key'] = 'value'
    st.set_page_config(page_title="stock sentiment analysis", page_icon="random", layout="wide",initial_sidebar_state="expanded")
padding = 0


def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
        st.markdown(
            f"""
            <style>
            .stApp 
            {{.reportview-container .main .block-container{{
            padding-top: {padding}rem;
            padding-right: {padding}rem;
            padding-left: {padding}rem;
            padding-bottom: {padding}rem;
            background-image: url(data:image/{"png"};base64,{encoded_string.decode()});
            background-size: cover}}
            </style> """, unsafe_allow_html=True
        )


# image = Image.open('photo.jpeg')
add_bg_from_local('bg2.PNG')
# st.image(image, width=100)

# for extracting data from finviz
finviz_url = 'https://finviz.com/quote.ashx?t='

# --- USER AUTHENTICATION ---st.
users = db.fetch_all_users()  # my define function

usernames = [user["key"] for user in users]

names = [user["name"] for user in users]
hashed_passwords = [user["password"] for user in users]
credentials = {"usernames": {}}

for un, name, pw in zip(usernames, names, hashed_passwords):
    user_dict = {"name": name, "password": pw}
    credentials["usernames"].update({un: user_dict})

authenticator = stauth.Authenticate(credentials, "app_home", "key", cookie_expiry_days=30)

name, authentication_status, username = authenticator.login("Login", "sidebar")


# if st.session_state['authentication_status']:
#     authenticator.logout("logout", "sidebar")
#     st.write("Welcome * %s *" % (st.session_state['username']))

def get_news(tickers):
    url = finviz_url + tickers
    req = Request(url=url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'})
    response = urlopen(req)
    # Read the contents of the file into 'html'
    html = BeautifulSoup(response)
    # Find 'news-table' in the Soup and load it into 'news_table'
    news_tables = html.find(id='news-table')
    return news_tables

    # parse news into dataframe


def parse_news(news_tables):
    parsed_news = []
    for x in news_tables.findAll('tr'):
        # read the text from each tr tag into text
        # get text from a only
        text = x.a.get_text()
        # split text in the td tag into a list
        date_scrape = x.td.text.split()
        # if the length of 'date_scrape' is 1, load 'time' as the only element

        if len(date_scrape) == 1:
            times = date_scrape[0]

        # else load 'date' as the 1st element and 'time' as the second
        else:
            date = date_scrape[0]
            times = date_scrape[1]

        # Append ticker, date, time and headline as a list to the 'parsed_news' list
        parsed_news.append([date, times, text])
        # Set column names
        columns = ['date', 'times', 'headline']
        # Convert the parsed_news list into a DataFrame called 'parsed_and_scored_news'
        parsed_news_df = pd.DataFrame(parsed_news, columns=columns)
        # Create a pandas datetime object from the strings in 'date' and 'time' column
        parsed_news_df['datetime'] = pd.to_datetime(parsed_news_df['date'] + ' ' + parsed_news_df['times'])

    return parsed_news_df


def score_news(parsed_news_df):
    # Instantiate the sentiment intensity analyzer
    vader = SentimentIntensityAnalyzer()

    # Iterate through the headlines and get the polarity scores using vader
    scores = parsed_news_df['headline'].apply(vader.polarity_scores).tolist()

    # Convert the 'scores' list of dicts into a DataFrame
    scores_df = pd.DataFrame(scores)

    # Join the DataFrames of the news and the list of dicts
    parsed_and_scored_news = parsed_news_df.join(scores_df, rsuffix='_right')
    parsed_and_scored_news = parsed_and_scored_news.set_index('datetime')
    parsed_and_scored_news = parsed_and_scored_news.drop(['date', 'times'], 1)
    parsed_and_scored_news = parsed_and_scored_news.rename(columns={"Headline": "sentiment_score"})

    return parsed_and_scored_news


def plot_hourly_sentiment(parsed_and_scored_news, ticker):
    # Group by date and ticker columns from scored_news and calculate the mean
    mean_scores = parsed_and_scored_news.resample('H').mean()

    # Plot a bar chart with plotly
    fig = px.bar(mean_scores, x=mean_scores.index, y='sentiment_score', title=ticker + ' Hourly Sentiment Scores')
    return fig


def plot_daily_sentiment(parsed_and_scored_news, ticker):
    # Group by date and ticker columns from scored_news and calculate the mean
    mean_scores = parsed_and_scored_news.resample('D').mean()

    # Plot a bar chart with plotly
    fig = px.bar(mean_scores, x=mean_scores.index, y='sentiment_score', title=ticker + ' Daily Sentiment Scores')
    return fig

    # animation = "https://iconscout.com/lotties/hello-october"
    # anim_json = load_lotti(animation)
    # st_lottie(anim_json)


if st.session_state['authentication_status']:
    authenticator.logout("logout", "sidebar")
    st.write("Welcome * %s *" % (st.session_state['username']))

    st.header("Stock News Sentiment Analyzer")

    ticker = st.text_input('Enter Stock Ticker', '').upper()
    # op = st.selectbox("select analysis", ["hourly", "daily"])

    try:
        st.success("Hourly and Daily Sentiment of {} Stock".format(ticker))
        news_table = get_news(ticker)
        parsed_news_df = parse_news(news_table)
        parsed_and_scored_news = score_news(parsed_news_df)
        fig_hourly = plot_hourly_sentiment(parsed_and_scored_news, ticker)
        fig_daily = plot_daily_sentiment(parsed_and_scored_news, ticker)

        if st.checkbox("hourly analysis"):
            st.plotly_chart(fig_hourly)
            st.balloons()
        if st.checkbox("daily analysis"):
            st.plotly_chart(fig_daily)
            st.balloons()
        with st.spinner("something exciting....."):
            time.sleep(5)
        st.balloons()

        description = """he above chart averages the sentiment scores of {} stock hourly and daily.The table below gives each of the most recent headlines of the stock and the negative, neutral, positive and an aggregated sentiment score.
        The news headlines are obtained from the FinViz website.Sentiments are given by the nltk.sentiment.vader Python library.""".format(ticker)

        st.success(description)
        st.table(parsed_and_scored_news)
    except():
        st.warning("Enter a correct stock ticker, e.g. 'AAPL' above and hit Enter.")
        st.info("if you want to explore ticker then click below link")

if not authentication_status:
    st.error("Username/password is incorrect")

if authentication_status is None:
    st.warning("Please enter your username and password")
    with st.sidebar:
        if st.button('about'):
            st.write(' i am an data science enthusiast')
