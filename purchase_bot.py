# -*- coding: utf-8 -*-
"""
Created on Sat Dec 26 14:17:37 2020

@author: rikus

This Selenium-based bot will log into k-ruoka.fi and buy your groceries for you.
It will user the parameters given in items_to_buy.py to find the cheapest products
and add them to your cart. In the end it will send you a summary of what happened
to your email.
"""


from items_to_buy import *
from mail_env_vars import *
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from email.message import EmailMessage # the base class for the email object model
import pandas as pd
import time
import smtplib # defines an SMTP client session object that can be used to send mail

# Alle käyttämäsi Firefox-selaimen profiilin tiedostopolku.
ff_profile_path = FILE PATH TO THE FIREFOX PROFILE YOU WANT TO USE
summary_email_address = EMAIL ADDRESS WHERE YOU WANT SUMMARY TO BE SENT AFTER CODE HAS RUN

# Määritetään webdriverin asetukset
driver_options = Options()
driver_options.headless = True
profile = webdriver.FirefoxProfile(ff_profile_path)
driver = webdriver.Firefox(profile, options=driver_options)
driver.implicitly_wait(5)


driver.get("https://www.k-ruoka.fi/kauppa/tuotehaku")


def searchItem(search_term, category):
    """
    Tekee haun K-Ruokaan hakusanoilla search_term.
    """
    assert type(search_term) == str, "search_term should be a string"
    assert type(category) == str, "category should be a string"
    
    driver.get("https://www.k-ruoka.fi/kauppa/tuotteet")
    time.sleep(2)
    
    # Valitaan hakukategoria
    category_element_path = f'//*[text()="{category}"]'
    category_element = driver.find_element_by_xpath(category_element_path)
    category_element.click()
    time.sleep(2)
    
    # Etsitään hakusanalla
    search_field_path = '//input[@type="search"]'
    search_field = driver.find_element_by_xpath(search_field_path)
    search_field.send_keys(search_term)


def scrollAllItems():
    """
    Vierittää hakusivua alas, kunnes kaikki haun tuotteet ovat näkyvillä.
    """
    scroll_pause = 2
    while True:
        elems = driver.find_elements_by_class_name("bundle-list-item")
        num_of_elems_first = len(elems)
        try:
            show_all_path = '//*[text()="Lataa lisää"]'
            show_all_element = driver.find_element_by_xpath(show_all_path)
            show_all_element.location_once_scrolled_into_view
        except:
            break
        time.sleep(scroll_pause)
        elems = driver.find_elements_by_class_name("bundle-list-item")
        num_of_elems_second = len(elems)
        if num_of_elems_first == num_of_elems_second:
            break


def fetchItemInfo():
    """
    Lataa sivun kaikki tuotetiedot dictiin muotoon:
        tuotenumero : (nimi, hinta)
        
    Palauttaa dictin.
    """
    search_results_dict = {}
    # jokainen tuote löytyy html-luokasta nimeltä "bundle-list-item"
    items_selenium = driver.find_elements_by_class_name("bundle-list-item")
    # iteroidaan kaikki tuotteet
    for item in items_selenium:
        # haetaan xpath-osoitteella tuotenumero
        # "." polun alussa tarkoittaa, että suoritetaan etsintä annetun html-luokan scopessa
        temp = item.find_element_by_xpath(".//div[contains(@id,'product-result')]")
        temp = temp.get_attribute("id")
        index = temp.find("item")
        item_list = item.text.split("\n")
        
        item_number = temp[index+5:]
        item_name = item_list[0]
        item_price = item_list[-1]
        
        # Jos tuotteelle ei löydy järkevää hintaa edellä mainitulla tavalla, koitetaan se
        # kaivaa esiin näin.
        if item_price[0] == "/":
            price_integer_part = item.find_element_by_class_name("price-integer-part").text
            price_fractional_part = item.find_element_by_class_name("price-fractional-part").text
            pricing_unit = item.find_element_by_class_name("pricing-unit").text
            item_price = f"{price_integer_part},{price_fractional_part}/{pricing_unit}"
        
        try:
            search_results_dict[item_number] = (item_name, item_price)
        except:
            pass
    
    return search_results_dict


