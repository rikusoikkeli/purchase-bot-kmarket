# -*- coding: utf-8 -*-
"""
Created on Sat Dec  5 11:10:11 2020

@author: rikus

Needed for purchase_bot.py/sendMail() to work.

This module is used to fetch user info from environment variables in a way that
is somewhat secure. The strings themselves are saved in base64 so even if someone
sees you opening environment variables, all they see is gibberish. And when the 
info is fetched, it's converted upon use and not saved into any variables. So the 
info can't be discerned from seeing the code run, either.
"""


import os
import base64


def intoBase64(string_object):
    """
    Ottaa string-objektin ja palauttaa sen base64-muodossa.
    """
    string_object = string_object.encode()
    string_object = base64.b64encode(string_object)
    return string_object


def fromBase64(bytes_object):
    """
    Ottaa base64-objektin ja palauttaa sen string-muodossa.
    """
    bytes_object = base64.b64decode(bytes_object)
    bytes_object = bytes_object.decode()
    return bytes_object


def getMailUser():
    """
    Noutaa environmental variabelin ROBOT_MAIL_USER, kääntää sen base64-muodosta
    stringiksi ja palauttaa.
    """
    user = fromBase64(os.environ.get("ROBOT_MAIL_USER"))
    return user


def getMailPass():
    """
    Noutaa environmental variabelin ROBOT_MAIL_PASS, kääntää sen base64-muodosta
    stringiksi ja palauttaa.
    """
    password = fromBase64(os.environ.get("ROBOT_MAIL_PASS"))
    return password

