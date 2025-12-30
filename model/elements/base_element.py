"""
BaseElement
"""
import inspect

from contextlib import contextmanager
from typing import Generator, Iterator
from typing_extensions import Self, overload
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from model.errors.element import ElementNotClickableError, ElementVisibleError, ElementNotVisibleError, \
    ElementNotFoundError

BASIC_TIMEOUT = 5


class BaseElement(object):
    """Base elements class contains all the common methods & attributes inherited by other elements"""

    def __init__(self, driver: WebDriver, selector: str, locator: str):
        self.locator = locator
        self.selector = selector
        self.driver = driver

    def __repr__(self) -> str:
        return f'{self.selector=}'

    def __iter__(self) -> Iterator[WebElement]:
        return iter(self.elements)

    @overload
    def __getitem__(self, index: int) -> WebElement:
        ...

    @overload
    def __getitem__(self, index: slice) -> list[WebElement]:
        ...

    def __getitem__(self, index: int | slice) -> WebElement | list[WebElement]:
        try:
            return self.elements[index]
        except IndexError:
            raise ElementNotFoundError(str(self), self.driver.current_url, f'Element with {index=} is not exist.')

    def __len__(self) -> int:
        return len(self.elements)

    @property
    def element(self) -> WebElement:
        try:
            return self.driver.find_element(self.locator, self.selector)
        except NoSuchElementException:
            raise ElementNotFoundError(str(self), self.driver.current_url)

    @property
    def elements(self) -> list[WebElement]:
        return self.driver.find_elements(self.locator, self.selector)

    def is_enabled(self) -> bool:
        return self.element.is_enabled()

    def click(self) -> None:
        try:
            self.element.click()
        except ElementClickInterceptedException:
            raise ElementNotClickableError(str(self), self.driver.current_url)

    @contextmanager
    def format(self, *args: str, **kwargs: str) -> Generator[Self, None, None]:
        """Takes a single string or an array of strings and add them as parameters
        to selector string.
        I.e:
        format(['a', 'b']) for selector ".//[{}][{}]" will set selector to
        ".//['a']['b']"

        :param args: string|[string]
        """
        original_selector = self.selector
        try:
            self.selector = original_selector.format(*args, **kwargs)
            yield self
        finally:
            self.selector = original_selector

    def is_clickable(self, timeout: int = BASIC_TIMEOUT) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((self.locator, self.selector)))
        except TimeoutException:
            return False
        return True

    def is_visible(self, timeout: int = BASIC_TIMEOUT) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((self.locator, self.selector)))
        except TimeoutException:
            return False
        return True

    def is_present_now(self) -> bool:
        try:
            _ = self.element
            return True
        except NoSuchElementException:
            return False

    def is_visible_now(self) -> bool:
        try:
            return self.element.is_displayed()
        except NoSuchElementException:
            return False

    def wait_for_clickability(self, timeout: int = BASIC_TIMEOUT, error_msg: str = None) -> WebElement:
        if not self.is_clickable(timeout):
            timeout_info = f'Error raised after {timeout=}s.'
            raise ElementNotClickableError(str(self), self.driver.current_url, error_msg or "", timeout_info)
        return self.element

    @property
    def text(self) -> str:
        return self.element.text

    def get_attribute(self, name: str) -> str:
        return self.element.get_attribute(name)
