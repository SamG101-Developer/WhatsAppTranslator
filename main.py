import time
from functools import partial
from threading import Thread

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from googletrans import Translator

# Initialize the translator
translator = Translator()

# Initialize the webdriver
driver = webdriver.Edge()
driver.delete_all_cookies()
driver.get("https://web.whatsapp.com")

# Wait for QR code to be scanned
wait = WebDriverWait(driver, 120)
element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "_aigz")))


def translate_message_nodes(nodes: list) -> None:
    # Highlight untranslated text red.
    for node in nodes:
        driver.execute_script("arguments[0].style.color = 'red';", node.find_element(By.CLASS_NAME, "_amk4"))

    # Translate the messages (from the most recent to the oldest).
    for node in reversed(nodes):

        # Get the string inside the node, detect the src language, and specify the destination language.
        message = node.find_element(By.CLASS_NAME, "selectable-text").text
        src_lang = translator.detect(message).lang
        dst_lang = "en"

        # Don't translate if the source language is the same as the destination language.
        if dst_lang == src_lang:
            translated_message = message
        else:
            translated_message = translator.translate(message, src=src_lang, dest=dst_lang).text

        # Replace the node data with the translated message & set the text color to white.
        driver.execute_script("arguments[0].innerText = arguments[1];", node.find_element(By.CLASS_NAME, "selectable-text"), translated_message)
        driver.execute_script("arguments[0].style.color = 'white';", node.find_element(By.CLASS_NAME, "_amk4"))


# Whenever a chat is being viewed, read the messages, and wait for the chat tag again (different chat can be viewed)
latest_message = {}
while True:
    try:
        # TODO: Scroll up to load more messages

        # Wait until a chat window is present on the screen.
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "x1vs56c6")))
        chat_window = driver.find_element(By.CLASS_NAME, "x1vs56c6")

        # Subset new messages from already-translated messages (allows new messages to be translated w/o reload)
        messages_recv = driver.find_elements(By.CLASS_NAME, "message-in")
        if chat_window not in latest_message.keys():
            message_subset = messages_recv
        else:
            message_subset = messages_recv[messages_recv.index(latest_message.get(chat_window, -1)) + 1:]

        # Grab all received messages and translate them in a separate thread.
        Thread(target=partial(translate_message_nodes, message_subset)).start()
        latest_message[chat_window] = messages_recv[-1]
        time.sleep(1)

    except KeyboardInterrupt:
        break

# Close the browser
driver.quit()
