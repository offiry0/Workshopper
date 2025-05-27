import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import threading
import concurrent.futures


def fetch_workshop_items(base_url):
    page_number = 1
    items = []

    while True:
        url = f"{base_url}&p={page_number}"
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        workshop_items = soup.select('.workshopItem')

        if not workshop_items:
            break

        def process_item(item):
            thread_id = threading.get_ident()
            thread_name = threading.current_thread().name

            name_tag = item.select_one('.workshopItemTitle')
            name = name_tag.text.strip() if name_tag else 'Unknown'

            item_link_tag = item.select_one('a')
            item_link = item_link_tag['href'] if item_link_tag else None

            if item_link:
                stats = fetch_item_details(item_link)
                stats = {"Name": name, **stats}

                displayType = 'unknown'

                if stats['Type'] == 'Mission':
                    displayType = 'custom mission'
                if stats['Type'] == 'Aircraft Livery':
                    displayType = 'livery'
                    if stats['Airframe'] != 'Unknown':
                        displayType = f"{stats['Airframe']} livery"

                current_console_text = console_text.get()
                console_text.set(console_text.get() + (f"\n[Thread {int(thread_name[-1]) + 1}]: Found {displayType}"
                                                       f" {stats['Name']}."))
                return stats

            return None


        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(process_item, workshop_items))

        items.extend(filter(None, results))

        console_text.set(console_text.get() + (f"\nCompleted page {page_number}, moving on..."))
        page_number += 1
        time.sleep(0.5)
        console_text.set(f"Loading page {page_number}...")

    return items


def fetch_item_details(item_url):
    response = requests.get(item_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    visitors = get_stat(soup, 'Unique Visitors')
    subscribers = get_stat(soup, 'Current Subscribers')
    favorites = get_stat(soup, 'Current Favorites')
    awards = get_awards(soup)
    item_type = get_item_type(soup)
    comments = get_comments_count(soup)
    file_size, date_posted, date_updated = get_file_info(soup)
    num_changes = get_num_changes(soup)
    description = get_description(soup)

    airframe = ""
    if item_type == "Aircraft Livery":
        airframe = get_airframe(soup, description)

    return {
        'Type': item_type,
        'Airframe': airframe,
        'Visitors': int(visitors.replace(",", "")),
        'Subscribers': int(subscribers.replace(",", "")),
        'Favorites': int(favorites.replace(",", "")),
        'Awards': int(awards),
        'Comments': int(comments.replace(",", "")),
        'Changes': int(num_changes.replace(",", "")),
        'File Size': file_size.replace(" ", ""),
        'Uploaded': date_posted.replace(" @ ", ", "),
        'Updated': date_updated.replace(" @ ", ", "),
        'Description': description
    }


def get_stat(soup, label):
    try:
        # Find the stats table
        stats_table = soup.find('table', class_='stats_table')
        if stats_table:
            # Find all rows in the table
            rows = stats_table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) == 2 and label in cells[1].text:
                    return cells[0].text.strip()  # Return the value in the first cell
    except Exception as e:
        console_text.set(console_text.get() + f"\nError fetching {label}: {e}")
    return '0'


def get_awards(soup):
    try:
        award_container = soup.find('div', class_='review_award_ctn')
        if not award_container:
            return '0'

        awards = award_container.find_all('div', class_='review_award tooltip')
        total_awards = sum(int(award['data-reactioncount']) for award in awards if award.has_attr('data-reactioncount'))
        return str(total_awards)
    except Exception as e:
        console_text.set(console_text.get() + f"\nError fetching awards: {e}")
        return '0'

def get_item_type(soup):
    try:
        details_block = soup.find('div', class_='rightDetailsBlock')
        if not details_block:
            return 'Unknown'

        item_type_tag = details_block.find('a')
        return item_type_tag.text.strip() if item_type_tag else 'Unknown'
    except Exception as e:
        console_text.set(console_text.get() + f"\nError fetching item type: {e}")
        return 'Unknown'

def get_comments_count(soup):
    try:
        comment_section = soup.find('div', class_='commentthread_header_and_count')
        if comment_section:
            count_label = comment_section.find('span', class_='ellipsis commentthread_count_label')
            if count_label:
                count_span = count_label.find('span')
                return count_span.text.strip() if count_span else '0'
    except Exception as e:
        console_text.set(console_text.get() + f"\nError fetching comments: {e}")
    return '0'

