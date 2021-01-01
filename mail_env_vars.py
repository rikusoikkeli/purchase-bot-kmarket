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
    assert type(string_object) == str, "string_object should be string"
    assert len(string_object) > 0, "string_object should be of length >0"
    string_object = string_object.encode()
    string_object = base64.b64encode(string_object)
    return string_object


def fromBase64(bytes_object):
    """
    Ottaa base64-objektin ja palauttaa sen string-muodossa.
    """
    assert type(bytes_object) == str, "bytes_object should be a string"
    assert len(bytes_object) > 0, "bytes_object should be of length >0"
    bytes_object = base64.b64decode(bytes_object)
    assert type(bytes_object) == bytes, "bytes_object should be a bytes object"
    bytes_object = bytes_object.decode()
    return bytes_object


def getMailUser():
    """
    Noutaa environmental variabelin ROBOT_MAIL_USER, kääntää sen base64-muodosta
    stringiksi ja palauttaa.
    """
    user = fromBase64(os.environ.get("ROBOT_MAIL_USER"))
    assert type(user) == str, "getMailUser() didn't fetch a string"
    assert len(user) > 0, "user should be of length >0"
    return user


def getMailPass():
    """
    Noutaa environmental variabelin ROBOT_MAIL_PASS, kääntää sen base64-muodosta
    stringiksi ja palauttaa.
    """
    password = fromBase64(os.environ.get("ROBOT_MAIL_PASS"))
    assert type(password) == str, "getMailPass() didn't fetch a string"
    assert len(password) > 0, "password should be of length >0"
    return password

