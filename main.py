import threading

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from seleniumwire import webdriver
from selenium.webdriver.support import expected_conditions as EC

from loguru import logger

import pymailtm
import requests
import string
import random
import time
import re


def get_password() -> str:
    password = []
    password += random.sample(string.ascii_letters, 4)
    password += random.sample(string.digits, 4)
    password += [random.choice(".+,!$&")]
    random.shuffle(password)
    return "".join(password)


def vote_with(driver: webdriver.Chrome):
    driver.implicitly_wait(10)

    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[2]/header/div[1]/div[2]/a'))
        ).click()
    except Exception:
        raise Exception("Something went wrong...")

    logger.info("Logging in...")

    driver.find_element(
        by="xpath",
        value='//*[@id="app"]/div[2]/div[3]/div/div/div[2]/div/form/div[3]/button',
    ).click()
    logger.info("Register clicked!")

    email = pymailtm.MailTm()
    account = email.get_account()

    driver.find_element(by="xpath", value='//*[@id="register_login"]').send_keys(
        account.address
    )

    password = get_password()
    driver.find_element(by="xpath", value='//*[@id="register_password"]').send_keys(
        password
    )

    logger.info("Writing password")

    register_button = driver.find_element(
        by="xpath", value='//*[@id="app"]/div[2]/div[4]/div/div/div[2]/div/form/button'
    )
    register_button.click()
    time.sleep(0.5)
    register_button.click()
    time.sleep(1)

    try:
        driver.find_element(
            by="xpath", value='//*[contains(text(), "Ваше поведение идентифицировано как подозрительное.")]'
        )
    except NoSuchElementException:
        pass
    else:
        raise Exception("Anti-abuse detected...")

    session = requests.Session()
    cookies = driver.get_cookies()
    for cookie in cookies:
        session.cookies[cookie["name"]] = cookie["value"]

    logger.info("Waiting for mail...")

    messages = account.get_messages()
    while not messages:
        messages = account.get_messages()
    verification_link = re.findall(r"\[(https://63.ru/.*)]", messages[0].text)[0]

    session.get(verification_link)
    logger.success(f"Successfully registered account! ({account.address})")

    threading.Thread(target=do_voting_shit, args=(session, account)).start()


def do_voting_shit(session: requests.Session, account: pymailtm.Account):
    # session.options(
    #     "https://newsapi.63.ru/v1/public/records/70386878/polls/withImages/954496907/vote?answerId=514037961"
    # )
    r = session.put(
        "https://newsapi.63.ru/v1/public/records/70386878/polls/withImages/954496907/vote?answerId=514037961",
        headers={
            "Accept": "vnd.news.v1.jtnews+json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ru-RU,en;q=0.9",
            # "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36"
        }
    )

    if r.status_code == 200:
        logger.success("Voted for nigga!")
    else:
        logger.warning("Cringe!!!")


def make_cookies_with_requests():
    try:
        resp = requests.get("https://63.ru/credits/")
        return resp.cookies
    except Exception:
        logger.warning("The site is dead. Sleeping...")
        time.sleep(2)
        return make_cookies_with_requests()


def main() -> None:
    seleniumwire_options = {
        # 'proxy': {
        #     'http': '',
        #     'https': '',
        # }
    }

    desired_capabilities = {
        "pageLoadStrategy": "eager"
    }
    prefs = {
        "profile.managed_default_content_settings.images": 2,
    }

    option = webdriver.ChromeOptions()
    # option.add_argument("--headless")
    option.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(seleniumwire_options=seleniumwire_options , desired_capabilities=desired_capabilities, chrome_options=option)
    driver.get("https://63.ru/credits/")
    while True:
        try:
            vote_with(driver)
        except KeyboardInterrupt:
            logger.info("Shutting down.")
            break
        except Exception as e:
            logger.exception(f"Got error: {e}")
            time.sleep(4)
        finally:
            driver.delete_all_cookies()
            driver.execute_script("window.localStorage.clear();")
            try:
                driver.find_element(By.XPATH, '//*[@id="app"]/div[2]/div[5]/div/div/div[2]/div/button').click()
            except Exception:
                pass
            for key, value in make_cookies_with_requests().get_dict().items():
                driver.add_cookie({"name": key, "domain": "63.ru", "value": value})


if __name__ == "__main__":
    main()
