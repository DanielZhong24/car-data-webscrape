from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from multiprocessing import Pool
import re
import time
import json

brands = ["BMW"]

def extract_engine_details(driver, engine_url):
    driver.get(engine_url)
    time.sleep(1)  # simple wait for page to load

    details = {}

    # --- Grab tables ---
    try:
        tables = driver.find_elements(By.CSS_SELECTOR, "div.enginedata.engine-inline table.techdata")
        for table in tables:
            try:
                title = table.find_element(By.TAG_NAME, "th").text.strip().upper()
            except:
                title = "UNKNOWN"

            rows = table.find_elements(By.TAG_NAME, "tr")
            table_data = {}
            for row in rows[1:]:  # skip title row
                try:
                    th = row.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text.strip().rstrip(":")
                    td = row.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text.strip()
                    if th and td:
                        table_data[th] = td
                except:
                    continue
            if table_data:
                details[title] = table_data
    except Exception as e:
        print(f"[WARN] Failed to extract tables from {engine_url}: {e}")

    # --- Grab up to 5 images ---
    try:
        gallery_json = driver.find_element(By.ID, "schema-gallery-data").get_attribute("innerHTML")
        urls = re.findall(r'"contentUrl":"(https://[^"]+)"', gallery_json)
        details["images"] = urls[:5]  # limit to 5
    except:
        details["images"] = []

    return details

def extract_gasoline_engines(driver):
    results = []
    generations = driver.find_elements(By.CSS_SELECTOR, "div.col23width.subtlesep_top.fl.bcol-white")

    for gen in generations:
        try:
            gen_name = gen.find_element(By.CSS_SELECTOR, "h2 span.col-red").text.strip()
        except:
            gen_name = "Unknown Generation"

        try:
            engine_blocks = gen.find_elements(By.CSS_SELECTOR, "div.mot.padcol2.clearfix")
            for block in engine_blocks:
                fuel_type = block.find_element(By.TAG_NAME, "strong").text.strip().lower()
                if "gasoline" not in fuel_type and "petrol" not in fuel_type:
                    continue

                engines = block.find_elements(By.CSS_SELECTOR, "p.engitm a")
                for e in engines:
                    engine_name = e.text.strip()
                    engine_url = e.get_attribute("href")
                    if engine_name:
                        details = extract_engine_details(driver, engine_url)
                        results.append({
                            "generation": gen_name,
                            "fuel_type": "gasoline",
                            "engine": engine_name,
                            "engine_url": engine_url,
                            **details
                        })
        except:
            continue

    return results

def scrape_brand(brand):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    driver.get("https://www.autoevolution.com/cars/")

    try:
        brand_el = driver.find_element(By.XPATH, f"//a[@title='{brand}']")
        brand_link = brand_el.get_attribute("href")
    except Exception as e:
        print(f"[ERROR] Could not find brand {brand}: {e}")
        driver.quit()
        return []

    driver.get(brand_link)
    time.sleep(1)

    models_data = []
    model_blocks = driver.find_elements(By.CSS_SELECTOR, "div.carmod.subtlesep_top.clearfix")
    for block in model_blocks:
        try:
            eng_text = block.find_element(By.CSS_SELECTOR, "p.eng").text.lower()
            if "gasoline" not in eng_text:
                continue

            h4 = block.find_element(By.TAG_NAME, "h4")
            model_name = h4.text.strip()
            model_url = h4.find_element(By.XPATH, "..").get_attribute("href")

            years_text = block.find_element(By.XPATH, ".//span[contains(text(), '-')]").text.strip()
            match = re.findall(r"(\d{4})", years_text)
            if match:
                start_year = int(match[0])
                end_year = int(match[1]) if len(match) > 1 else None
            else:
                start_year = end_year = None

            if start_year and start_year >= 1993:
                models_data.append({
                    "brand": brand,
                    "model": model_name,
                    "url": model_url,
                    "start_year": start_year,
                    "end_year": end_year
                })
        except:
            continue

    print(f"[{brand}] Found {len(models_data)} gasoline models.")

    all_engines = []
    for m in models_data:
        try:
            driver.get(m["url"])
            time.sleep(1)
            engines = extract_gasoline_engines(driver)
            for e in engines:
                e.update(m)
                all_engines.append(e)
        except Exception as e:
            print(f"[WARN] Failed model {m['model']} ({brand}): {e}")
            continue

    driver.quit()
    return all_engines

if __name__ == "__main__":
    with Pool(processes=3) as pool:
        all_results = pool.map(scrape_brand, brands)

    # Flatten results
    all_data = [item for sublist in all_results for item in sublist]

    # Print results
    for r in all_data:
        print(r)
