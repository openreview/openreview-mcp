"""This file imports selenium and must be excluded from the index."""

from selenium import webdriver


def test_browser_ui(client):
    driver = webdriver.Firefox()
    driver.get("https://openreview.net")
    driver.quit()