def convertToDF(search_results_dict):
    """
    Ottaa search_results_dict (dict)
    Palauttaa tuon tiedoston muutettuna dataframeksi, jossa on pylväät:
        "Tuotenimi", "Hinta", "Yksikkö"
    """
    assert type(search_results_dict) == dict, "search_results_dict should be a dict"
    
    # Asettaa Pandasin näyttämään kaikki DF-objektin pylväät konsolissa
    pd.set_option('display.expand_frame_repr', False)
    # Asettaa Pandasin näyttämään x määrän rivejä ennen kuin lyhentää
    pd.set_option('display.max_rows', 250)
    
    # Tuodaan dict DF-objektiin
    temp_df = pd.DataFrame.from_dict(search_results_dict, orient="index", columns=["Tuotenimi", "Hinta"])
    
    # Rakennetaan uusi index
    temp_df = temp_df.reset_index(drop=False)
    
    # Nimetään vanha index-pylväs uudestaan
    temp_df = temp_df.rename(columns={"index" : "Tuotenumero"})
    
    # Luodaan uusi df, jossa "Hinta"-pylväs on jaettu "/" tai " "-merkin perusteella 
    # (regular expression)
    price_columns_df = temp_df["Hinta"].str.split(r"/|\s", expand=True) # 
    
    # Korvataan alkuperäisestä df "Hinta"-pylväs pelkällä hinnalla ja siirretään
    # yksikkötieto uuteen pylvääseen nimeltä "Yksikkö".
    temp_df["Hinta"] = price_columns_df[0]
    temp_df["Yksikkö"] = price_columns_df[1]
    
    # Poistetaan rivit, joidenka "Yksikkö"-tieto on "None".
    length = temp_df.shape[0]
    rows_to_drop = []
    for i in range(length):
        yksikkö = temp_df["Yksikkö"][i]
        if yksikkö == "None":
            rows_to_drop.append(i)
    temp_df.drop(rows_to_drop)
    temp_df = temp_df.reset_index(drop=True)
    
    # Muutetaan hinnat str -> float, jotta ne voidaan sortata
    length = temp_df.shape[0]
    for i in range(length):
        price_cell = temp_df["Hinta"][i]
        
        hinta_edit = price_cell.replace(",", ".")
        hinta_edit2 = float(hinta_edit)
        temp_df["Hinta"][i] = hinta_edit2
        
    temp_df = temp_df.sort_values("Hinta")
    temp_df = temp_df.reset_index(drop=True)
    search_results_df = temp_df
    
    return search_results_df


def getCheapestItem(search_results_df, price_constraint, unit_constraint):
    """
    search_results_df: DF-objekti, jossa pylväät "Tuotenumero", "Tuotenimi", "Hinta", "Yksikkö"
    price_constraint: korkein hyväksytty hinta tuottelle (int)
    unit_constraint: onko tuotteen hinta per "kg", "kpl" vai "l"
    
    Palauttaa halvimman tuotteen, joka täyttää ehdot. Muussa tapauksessa palauttaa None
    """
    assert type(search_results_df) == pd.core.frame.DataFrame, "search_results_df should be a pandas dataframe"
    assert type(price_constraint) == int or type(price_constraint) == float, "price_constraint should be an int or float"
    assert price_constraint > 0, "price_constraint should be >0"
    assert type(unit_constraint) == str, "unit_constraint should be a string"
    assert unit_constraint == "kg" or unit_constraint == "l" or unit_constraint == "kpl", "unit_constraint should be kg/l/kpl"
    
    return_index = -1
    length = search_results_df.shape[0]
    for i in range(length):
        price = search_results_df["Hinta"][i]
        unit = search_results_df["Yksikkö"][i]
        if price < price_constraint and unit == unit_constraint:
            return_index = i
            break
    if return_index < 0:
        return None
    else:
        cheapest_item_df = search_results_df.iloc[return_index,:]
        return cheapest_item_df


def addToCart(product_number):
    """
    Lisää tuotteen ostoskoriin.
    """
    product_html_id = f"product-result-item-{product_number}"
    product_html_element = driver.find_element_by_id(product_html_id)
    add_to_cart_xpath = '//button[@title="Lisää"]'
    add_to_cart_element = product_html_element.find_element_by_xpath(add_to_cart_xpath)
    add_to_cart_element.click()


def cheapestItemToString(cheapest_item_df):
    """
    Muutetaan cheapest_item_df (dataframe) stringiksi.
    """
    assert type(cheapest_item_df) == pd.core.series.Series, "cheapest_item_df should be a pandas series"
    
    item_number = str(cheapest_item_df["Tuotenumero"])
    item_name = str(cheapest_item_df["Tuotenimi"])
    item_price = str(cheapest_item_df["Hinta"])
    item_unit = str(cheapest_item_df["Yksikkö"])
    cheapest_item_str = f"{item_number}; {item_name}; {item_price}; {item_unit}"
    return cheapest_item_str


