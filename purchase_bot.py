# -*- coding: utf-8 -*-
"""
Created on Sat Dec 26 14:17:37 2020

@author: rikus

"""

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from items_to_buy import *
# Alle käyttämäsi Firefox-selaimen profiilin tiedostopolku.
FF_PROFILE_PATH = r"C:\Users\rikus\AppData\Roaming\Mozilla\Firefox\Profiles\selenium_test_profile_copy"
import time
import pandas as pd


# Määritetään webdriverin asetukset
driver_options = Options()
driver_options.headless = True
profile = webdriver.FirefoxProfile(FF_PROFILE_PATH)
driver = webdriver.Firefox(profile, options=driver_options)
driver.implicitly_wait(5)


driver.get("https://www.k-ruoka.fi/kauppa/tuotehaku")


def searchItem(search_term, category):
    """
    Tekee haun K-Ruokaan hakusanoilla search_term.
    """
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


def downloadItems():
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
    
    # Luodaan uusi df, jossa "Hinta"-pylväs on jaettu "/"-merkin perusteella
    price_columns_df = temp_df["Hinta"].str.split("/", expand=True)
    
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
    
    print("Löydetyt tuotteet:")
    print(search_results_df)
    print("")
    
    return search_results_df


def findCheapestItem(search_results_df, price_constraint, unit_constraint):
    """
    search_results_df: DF-objekti, jossa pylväät "Tuotenumero", "Tuotenimi", "Hinta", "Yksikkö"
    price_constraint: korkein hyväksytty hinta tuottelle (int)
    unit_constraint: onko tuotteen hinta per "kg", "kpl" vai "l"
    
    Palauttaa halvimman tuotteen, joka täyttää ehdot. Muussa tapauksessa palauttaa None
    """
    return_index = -1
    length = search_results_df.shape[0]
    for i in range(length):
        price = search_results_df["Hinta"][i]
        unit = search_results_df["Yksikkö"][i]
        if price < price_constraint and unit == unit_constraint:
            return_index = i
            break
    if return_index < 0:
        print("Ei valittu tuotetta.")
        return None
    else:
        print("Valittiin tuote:")
        print(search_results_df.iloc[return_index,:])
        return search_results_df.iloc[return_index,:]


def addToCartClick():
    """
    Lisää tuotteen ostoskoriin.
    """
    add_to_cart_path = '//button[@title="Lisää"]'
    add_to_cart = driver.find_element_by_xpath(add_to_cart_path)
    add_to_cart.click()


def buy(shopping_list):
    """
    Ottaa ostoslistan (list), etsii jokaisesta tuotteesta halvimman version k-market.fi
    verkkokaupasta ja lisää ostoskoriin, mikäli price_constraint sallii.
    """
    for article in shopping_list:
        search_term = article[0]
        category = article[1]
        price_constraint = article[2]
        unit_constraint = article[3]
        
        searchItem(search_term, category)
        scrollAllItems()
        search_results_dict = downloadItems()
        search_results_df = convertToDF(search_results_dict)
        cheapest_item = findCheapestItem(search_results_df, price_constraint, unit_constraint)
        print("")
        try:
            cheapest_item_product_number = cheapest_item["Tuotenumero"]
            searchItem(cheapest_item_product_number, category)
            time.sleep(2)
            addToCartClick()
        except:
            pass


print("Ostaminen alkaa...")
print("")
time.sleep(5)
buy(shopping_list)
print("Valmis!")