def get_file_info(soup):
    try:
        stats_container = soup.find('div', class_='detailsStatsContainerRight')
        if stats_container:
            stats = stats_container.find_all('div', class_='detailsStatRight')
            if len(stats) >= 2:
                file_size = stats[0].text.strip()
                date_posted = stats[1].text.strip()
                date_updated = date_posted
                if len(stats) >= 3:
                    date_updated = stats[2].text.strip()
                return file_size, date_posted, date_updated
    except Exception as e:
        console_text.set(console_text.get() + f"\nError fetching file info: {e}")
    return '? KB', 'Unknown', 'Unknown'

def get_num_changes(soup):
    try:
        change_note = soup.find('div', class_='detailsStatNumChangeNotes')
        if change_note:
            text = change_note.text.strip()
            return text[:-26] if text.endswith("( view )") else '0'
    except Exception as e:
        console_text.set(console_text.get() + f"\nError fetching changes: {e}")
    return '0'

def get_description(soup):
    try:
        description_div = soup.find('div', id='highlightContent', class_='workshopItemDescription')
        if description_div:
            return description_div.text.strip()
    except Exception as e:
        console_text.set(console_text.get() + f"\nError fetching description: {e}")
    return 'No description.'

def get_airframe(soup, description):

    airframes = {
        "ci-22": "CI-22",
        "cricket": "CI-22",
        "t/a-30": "T/A-30",
        "compass": "T/A-30",
        "sah-46": "SAH-46",
        "chicane": "SAH-46",
        "fs-12": "FS-12",
        "revoker": "FS-12",
        "fs-20": "FS-20",
        "vortex": "FS-20",
        "kr-67": "KR-67",
        "ifrit": "KR-67",
        "vl-49": "VL-49",
        "tarantula": "VL-49",
        "ew-25": "EW-25",
        "medusa": "EW-25",
        "sfb-81": "SFB-81",
        "darkreach": "SFB-81"
    }

    try:
        description = description.lower()
        for airframe in airframes:
            if airframe in description:
                return airframes[airframe]
    except Exception as e:
        console_text.set(console_text.get() + f"\nError fetching airframe: {e}")
    return "Unknown"

def save_to_excel(data):
    console_text.set(console_text.get() + "\nAll items processed, attempting to save file...")
    filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    if filename:
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)
        if not filename == "":
            console_text.set(console_text.get() + f"\nData exported as {filename}")

def main_process(username):
    if username.isdigit():
        user_url = f"https://steamcommunity.com/profiles/{username}/myworkshopfiles/?appid=2168680"
        console_text.set("Steam User ID detected, searching...")
        print(user_url)
    else:
        user_url = f"https://steamcommunity.com/id/{username}/myworkshopfiles/?appid=2168680"
        console_text.set("Steam CustomLink name detected, searching...")
    try:
        workshop_items = fetch_workshop_items(user_url)
        save_to_excel(workshop_items)
        messagebox.showinfo("Success", f"Data saved successfully for {username}!")
        console_text.set(console_text.get() + f"\nData saved successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def run_scraper():
    username = username_entry.get().strip()
    if not username:
        messagebox.showwarning("Input Error", "Please enter a Steam username.")
    else:
        console_text.set(console_text.get() + f"\nFetching workshop items from {username}...")
        time.sleep(1)
        threading.Thread(target=main_process, args=(username,), daemon=True).start()


root = tk.Tk()
root.title("Workshopper 0.1.3n")

root.geometry("800x400")

frame = ttk.Frame(root, padding=10)
frame.pack(fill="both", expand=True)

ttk.Label(frame, text="Enter Steam User ID (e.g. 123456789)\nor Steam CustomLink (e.g. offiry)").pack(pady=5)
username_entry = ttk.Entry(frame, width=40)
username_entry.pack(pady=5)

ttk.Button(frame, text="Run!", command=run_scraper).pack(pady=10)

console_text = tk.StringVar(value="Workshopper Version 0.1.3n\nby offiry")
console_label = ttk.Label(frame, textvariable=console_text, wraplength=700, justify="left")
console_label.pack(pady=5)

root.mainloop()

