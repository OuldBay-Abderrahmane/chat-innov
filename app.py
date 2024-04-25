import streamlit as st
from openai import OpenAI
import tiktoken
import pandas as pd
from scipy import spatial
import os  # Ensure os is imported
import pickle



import requests
import math
import os
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from selenium.webdriver.support import expected_conditions as EC
import time
import json

# Credentials
username = "KyvnScr"
password = "SVisBetterThanArchi"


class TwitterScrapper: 
    """

    Info:  Bot for scrapping important features of specific cryptocurrencies twitter account
    @attributes : username, password 
    @methods : login, scroll_and_fetch, save

    """
    def __init__(self, username, password):
        """

        Args:
            username: Twitter account username
            password: Twitter account password

        Returns:

        """
        self.username = username
        self.password = password
        service = Service()
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--incognito")
        self.driver = webdriver.Chrome(service=service, options=chrome_options)


    def login(self):
        """

        Args:
            self: TwitterScrapper object

        Returns:

        """
        driver = self.driver
        # Open Twitter
        try:
            driver.get("https://twitter.com/i/flow/login")
            WebDriverWait(driver, 250).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input')))
            print("Login appeared")
        except:
            print("Login did not appear")

        # Find the search input box and enter the user's handle
        try:
            username = driver.find_element(By.CSS_SELECTOR, 'input')
            username.send_keys(self.username)
            print('Found username')
            
            #Find next button 
            button = driver.find_element(By.XPATH, "//*[contains(text(),'Next')]")
            button.click()

        except:
            print('Did not found username field')

        try:
            # Find and enter password password
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'password')))
            password = driver.find_element(By.NAME, 'password')
            print('Found password')
            password.send_keys(self.password)
            time.sleep(3)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located(By.XPATH, "//*[contains(text(),'Log in')]"))
            password.send_keys(Keys.RETURN)  # click the ENTER key to login
            time.sleep(5)
        except:
            print("Did not find password field")

        try: 
            WebDriverWait(driver, 10000).until(EC.presence_of_element_located(By.XPATH, "//*[contains(text(),'Home')]"))
            print('Logged in')
        except:
            print('Log in problem - Maybe captcha or 2-step identification')

    def scroll_and_fetch(self):
        """

        Args:
            self: TwitterScrapper object
            account:  Cryptocurrency account to scrape

        Returns:
            infos: dictionnary with last tweets informations
        """
        infos = {"replies" : [], "retweets": [], "like" : [], "vues" : []}
        text = []
        try:
            # Advanced search
            self.driver.get("https://twitter.com/search?q=(%40Sunrise_de)&src=typed_query")
            time.sleep(3)
            WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(),'Latest')]"))).click()
        except:
            print("Did not found search bar")
        
        try:
            for i in range(1, 3):
                # Scroll down in order to load new tweets
                self.driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
                time.sleep(5)
        except:
            print("Can not scroll")
        
        try:
            # Iterate over a components to get all elements
            all_cards = self.driver.find_elements(By.CSS_SELECTOR, 'article')

            for card in all_cards:                
                card_text = card.find_elements(By.CSS_SELECTOR, 'span[data-testid="tweetText"]')
                text.append(card_text.text)

        except:
            print("Can't fetch all data points")    
        return text
    
    def convert_strings_to_numbers(self, string_list):
        converted_numbers = []
        try:
            for s in string_list:
                s = s.strip().upper().replace(',', '.')
                if s.endswith('K'):
                    converted_numbers.append(int(float(s[:-1]) * 1000))
                elif s.endswith('M'):
                    converted_numbers.append(int(float(s[:-1]) * 1000000))
                elif s.endswith('B'):
                    converted_numbers.append(int(float(s[:-1]) * 1000000000))
                else:
                    converted_numbers.append(int(float(s)))
        
            return converted_numbers
        except:
            return math.nan
    def fetch_account(self,bot):
        data = pd.DataFrame(columns=["data","replies","retweets","like","vues"])
        cwd = os.path.dirname(os.getcwd())
        infos = bot.scroll_and_fetch()
        return infos




#API_KEY = os.getenv('OPENAI_API_KEY')

#client = OpenAI(api_key=API_KEY)
client = OpenAI()

# Constants for model names
EMBEDDING_MODEL = "text-embedding-ada-002"
GPT_MODEL = "gpt-3.5-turbo"

def save_embeddings(embeddings, filename):
    with open(filename, 'wb') as f:
        pickle.dump(embeddings, f)

# Example of saving DataFrame to a pickle file
def create_and_save_embeddings(file_path):
    with open(file_path, 'r') as f:
        text = f.read()
    embedding_response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    embeddings = [embedding_response.data[0].embedding]
    df = pd.DataFrame({'text': [text], 'embedding': embeddings})
    save_embeddings(df, 'embeddings.pkl')  # Specify the filename
    return df

def load_embeddings(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

def strings_ranked_by_relatedness(query, df):
    query_embedding_response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query,
    )
    query_embedding = query_embedding_response.data[0].embedding
    strings_and_relatednesses = [
        (row["text"], 1 - spatial.distance.cosine(query_embedding, row["embedding"]))
        for i, row in df.iterrows()
    ]
    strings_and_relatednesses.sort(key=lambda x: x[1], reverse=True)
    strings, relatednesses = zip(*strings_and_relatednesses)
    return strings[:100], relatednesses[:100]

def num_tokens(text):
    encoding = tiktoken.encoding_for_model(GPT_MODEL)
    return len(encoding.encode(text))

def query_message(query, df, token_budget=4096 - 500):
    strings, relatednesses = strings_ranked_by_relatedness(query, df)
    message = 'Use the below articles to answer the subsequent question. If the answer cannot be found in the articles, write "I could not find an answer."'
    question = f"\n\nQuestion: {query}"
    for string in strings:
        next_article = f'\n\nArticle:\n"""\n{string}\n"""'
        if num_tokens(message + next_article + question) > token_budget:
            break
        else:
            message += next_article
    return message + question

def ask(query, df):
    message = query_message(query, df)
    messages = [
        {"role": "system", "content": "You answer questions about the text."},
        {"role": "user", "content": message},
    ]
    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=messages,
        temperature=0
    )
    return response.choices[0].message.content

def main():
    embeddings_file = 'embeddings.pkl'  # or 'embeddings.npy' for numpy
    try:
        username = "KyvnScr"
        password = "SVisBetterThanArchi"
        bot = TwitterScrapper(username, password)
        bot.login()
        data = bot.fetch_account(bot)
        st.text_area(data)
        df = load_embeddings(embeddings_file)
        st.write("Loaded embeddings from file.")
    except FileNotFoundError:
        st.write("Embeddings file not found. Creating new embeddings...")
        df = create_and_save_embeddings('data/d1.txt')  # Adjust as necessary for numpy

    user_input = st.text_input("Enter your query:", "")
    if st.button("Send") and user_input:
        response = ask(user_input, df)
        st.text_area("Response", response, height=300)

if __name__ == "__main__":
    main()
