import requests
import re
import tkinter as tk
from tkinter import ttk, filedialog
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
from urllib.parse import urlparse
from threading import Thread


def open_file():
    # Clear the previous contents of the websites entry
    websites_entry.delete("1.0", "end")

    # Open the file dialog to select the website list file
    filename = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])

    # Read the contents of the file and populate the websites entry
    with open(filename, "r") as file:
        websites = file.read()
        websites_entry.insert("1.0", websites)

def check_hubspot_usage(website_url):
    try:
        response = requests.get(website_url)
        response.raise_for_status()  # Raise an exception if the response status is an error (4xx or 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')
        page_content = response.text.lower()  # Convert the page content to lowercase for case-insensitive matching

        # Method 1: Look for specific HTML tags or patterns indicating HubSpot usage
        # Example: Checking if the website has a HubSpot tracking code in the HTML
        hubspot_tracking_code = soup.find('script', {'src': re.compile(r'https?://.*?\.hs-scripts\.com/')})
        if hubspot_tracking_code:
            return True

        # Method 2: Analyze JavaScript libraries to find HubSpot usage
        # Example: Checking if the website includes the HubSpot analytics library
        scripts = soup.find_all('script')
        for script in scripts:
            if re.search(r'https?://.*?\.hs-analytics\.net/analytics/', script.get('src', ''), re.IGNORECASE):
                return True

        # Method 3: Check for HubSpot CRM using regex pattern matching
        if check_hubspot_crm(website_url):
            return True

        # Method 4: Check for "js.hsforms" in page content
        if 'js.hsforms' in page_content:
            return True

        # Method 5: Check for "hubspot" text in page content
        if 'hubspot' in page_content:
            return True

            # Method 6: Check network requests for HubSpot patterns
            network_requests = soup.find_all('script', {'src': True})  # Find all script tags with src attribute
            for request in network_requests:
                script_url = request['src']
                if re.search(r'https?://.*?\.hs-scripts\.com/', script_url, re.IGNORECASE):
                    script_response = requests.get(script_url)
                    script_response.raise_for_status()
                    script_content = script_response.text.lower()  # Convert the script content to lowercase for case-insensitive matching

                    # Check for specific HubSpot content in the script response
                    if 'hubspot' in script_content:
                        return True



    except requests.exceptions.RequestException:
        pass  # Ignore the exception and continue to the next website

    return False


def check_hubspot_crm(url):
    # Check for HubSpot tracking code
    response = requests.get(url)
    if response.status_code == 200:
        page_content = response.text

        # Check for HubSpot tracking code
        hubspot_pattern = r'<script.*?src="https://js\.hubspot\.com/.*?</script>'
        match = re.search(hubspot_pattern, page_content, re.IGNORECASE | re.DOTALL)
        if match:
            return True

        # Check for HubSpot forms
        hubspot_form_pattern = r'<form[^>]*class=["\'][^"\']*hs-form["\'][^>]*>'
        match = re.search(hubspot_form_pattern, page_content, re.IGNORECASE)
        if match:
            return True

        # Check for HubSpot cookies
        hubspot_cookies = [
            '__hs_opt_out',
            '__hs_do_not_track',
            '__hs_initial_opt_in',
            '__hs_cookie_cat_pref',
            '__hs_gpc_banner_dismiss',
            'hs_ab_test',
            'hs-messages-is-open',
            'hs-messages-hide-welcome-message',
            '__hsmem',
            'hs-membership-csrf',
            'hs_langswitcher_choice',
            '__cfruid',
            '__cf_bm',
            '__hstc',
            'hubspotutk',
            '__hssc',
            '__hssrc',
            'messagesUtk'
        ]

        for cookie in hubspot_cookies:
            if cookie in response.cookies:
                return True

    return False

def check_websites():
    websites = websites_entry.get("1.0", "end").strip().split("\n")
    websites = [url if urlparse(url).scheme else f"http://{url}" for url in websites]
    num_websites = len(websites)

    # Create a progress bar
    progress_bar['maximum'] = num_websites
    progress_bar['value'] = 0

    for index, website in enumerate(websites, start=1):
        is_hubspot_used = check_hubspot_usage(website)

        if is_hubspot_used:
            result_text = f"HubSpot is used on {website}."
        else:
            result_text = f"HubSpot is not used on {website}."

        # Update the result label
        result_label.config(text=result_text)

        # Write the result to the output file
        with open('hubspot_results.txt', 'a') as output_file:
            output_file.write(result_text + "\n")

        # Update the progress bar
        progress_bar['value'] = index
        window.update()

        # Delay for 2 seconds between each website check
        time.sleep(1)

    # Update the result label with completion message
    result_label.config(text="Website checks completed. Results saved in hubspot_results.txt.")
    # Enable the check button
    check_button.config(state="normal")

# Create the main window
window = tk.Tk()
window.title("HubSpot Checker")

# Create and configure the content frame
content_frame = ttk.Frame(window, padding=20)
content_frame.grid(row=0, column=0, sticky="nsew")

# Create and configure the websites entry
websites_label = ttk.Label(content_frame, text="Website List:")
websites_label.grid(row=0, column=0, sticky="w")
websites_entry = tk.Text(content_frame, width=40, height=10)
websites_entry.grid(row=1, column=0, columnspan=2, sticky="w")

# Create the open file button
open_button = ttk.Button(content_frame, text="Open File", command=open_file)
open_button.grid(row=2, column=0, pady=10)

# Create the check button
check_button = ttk.Button(content_frame, text="Check", command=check_websites)
check_button.grid(row=2, column=1, pady=10)

# Create the result label
result_label = ttk.Label(content_frame, text="")
result_label.grid(row=3, column=0, columnspan=2)

# Create the progress bar
progress_bar = ttk.Progressbar(content_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
progress_bar.grid(row=4, column=0, columnspan=2, pady=10)

# Configure the grid weights
content_frame.columnconfigure(1, weight=1)
content_frame.rowconfigure(3, weight=1)

# Start the GUI event loop
window.mainloop()
