import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEST_USER_EMAIL = "testuser+qa-1@osgrm.ru"
TEST_USER_PASSWORD = "Test123-"


@pytest.fixture(scope="module")
def driver():
    service = Service(ChromeDriverManager().install())
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    driver = webdriver.Chrome(service=service, options=options)
    yield driver
    driver.quit()


def test_login(driver):
    """Тест авторизации на сайте"""
    driver.delete_all_cookies()
    driver.get('https://cp.osgrm.ru/#/auth')
    page_html = driver.page_source
    logger.info(f"Загружена страница: {driver.current_url}")
    
    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        logger.info("Страница авторизации загрузилась")

        email_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, 'loginform-username-input')),
            message="Поле ввода email не найдено."
        )
        email_input.clear()
        email_input.send_keys(TEST_USER_EMAIL)

        password_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, 'loginform-password-input')),
            message="Поле ввода пароля не найдено."
        )
        password_input.clear()
        password_input.send_keys(TEST_USER_PASSWORD)

        login_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="loginform-enter-button"]')),
            message="Кнопка входа не найдена или не кликабельна"
        )
        time.sleep(1)
        try:
            login_button.click()
        except EC.ElementClickInterceptedException:
            logger.warning("Стандартный клик не сработал, используем JavaScript")
            driver.execute_script("arguments[0].click();", login_button)

        # Проверка URL сразу после авторизации
        WebDriverWait(driver, 30).until(EC.url_to_be("https://cp.osgrm.ru/#/info"))
        assert driver.current_url == "https://cp.osgrm.ru/#/info", f"Ожидался URL 'https://cp.osgrm.ru/#/info', но получен '{driver.current_url}'"
        logger.info("Главная страница открыта")

        main_page = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="home-main-menu"]/span[1]'))
        )
        assert main_page.is_displayed()

    except Exception as e:
        logger.error(f"Ошибка при авторизации: {str(e)}")
        logger.info(f"HTML при ошибке: {page_html[:500]}")
        raise


@pytest.mark.depends(on=['test_login'])
def test_documents_button_click(driver):
    """Тест нажатия на кнопку 'Документы и скан-копии'"""
    try:
        documents_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "documents-and-scans-menu")),
            message="Кнопка 'Документы и скан-копии' не найдена или не кликабельна"
        )
        
        assert documents_button.is_displayed(), "Кнопка не отображается"
        assert documents_button.is_enabled(), "Кнопка не активна"
        
        documents_button.click()
        logger.info("Кнопка 'Документы и скан-копии' успешно нажата")
        
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body")),
            message="Страница после нажатия кнопки не загрузилась"
        )

    except Exception as e:
        logger.error(f"Ошибка при тестировании кнопки документов: {str(e)}")
        page_html = driver.page_source
        logger.info(f"HTML при ошибке: {page_html[:500]}")
        raise


@pytest.mark.depends(on=['test_documents_button_click'])
def test_search_button_click(driver):
    """Тест нажатия на кнопку 'Поиск' с предварительным вводом значения"""
    try:
        # Ожидание появления поля ввода по абсолютному XPath
        search_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/app-root/app-user-cabinet/mat-drawer-container/mat-drawer-content/div/app-documents/section/mat-tab-group/div/mat-tab-body/div/app-doc-tab/mat-drawer-container/mat-drawer/div/div/app-tab-slider/app-search-dialog/div/form/div[2]/app-edit-autocompleate/mat-form-field/div/div[1]/div[1]/input")),
            message="Поле ввода штрих-кода документа не найдено"
        )
        
        # Очистка поля и ввод значения
        search_input.clear()
        search_input.send_keys("R029256127")
        logger.info("Значение 'R029256127' введено в поле штрих-кода документа")

        # Ожидание появления кнопки поиска
        search_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "search-dialog-button-search")),
            message="Кнопка 'Поиск' не найдена или не кликабельна"
        )
        
        # Проверка состояния кнопки
        assert search_button.is_displayed(), "Кнопка 'Поиск' не отображается"
        assert search_button.is_enabled(), "Кнопка 'Поиск' не активна"
        
        # Клик по кнопке
        search_button.click()
        logger.info("Кнопка 'Поиск' успешно нажата")

        # 1. Найти элемент и нажать на него: //*[@id="data-table-menu-button"]/span[1]/mat-icon
        menu_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="data-table-menu-button"]/span[1]/mat-icon')),
            message="Кнопка меню таблицы не найдена или не кликабельна"
        )
        menu_button.click()
        logger.info("Нажата кнопка меню таблицы")

        # 2. Найти элемент и навести на него, зажав мышку: //*[@id="context-menu-item-button"]/span
        context_menu_item = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Скачать выбранные документы')]")),
            message="Элемент контекстного меню не найден"
        )
        actions = ActionChains(driver)
        actions.click_and_hold(context_menu_item).perform()
        logger.info("Выполнено нажатие и удержание на элементе контекстного меню")
        time.sleep(1)  # Небольшая пауза для стабильности
        actions.release().perform()  # Отпускаем кнопку мыши

        # 3. Найти элемент и нажать на него: <span>Скачать выбранные документы</span>
        download_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[text()="в формате PDF"]')),
            message="Элемент 'Скачать выбранные документы' не найден или не кликабелен"
        )
        download_button.click()
        logger.info("Нажата кнопка 'Скачать выбранные документы'")

    except Exception as e:
        logger.error(f"Ошибка при тестировании: {str(e)}")
        page_html = driver.page_source
        logger.info(f"HTML при ошибке: {page_html[:1000]}")
        raise


if __name__ == "__main__":
    pytest.main(["-v"])