#by @xavsiohw on discord
import requests
from time import sleep
from re import findall
from threading import Lock
from concurrent.futures import ThreadPoolExecutor

counterLock = Lock()
page, counter = 1, 0 # constants, don't change

low = [""] # if at least 5 keywords on here are detected, snipe
mid = [""] # if at least 3 keywords on here are detected, sinipe
high = [""] # if any keywords on here are detected, immeditely snipe
category = 6 # assettypeid for models, for more check https://create.roblox.com/docs/projects/assets/api#query-parameters
numOfThreads = 10 # adjust according to need, 10 is the recommended
webhookUrl = "" # your webhook url that will have the sniped results sent to

def heat(content, tier, strictness):
    count = 0
    for string in tier:
        if string in content:
            count += 1
    return count >= strictness

def search():
    global page
    try:
        response = requests.get(f"https://search.roblox.com/catalog/json?Category={category}&PageNumber={page}").json()
        return [(item['AssetId'], item['Favorited']) for item in response if 'AssetId' in item]
    except Exception as e:
        print(f"Error in search: {e}")
        return []

def scrape(threadCounter):
    global page, counter
    with counterLock:
        counter += 1
        itemCounter = counter
        if itemCounter >= 42:
            page += 1
            counter = 0
    try:
        sleep(4.5)
        assetID, favoriteCount = search()[counter]
        counter += 1
        print(f"Thread-{threadCounter} Processing item {itemCounter} on Page {page}")
        content = requests.get(f"https://assetdelivery.roblox.com/v1/asset/?ID={assetID}").text
        print(f"processing {counter}")
        if int(''.join(findall(r'\d', favoriteCount))) < 50:
            if heat(content, low, 5) or heat(content, mid, 3) or any(keyword in content for keyword in high):
                print(f"Thread-{threadCounter} Sniped item {itemCounter} from Page {page}")
                requests.post(webhookUrl, json={"content": f"https://assetdelivery.roblox.com/v1/asset/?ID={assetID}"})
        else:
            print(f"Thread-{threadCounter} Skipped item {itemCounter} from Page {page}")
    except Exception as e:
        print(f"Thread-{threadCounter} Error in scrape: {e} Page: {page} with counter: {counter}")

def processItem(threadCounter):
    while True:
        scrape(threadCounter)

def runloop():
    with ThreadPoolExecutor(max_workers=numOfThreads) as executor:
        for threadCounter in range(1, numOfThreads + 1):
            executor.submit(processItem, threadCounter)

if __name__ == "__main__":
    runloop()
