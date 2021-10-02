from numpy.core.records import array
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
from urllib.parse import urlencode
import psycopg2

import chromedriver_binary

def findMaxNumberOfPages(driverWait: WebDriverWait) -> int:
    paginatorBtns = driverWait.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, 'paginator__btn ')))
    foundNumbersList = re.findall(r'\d+', paginatorBtns[-2].get_attribute('textContent'))
    return int(foundNumbersList[-1])

def getDbConnection():
    return psycopg2.connect(user="postgres", 
            password="d24-postgres-pass",
            host="127.0.0.1",
            port="5432",
            database="krishaParsedData")

def insertAppartments(appsData):
    if len(appsData) == 0:
        return

    connection = getDbConnection()
    cursor = connection.cursor()
    # appsData = [(1,'x'), (2,'y')]
    records_list_template = ','.join(['%s'] * len(appsData))
    insert_query = 'INSERT INTO appartments (cost, street, rooms, area, condition, krisha_id, floor, max_floor, is_dorm, description) VALUES {}'.format(records_list_template)
    cursor.execute(insert_query, appsData)
    connection.commit()
    cursor.close()
    connection.close()

driver = webdriver.Chrome(executable_path='C:\Program Files\Google\Chrome\Application\chromedriver.exe')
wait = WebDriverWait(driver, 5)
baseKrishaUrl = 'https://krisha.kz/'
rentAppsUrl = baseKrishaUrl + 'arenda/kvartiry/'
filters = {
    'das[rent.period]': 2, #monthly rental
    'page': 1 #page
}
regions = [
    'almaty-almalinskij'
]

appsDataToWrite = []
for currRegion in (regions):
    driver.get(rentAppsUrl + currRegion + '?' + urlencode(filters))
    maxPages = findMaxNumberOfPages(wait)
    for currPage in range(1, maxPages + 1):
        if (currPage > 1):
            filters.page = currPage
            driver.get(rentAppsUrl + currRegion + '?' + urlencode(filters))
        
        
        appsCards = driver.find_elements_by_xpath("//div[@class='primary-navbar-container']//following::a[contains(@class, 'a-card__title')]")
        for currACardTitle in appsCards:
            currHref = currACardTitle.get_attribute('href')
            driver.get(currHref)
            driver.implicitly_wait(5)
            
            #region hadnling hint pop-up
            if driver.find_elements_by_xpath("//button[@class='kr-btn kr-btn--gray-gradient']"):
                driver.find_element_by_xpath("//button[@class='kr-btn kr-btn--gray-gradient']").click()
                driver.implicitly_wait(3)
            #endregion xd
            currTitleAsArray = driver.find_element_by_css_selector("div[class='offer__advert-title'] h1").get_attribute('textContent').split(',')
            floorInfo = re.findall(r'\d+', currTitleAsArray[2])
            shortInfo = driver.find_elements_by_xpath("//div[@class='offer__advert-short-info']")
            print(len(shortInfo))
            valuesList = [
                driver.find_element_by_xpath("//div[@class='offer__price']").get_attribute('textContent'),
                currTitleAsArray[-1],
                re.findall(r'\d+', currTitleAsArray[0])[0],
                re.findall(r'\d+', currTitleAsArray[1])[0],
                shortInfo[3].get_attribute('textContent'),
                int(re.findall(r'\d+', currHref)[0]),
                floorInfo[0],
                floorInfo[-1],
                False, #todo: is dorm
                'description', #mojet i ne byt etoy infy
            ]
            appsDataToWrite.append(tuple(valuesList))

print(appsDataToWrite)
insertAppartments(appsDataToWrite)
        
driver.close()
