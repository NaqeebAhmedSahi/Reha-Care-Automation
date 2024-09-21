import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import re
import csv
import time

# Function to initialize Chrome with headless mode, disabled images, and extensions
def initialize_driver():
    options = uc.ChromeOptions()
    # options.add_argument('--headless')  # Run headless for faster performance
    options.add_argument('--disable-extensions')  # Disable extensions
    options.add_argument('--disable-gpu')  # Disable GPU
    options.add_argument('--no-sandbox')  # Bypass OS security model
    options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
    options.add_argument('--blink-settings=imagesEnabled=false')  # Disable images for speed

    driver = uc.Chrome(options=options)
    return driver

# Function to wait until an element is present or clickable
def wait_for_element(driver, by_type, identifier, condition=EC.presence_of_element_located, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            condition((by_type, identifier))
        )
        return element
    except TimeoutException:
        print(f"Timeout: Could not find element with {identifier}")
        return None

def scrape_company_data(link, driver):
    try:
        print(f"Opening link: {link}")
        driver.get("https://www.rehacare.com/" + link)
        time.sleep(1)

        # Wait for the profile CTA buttons container to load
        container = wait_for_element(driver, By.CLASS_NAME, 'profile__cta-buttons', condition=EC.presence_of_element_located)
        if container:
            # Find the button and click it using JavaScript
            button = container.find_element(By.CLASS_NAME, 'cta-button--primary')
            driver.execute_script("arguments[0].click();", button)
            print("Company data button clicked.")
            time.sleep(0.5)
            # Wait for the company data section to load
            profile_section = wait_for_element(driver, By.ID, 'profile-top', condition=EC.presence_of_element_located)
            if profile_section:
                # Parse the updated page
                soup = BeautifulSoup(driver.page_source, 'html.parser')

                # Extract Hall name using regex containing 'Hall'
                hall_name = "NA"
                hall_text = soup.find(string=re.compile(r"Hall\s+\d+"))
                if hall_text:
                    hall_name = hall_text.strip()
                print(f"Hall Name: {hall_name}")

                # Extract the country and city using 'profile__country-city' class
                country_city = "NA"
                country_city_div = soup.find('div', class_='profile__country-city')
                if country_city_div:
                    country_city = country_city_div.get_text(strip=True)
                print(f"Country & City: {country_city}")

                # Extract company name from the h1 tag inside 'profile-top'
                company_name = "NA"
                profile_top = soup.find('div', id='profile-top')
                if profile_top:
                    h1_tag = profile_top.find('h1')
                    if h1_tag:
                        company_name = h1_tag.get_text(strip=True)
                print(f"Company Name: {company_name}")

                # Extract about section by concatenating all text from elements within 'profile-details-text'
                about_section = "NA"
                about_div = soup.find('div', class_='profile-details-text')
                if about_div:
                    # Extract text directly from the div tag, including text from all child elements
                    about_section = about_div.get_text(separator=' ', strip=True)
                print(f"About Section: {about_section}")

                # Extract various business details from 'profile-business-exh-address'
                business_data = {
                    'Street': 'NA',
                    'ZIP Code': 'NA',
                    'City': 'NA',
                    'Country': 'NA',
                    'Email': 'NA',
                    'Phone': 'NA'
                }

                address_div = soup.find('div', class_='profile-business-exh-address')
                if address_div:
                    street = address_div.find('div', class_='address-street')
                    if street:
                        business_data['Street'] = street.get_text(strip=True)
                    zip_code = address_div.find('span', class_='address-zip')
                    if zip_code:
                        business_data['ZIP Code'] = zip_code.get_text(strip=True)
                    city = address_div.find('span', class_='address-city')
                    if city:
                        business_data['City'] = city.get_text(strip=True)
                    country = address_div.find('div', class_='address-country')
                    if country:
                        business_data['Country'] = country.get_text(strip=True)
                print(f"Business Data: {business_data}")

                # Extract contact details
                contact_div = soup.find('div', class_='exh-contact')
                if contact_div:
                    email = contact_div.find('div', class_='exh-contact__email')
                    if email:
                        business_data['Email'] = email.get_text(strip=True).replace('E-mail: ', '')
                    phone = contact_div.find('div', class_='exh-contact__phone')
                    if phone:
                        business_data['Phone'] = phone.get_text(strip=True).replace('Phone: ', '')
                print(f"Business Data: {business_data}")

                # Extract website links
                website_links = []
                links_div = soup.find('div', class_='exh-contact__links')
                if links_div:
                    link_list = links_div.find('div', class_='link-list')
                    if link_list:
                        website_links = [a['href'] for a in link_list.find_all('a', href=True)]
                website_links_text = ', '.join(website_links) if website_links else 'NA'
                print(f"Website Links: {website_links_text}")

                # NEW: Extract product data
                product_data = []
                product_list = soup.find('ul', class_='tags-list tags-list--selectable tags-list--scrollable')
                if product_list:
                    for product in product_list.find_all('li', class_='tags-list__item'):
                        product_name = product.find('span', class_='tags-item__label').get_text(strip=True)
                        product_data.append(product_name)
                product_data_text = ', '.join(product_data) if product_data else 'NA'
                print(f"Product Data: {product_data_text}")

                # Write data to CSV immediately
                with open('company_data.csv', 'a', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['Company Name', 'Hall Name', 'Country & City', 'About', 'Street', 'ZIP Code', 'City', 'Country', 'Email', 'Phone', 'Website Links', 'Product Data']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    # Write header only if file is empty
                    if csvfile.tell() == 0:
                        writer.writeheader()

                    writer.writerow({
                        'Company Name': company_name,
                        'Hall Name': hall_name,
                        'Country & City': country_city,
                        'About': about_section,
                        'Street': business_data['Street'],
                        'ZIP Code': business_data['ZIP Code'],
                        'City': business_data['City'],
                        'Country': business_data['Country'],
                        'Email': business_data['Email'],
                        'Phone': business_data['Phone'],
                        'Website Links': website_links_text,
                        'Product Data': product_data_text
                    })

                # Log successful processing
                with open('processed_links.txt', 'a') as f:
                    f.write(link + '\n')
                print(f"Successfully processed {link}")

            else:
                print(f"Profile section not found for {link}")

    except Exception as e:
        print(f"Error while processing {link}: {e}")

def scrape_links():
    driver = initialize_driver()
    driver.get("https://www.rehacare.com/vis/v1/en/search?ticket=g_u_e_s_t&_query=&f_type=profile")
    input("Press enter to start scraping of data ")
    # Wait for the search results section to load
    search_area = wait_for_element(driver, By.ID, 'vis-search-scroll-area', condition=EC.presence_of_element_located)
    if search_area:
        # Parse the page using BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Find all profile links inside 'vis-search-scroll-area'
        search_area = soup.find('div', id='vis-search-scroll-area')
        if search_area:
            links = [a['href'] for a in search_area.find_all('a', href=True)]
            print(f"Found {len(links)} profile links.")

            # Read previously processed links
            try:
                with open('processed_links.txt', 'r') as f:
                    processed_links = set(line.strip() for line in f)
            except FileNotFoundError:
                processed_links = set()

            for i, link in enumerate(links):
                if i % 2 == 0 and link not in processed_links:  # Only open odd links (1, 3, 5, ...) and not processed
                    scrape_company_data(link, driver)

    driver.quit()

if __name__ == "__main__":
    scrape_links()
