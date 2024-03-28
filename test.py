from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Set up the Chrome WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# URL of the webpage you want to scrape
url = 'https://www.centennialcollege.ca/programs-courses/full-time?tab=areasofstudy'

# Navigate to the page
driver.get(url)

# Wait for JavaScript to render. You might need to adjust the sleep time or use more sophisticated waiting methods.
import time
time.sleep(5)  # Adjust this delay as necessary for the page to load completely

# Get the rendered HTML
rendered_html = driver.page_source

print(rendered_html)

# Don't forget to close the browser when you're done
driver.quit()

