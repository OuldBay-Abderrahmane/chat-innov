"""
# ------------- # <HEADERS> # ------------- #
# Description:
#   This script extract the main Twitter features for a given cryptocurrency:
#       1. comment, retweet, like, views
#
#   The goal is to use the numerical information for training model combined with the work on learning features
#   representation.
#
# Last revision: 18.08.2023
#
# ------------- # </HEADERS> # ------------- #
"""


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
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'css-18t94o4 ')))
            password.send_keys(Keys.RETURN)  # click the ENTER key to login
            time.sleep(5)
        except:
            print("Did not find password field")

        try: 
            WebDriverWait(driver, 10000).until(EC.presence_of_element_located(By.XPATH, "//*[contains(text(),'Home')]"))
            print('Logged in')
        except:
            print('Log in problem - Maybe captcha or 2-step identification')

    def scroll_and_fetch(self, account):
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
            self.driver.get("https://twitter.com/search?q=from%3A%40"+account+"&src=typed_query&f=top")
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
                card_infos = card.find_elements(By.CSS_SELECTOR, 'span[data-testid="app-text-transition-container"]')                
                if len(card_infos)==4:
                    infos["replies"].append(card_infos[0].text)
                    infos["retweets"].append(card_infos[1].text)
                    infos["like"].append(card_infos[2].text)
                    infos["vues"].append(card_infos[3].text)
                else:
                    infos["replies"].append(card_infos[0].text)
                    infos["retweets"].append(card_infos[1].text)
                    infos["like"].append(card_infos[2].text)
                card_text = card.find_elements(By.CSS_SELECTOR, 'span[data-testid="tweetText"]')
                text.append(card_text.text)

        except:
            print("Can't fetch all data points")    
        return [infos, text]
    
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
    def fetch_account(self, excel):
        data = pd.DataFrame(columns=["data","replies","retweets","like","vues"])
        cwd = os.path.dirname(os.getcwd())
        excel_data_df = pd.read_excel(os.path.dirname(cwd)+ excel, sheet_name='Sheet1')
        for i in range(len(excel_data_df.twitter_accounts)):
            crypto = excel_data_df.twitter_accounts[i].replace('https://twitter.com/', '')
            infos = bot.scroll_and_fetch(crypto)[1]
            replies = bot.convert_strings_to_numbers(infos["replies"])
            retweets = bot.convert_strings_to_numbers(infos["retweets"])
            like = bot.convert_strings_to_numbers(infos["like"])
            vues = bot.convert_strings_to_numbers(infos["vues"])
            current  = pd.DataFrame({"crypto":[crypto], "replies":[np.mean(replies)], "retweets":[np.mean(retweets)], "like":[np.mean(like)], "vues":[np.mean(vues)]})
            data.concat(current, ignore_index = True)
            data.to_csv('output.csv')
        return data


bot = TwitterScrapper(username, password)
bot.login()
excel ='/data/twitter_accounts_test.xlsx'
data = bot.fetch_account(excel)

data.to_csv('output.csv')