def composeSummary(items_found, items_not_found):
    """
    Luodaan yhteenveto ostotapahtumista (str)
    
    items_found: lista stringejä
    items_not_found: lista stringejä
    """
    assert type(items_found) == list, "items_found should be a list"
    assert type(items_not_found) == list, "items_not_found should be a list"
    if len(items_found) > 0:
        assert type(items_found[0]) == str, "items_found should be a list of strings"
    if len(items_not_found) > 0:
        assert type(items_not_found[0]) == str, "items_not_found should be a list of strings"
    
    # Luodaan yhteenveto ostotapahtumista
    summary = ""
    
    found_title = "Nämä tuotteet lisättiin ostoskoriin:\n"
    summary += found_title + "\n"
    if len(items_found) > 0:
        for item in items_found:
            summary += item + "\n"
    else:
        summary += "<tyhjä>\n"
    
    not_found_title = "\nNäillä hakutermeillä ei löydetty mitään:\n"
    summary += not_found_title + "\n"
    if len(items_not_found) > 0:
        for item in items_not_found:
            summary += item + "\n"
    else:
        summary += "<tyhjä>\n"

    return summary


def sendToMail(summary, summary_email_address):
    """
    Lähetetään yhteenveto ostotapahtumista valittuun s-postiin summary_email_address
    
    summary: yhteenveto ostotapahtumista (str)
    summary_email_address: s-postiosoite, johon yhteenveto halutaan (str)
    """
    assert type(summary) == str, "summary should be a string"
    assert type(summary_email_address) == str, "summary_email_address should be a string"
    
    msg = EmailMessage()
    msg["Subject"] = "Ostoskorisi osoitteessa k-ruoka.fi"
    msg["From"] = getMailUser()
    msg["To"] = summary_email_address
    msg.set_content(summary)
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp: # SSL-salauksella portin tulee olla 465
        smtp.login(getMailUser(), getMailPass()) # haetaan kirjautumistiedot environment variablesista
        smtp.send_message(msg)


def buy(shopping_list):
    """
    Ottaa ostoslistan (list), etsii jokaisesta tuotteesta halvimman version k-market.fi
    verkkokaupasta ja lisää ostoskoriin, mikäli price_constraint sallii.
    """
    assert type(shopping_list) == list, "shopping_list should be a list"
    for item in shopping_list:
        assert type(item) == tuple, "shopping_list should comprise tuples"
        assert len(item) == 4, "shopping_list tuples should be of length 4"
        assert type(item[0]) == str, "shopping_list tuples' index 0 should be a string"
        assert type(item[1]) == str, "shopping_list tuples' index 1 should be a string"
        assert type(item[2]) == int, "shopping_list tuples' index 2 should be an int"
        assert type(item[3]) == str, "shopping_list tuples' index 3 should be a string"
        
    print("Ostaminen alkaa...")
    time.sleep(5)
    items_found = []
    items_not_found = []
    for article in shopping_list:
        print("")
        search_term = article[0]
        category = article[1]
        price_constraint = article[2]
        unit_constraint = article[3]
        
        print(f'Haetaan hakusanalla: "{search_term}"\n')
        searchItem(search_term, category)
        scrollAllItems()
        search_results_dict = fetchItemInfo()
        search_results_df = convertToDF(search_results_dict)
        print("Löydettiin nämä tuotteet:")
        print(search_results_df)
        print("")
        cheapest_item_df = getCheapestItem(search_results_df, price_constraint, unit_constraint)
        try:
            cheapest_item_product_number = cheapest_item_df["Tuotenumero"]
            addToCart(cheapest_item_product_number)
            cheapest_item_str = cheapestItemToString(cheapest_item_df)
            items_found.append(cheapest_item_str)
            print(f"Valittiin ostoskoriin: {cheapest_item_str}")
        except:
            print("Mikään tuotteista ei täyttänyt ostoslistan rajoituksia.")
            items_not_found.append(search_term)
    print("\nValmis!\n")
    return items_found, items_not_found


items_found, items_not_found = buy(shopping_list)
summary = composeSummary(items_found, items_not_found)
sendToMail(summary, summary_email_address)
driver.quit()

