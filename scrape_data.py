from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from openpyxl import load_workbook
from io import BytesIO
from rapidfuzz import fuzz
import pandas as pd
from read_in_establishments import convert_excel_to_csv, get_address
import io

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Optional
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def scrape_website(excel_file, links, establishments_list):
    
    # Webdriver
    driver = get_driver()
    #Open excel file to write
    wb = load_workbook(excel_file)

    for link in links:
        # Open generated file
        driver.get(link)
        
        # Wait for elements to load
        driver.implicitly_wait(5)
        
        # Entire table
        table = driver.find_element(By.ID, 'decrs_table')
        
        # Get all rows
        rows = table.find_elements(By.TAG_NAME, 'tr')
        
        # Extract data from each row
        for row in rows:
            try:
                name = row.find_element(By.CLASS_NAME, 'firm_name').text
                address = row.find_element(By.CLASS_NAME, 'decrs-address').text
                duns = row.find_element(By.CLASS_NAME, 'duns-number').text
                business = row.find_element(By.CLASS_NAME, 'business_operations').text
                expiration = row.find_element(By.CLASS_NAME, 'expiration_date').text
                print(f' DUNS: {duns}, Address: {address}')  

                for i, original_address in enumerate(establishments_list.values()):
                    match_ratio = fuzz.partial_ratio(original_address, address)
                    if match_ratio >= 85:
                        print("Matched with a:", match_ratio, "for", original_address)
                        write_file(excel_file, wb, i, name, duns, business, expiration)
                        break
            except:
                continue  # Skip rows that don’t match

    # Save file
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    # Close file and webdriver
    wb.close()
    driver.quit()

    return buffer


def write_file(excel_file, wb, count, name, duns, business, expiration):
    if isinstance(excel_file, BytesIO):
        df = pd.read_excel(excel_file)
    else:
        csv_file = convert_excel_to_csv(excel_file)
        df = pd.read_csv(csv_file)
    
    # Find column in which establishment specfied is
    establishment_label = f"Establishment {count+1}"
    column = df.columns.get_loc(df.columns[df.eq(establishment_label).any(axis=0)][0]) + 1

    # Find rows that need to be filled
    name_label = 'Establishment Name (DECRS)'
    name_row = df[df.eq(name_label).any(axis=1)].index[0] + 2
    
    duns_label = 'DUNS (DECRS)'
    duns_row = df[df.eq(duns_label).any(axis=1)].index[0] + 2
    
    business_label = 'Business Operations (DECRS)'
    business_row = df[df.eq(business_label).any(axis=1)].index[0] + 2
    
    expiration_label = 'Registration Expiration Date (DECRS)'
    expiration_row = df[df.eq(expiration_label).any(axis=1)].index[0] + 2

    # Writing on "Full Query" sheet
    wb.active = wb.sheetnames.index('Full Query') 
    ws = wb.active

    ws.cell(row=name_row, column=column, value=name)
    ws.cell(row=duns_row, column=column, value=duns)
    ws.cell(row=business_row, column=column, value=business)
    ws.cell(row=expiration_row, column=column, value=expiration)

    print("Data successfully written to Excel!")