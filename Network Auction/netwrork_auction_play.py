import csv
import json
import re
import openpyxl
from playwright.sync_api import Page
from auction_scraper_base import browser_context, prepare_price, get_bedroom, get_property_type, get_tenure, \
    parse_postal_code

start_url = "https://www.networkauctions.co.uk/auctions/next-auction/?online_auction_id=46051"


def property_scraper(detail_url_page, property_link):
    detail_url_page.goto(property_link)

    image_link = detail_url_page.locator(
        "xpath=(//div[contains(@class,'property-single-images')]//img)[1]").get_attribute("src")
    print(image_link)

    guidePrice = detail_url_page.locator("xpath=//div[@class='property-info-banner-left']/h2").text_content()
    price, currency = prepare_price(guidePrice)

    description = detail_url_page.locator("xpath=(//div[@class='p__readmore__wrap']/p)[1]")
    print(description)

    property_type = get_property_type(description)

    address = detail_url_page.locator(
        "xpath=//div[@class='property-info-banner-center']").text_content()

    title = detail_url_page.locator("xpath=//div[@class='property-info-banner-center']").text_content()

    postal_code = parse_postal_code(title)

    tenure = detail_url_page.locator("xpath=//p[contains(text(),'Free')]").text_content()

    short_description = detail_url_page.locator("//h5[@class='image-caption']").text_content()
    number_of_bedrooms = get_bedroom(short_description)

    if not tenure:
        tenure = get_tenure(description)

    if number_of_bedrooms is None:
        number_of_bedrooms = get_bedroom(title)

    if property_type == "other" and "land" in address.lower():
        property_type = "land"
    if "land" in address.lower():
        address = re.search(r"(?<= to ).*|(?<= of ).*|(?<= at ).*", address, re.IGNORECASE)
        if address:
            address = address.group().strip()

    data_hash = {
        "price": price,
        "currency_type": currency,
        "picture_link": image_link,
        "property_description": description,
        "property_link": property_link,
        "address": address,
        "postal_code": postal_code,
        "auction_venue": "online",
        "source": "networkauctions",
        "property_type": property_type,
        "number_of_bedrooms": number_of_bedrooms,
        "tenure": tenure,
        "title": title
    }
    return data_hash


def properties_scraper(page, browser):
    auction_divs = []
    anchor_locator = page.locator("//div[@class='current-lots-single']/a")

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    csv_fh = open('connect_auctions_req.csv', mode='w', newline='', encoding='utf8')
    json_fh = open("connect_auctions_req.json", "w", encoding='utf8')
    csv_writer = csv.writer(csv_fh)

    list_dict = []

    for i in range(anchor_locator.count()):
        property_href = anchor_locator.nth(i)
        property_card = property_href.get_attribute("href")
        auction_divs.append(property_card)

    detail_url_page: Page = browser.new_page()

    for property_link in auction_divs:
        result_dict = property_scraper(detail_url_page, property_link)
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


def run():
    with browser_context(headless=False) as (page, browser):
        page.set_default_navigation_timeout(120000)
        page.goto(start_url)
        properties_scraper(page, browser)


if __name__ == "__main__":
    run()
