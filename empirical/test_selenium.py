from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time

# browser = webdriver.Firefox() # Get local session of firefox
# browser = webdriver.Chrome() # Get local session of firefox
# browser = webdriver.AndroidDriver() # Get local session of firefox
# browser = webdriver.Remote("http://localhost:8080/wd/hub",
#                            webdriver.DesiredCapabilities.ANDROID)
# browser.get("http://www.yahoo.com") # Load page


# assert "Yahoo!" in browser.title
# elem = browser.find_element_by_name("p") # Find the query box
# elem.send_keys("seleniumhq" + Keys.RETURN)
# time.sleep(0.2) # Let the page load, will be added to the API
# try:
#     browser.find_element_by_xpath("//a[contains(@href,'http://seleniumhq.org')]")
# except NoSuchElementException:
#     assert 0, "can't find seleniumhq"

profile = webdriver.FirefoxProfile()
profile.set_preference("browser.cache.disk.enable", False)
profile.set_preference("network.http.pipelining", True)
profile.set_preference(
  "network.http.pipelining.maxrequest", 16)
profile.set_preference("network.http.pipelining.ssl", True)
profile.update_preferences()

browser_driver = webdriver.Firefox(firefox_profile = profile)
browser_driver.get('https://theseus.news.cs.nyu.edu')
browser_driver.quit()

profile = webdriver.FirefoxProfile()
profile.set_preference("browser.cache.disk.enable", False)
profile.set_preference("network.http.pipelining", True)
profile.set_preference(
  "network.http.pipelining.maxrequest", 8)
profile.set_preference("network.http.pipelining.ssl", True)
profile.update_preferences()
browser_driver = webdriver.Firefox(firefox_profile = profile)
browser_driver.get('https://theseus.news.cs.nyu.edu')
browser_driver.quit()
