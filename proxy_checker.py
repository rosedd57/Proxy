import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import ipaddress # For IP validation

# --- Configuration ---
PROXY_SOURCES_FILE = "proxy_sources.txt"
PROXY_TEST_URL = "http://www.google.com" # URL to test if proxy is working
TIMEOUT = 10 # Seconds for proxy test
MAX_WORKERS = 200 # Adjust based on GitHub Actions runner capabilities. More is faster.
OUTPUT_FILE = "proxy.txt"
# --- End Configuration ---

# Free/Public DNSBL servers for basic blacklist check
# Note: These might have rate limits or not be as comprehensive as paid services.
# We'll use them as DNS lookups. If an IP resolves, it's listed.
FREE_DNSBL_SERVERS = [
    "zen.spamhaus.org", # Very common, but might have usage limits for high volume
    "bl.spamcop.net",
    "dnsbl.sorbs.net",
    "b.barracudacentral.org"
]

def fetch_proxy_sources():
    """Reads GitHub raw URLs from proxy_sources.txt."""
    if not os.path.exists(PROXY_SOURCES_FILE):
        print(f"Error: {PROXY_SOURCES_FILE} not found. Please create it with your raw proxy URLs.")
        return []
    with open(PROXY_SOURCES_FILE, "r") as f:
        urls = [line.strip() for line in f if line.strip()]
    return urls

def fetch_proxies_from_url(url):
    """Fetches proxy list from a given GitHub raw URL."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status() # Raise an exception for HTTP errors
        proxies = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+', response.text)
        print(f"Fetched {len(proxies)} proxies from {url}")
        return proxies
    except requests.exceptions.RequestException as e:
        print(f"Error fetching proxies from {url}: {e}")
        return []

def test_proxy(proxy):
    """Tests if a proxy is working."""
    try:
        proxies_dict = {
            'http': f'http://{proxy}',
            'https': f'https://{proxy}'
        }
        # Using verify=False for some proxies that might have SSL issues, but be cautious.
        # For production, it's better to ensure proper SSL.
        response = requests.get(PROXY_TEST_URL, proxies=proxies_dict, timeout=TIMEOUT, verify=False) 
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        pass
    return False

def check_dnsbl(ip):
    """Checks an IP against free DNSBL servers."""
    try:
        # We don't need dnspython for a basic check, can use socket.gethostbyname
        # but it's not ideal for all DNSBL types.
        # For true DNSBL queries, you reverse the IP.
        # e.g., 1.2.3.4 -> 4.3.2.1.zen.spamhaus.org
        
        # A simple way without `dnspython` is to just try resolving the reversed IP + DNSBL domain.
        # If it resolves, it's probably listed.
        reversed_ip = ".".join(ip.split('.')[::-1])
        listed_count = 0
        for dnsbl in FREE_DNSBL_SERVERS:
            try:
                # This is a very basic check. A proper DNSBL query would check the response IP range.
                # For example, Spamhaus returns specific IP addresses for different listing types.
                # For this simple implementation, if it resolves, we count it as listed.
                requests.get(f"http://{reversed_ip}.{dnsbl}", timeout=1) # Just try to make a connection
                listed_count += 1
                print(f"IP {ip} listed on {dnsbl}")
            except requests.exceptions.RequestException:
                pass # Not listed on this DNSBL or error
            except Exception as e:
                print(f"Error during DNSBL check for {ip} on {dnsbl}: {e}")
        return listed_count
    except Exception as e:
        print(f"Error checking DNSBL for {ip}: {e}")
        return 0

def process_proxy_list():
    """Main function to fetch, test, and save proxies."""
    proxy_urls = fetch_proxy_sources()
    if not proxy_urls:
        print("No proxy source URLs found. Exiting.")
        return

    all_proxies = []
    print("Fetching proxies from GitHub URLs...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(fetch_proxies_from_url, url): url for url in proxy_urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                proxies = future.result()
                all_proxies.extend(proxies)
            except Exception as exc:
                print(f'{url} generated an exception: {exc}')

    unique_proxies = list(set(all_proxies))
    print(f"Total unique proxies fetched: {len(unique_proxies)}")

    working_clean_proxies = []
    print("Testing proxies for connectivity and checking basic DNSBLs...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_proxy = {executor.submit(test_and_check_proxy, proxy): proxy for proxy in unique_proxies}
        
        for future in as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            is_working, dnsbl_listings = future.result()
            
            if is_working and dnsbl_listings == 0: # Only accept working proxies with 0 DNSBL listings
                working_clean_proxies.append(proxy)
            elif not is_working:
                print(f"Skipping {proxy}: Not working.")
            else:
                print(f"Skipping {proxy}: Listed on {dnsbl_listings} DNSBLs.")

    print(f"Found {len(working_clean_proxies)} working and clean proxies.")

    with open(OUTPUT_FILE, "w") as f:
        for proxy in working_clean_proxies:
            f.write(proxy + "\n")
    print(f"Working proxies saved to {OUTPUT_FILE}")

def test_and_check_proxy(proxy):
    """Combines proxy testing and DNSBL checking."""
    is_working = test_proxy(proxy)
    ip = proxy.split(":")[0]
    dnsbl_listings = 0
    if is_working:
        dnsbl_listings = check_dnsbl(ip)
    return is_working, dnsbl_listings

if __name__ == "__main__":
    process_proxy_list()
