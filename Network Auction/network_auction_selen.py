import csv
import json
import openpyxl
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from auction_scraper_base import get_property_type, prepare_price, get_bedroom, get_tenure, parse_postal_code


class NetworkAuction:
    driver: webdriver.Chrome

    def __init__(self):
        service = Service(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)

    def property_scraper(self, property_link):
        self.driver.get(property_link)
        print(property_link)

        image = self.driver.find_element(By.XPATH, "(//div[contains(@class,'property-single-images')]//img)[1]")
        image_link = image.get_attribute("src")

        guidePrice = self.driver.find_element(By.XPATH, "//div[@class='property-info-banner-left']/h2").text
        price, currency = prepare_price(guidePrice)

        description_list = []
        sibling_description = self.driver.find_element(By.XPATH, "//div[@class='property-single-main-info']/p").text
        for sibling_list in sibling_description:
            description_list.append(sibling_list)
            description = "".join(description_list)
            print(description)

        address = self.driver.find_element(By.XPATH, "//div[@class='property-info-banner-center']").text
        postal_code = parse_postal_code(address)

        short_description = self.driver.find_element(By.XPATH, "//h5[@class='image-caption']").text
        number_of_bedrooms = get_bedroom(short_description)

        tenure = self.driver.find_element(By.XPATH, "//p[contains(text(),'Free')]").text

        title = self.driver.find_element(By.XPATH, "//div[@class='property-info-banner-center']").text

        property_type = get_property_type(title)

        if property_type == "other":
            property_type = get_property_type(description)
        if not tenure:
            tenure = get_tenure(description)

        data_hash = {
            "price": price,
            "currency_type": currency,
            "picture_link": image_link,
            "property_description": description,
            "property_link": property_link,
            "address": address,
            "postal_code": postal_code,
            "auction_venue": "online",
            "source": "iamsold.co.uk",
            "property_type": property_type,
            "number_of_bedrooms": number_of_bedrooms,
            "tenure": tenure,
        }
        return data_hash

    def properties_scraper(self):
        auction_divs = []
        for auction_divs_href in self.driver.find_elements(
                By.XPATH, "//div[@class='current-lots-single']/a"):
            auction_property = auction_divs_href.get_attribute('href')
            print(auction_property)
            auction_divs.append(auction_property)

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        csv_fh = open('connect_auctions_req.csv', mode='w', newline='', encoding='utf8')
        json_fh = open("connect_auctions_req.json", "w", encoding='utf8')
        csv_writer = csv.writer(csv_fh)

        list_dict = []

        for property_link in auction_divs:
            result_dict = self.property_scraper(property_link)
            result_list = list(result_dict.values())
            worksheet.append(result_list)
            csv_writer.writerow(result_list)
            list_dict.append(result_dict)
            workbook.save("connect_auctions_req.xlsx")

        json_result = json.dumps(list_dict)
        json_fh.write(json_result)
        json_fh.close()
        workbook.close()
        csv_fh.close()

    def run(self):
        self.driver.get(
            "https://www.networkauctions.co.uk/auctions/next-auction/?online_auction_id=46051")
        self.properties_scraper()


auction = NetworkAuction()
auction.run()
