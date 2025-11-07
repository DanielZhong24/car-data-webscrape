from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from collections import deque
from selenium.webdriver.firefox.options import Options
import time
from multiprocessing import Pool
brands = ["LEXUS","BMW","AUDI","HONDA"]

db = dict()

def scrape_brand(brand):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)

    #open main website
    driver.get("https://www.autoevolution.com/cars/")
    time.sleep(1)
    #get brand
    element = driver.find_element(By.XPATH,f"//a[@title='{brand}']")
    brand_link = element.get_attribute('href')

    #get brand models
    driver.get(brand_link)

    models = driver.find_elements(By.TAG_NAME,"h4")


    for model in models:
        model_name = model.text.strip() 
        parent_a = model.find_element(By.XPATH, "..")  
        model_url = parent_a.get_attribute("href")
        print(model_name, model_url)



    #get hp
   

    driver.quit()
    return {}


if __name__ == "__main__":
    with Pool(processes=3) as pool:
        results = pool.map(scrape_brand,brands)

    print(results)
