import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import ipaddress # For IP validation

# --- Configuration ---
PROXY_TEST_URL = "http://www.google.com" # URL to test if proxy is working
TIMEOUT = 10 # Seconds for proxy test
MAX_WORKERS = 200 # Adjust based on GitHub Actions runner capabilities. More is faster.
OUTPUT_FILE = "proxy.txt"
# --- End Configuration ---

# Complete categorized proxy sources (all URLs included)
SOURCES = {
    "http": [
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "https://raw.githubusercontent.com/gfpcom/free-proxy-list/main/list/http.txt",
        "https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/http.txt",
        "https://raw.githubusercontent.com/zenjahid/FreeProxy4u/master/http.txt",
        "https://raw.githubusercontent.com/shiftytr/proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/http.txt",
        "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/proxylist-to/update-list/main/http.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http_proxies.txt",
        "https://raw.githubusercontent.com/official-proxy/proxies/main/proxies/http.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        "https://raw.githubusercontent.com/sunny9577/proxy-scraper/main/proxies.txt",
        "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/proxies.txt",
        "https://raw.githubusercontent.com/Anonymaron/free-proxy/main/http.txt",
        "https://raw.githubusercontent.com/HyperBeast/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/TuanMinhPay/Proxy-List/main/http.txt",
        "https://raw.githubusercontent.com/vmheaven/VMHeaven-Free-Proxy-Updated/refs/heads/main/http.txt",
        "https://raw.githubusercontent.com/yemixzy/proxy-list/refs/heads/main/proxies/http.txt",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/refs/heads/master/http.txt",
        "https://raw.githubusercontent.com/handeveloper1/Proxy/refs/heads/main/Proxies-Ercin/http.txt",
        "https://raw.githubusercontent.com/ProxyScraper/ProxyScraper/refs/heads/main/http.txt",
        "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/refs/heads/main/proxy_files/http_proxies.txt",
        "https://raw.githubusercontent.com/Vann-Dev/proxy-list/refs/heads/main/proxies/http.txt",
        "https://sunny9577.github.io/proxy-scraper/generated/http_proxies.txt",
        "https://raw.githubusercontent.com/zloi-user/hideip.me/master/http.txt",
        "http://multiproxy.org/txt_all/proxy.txt",
        "http://promicom.by/tools/proxy/proxy.txt",
        "http://www.socks24.org/feeds/posts/default",
        "http://globalproxies.blogspot.de/feeds/posts/default",
        "http://www.caretofun.net/free-proxies-and-socks/"
    ],
    "https": [
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=https",
        "https://raw.githubusercontent.com/gfpcom/free-proxy-list/main/list/https.txt",
        "https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/https",
        "https://raw.githubusercontent.com/shiftytr/proxy-list/master/https.txt",
        "https://raw.githubusercontent.com/proxylist-to/update-list/main/https.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt",
        "https://raw.githubusercontent.com/handeveloper1/Proxy/refs/heads/main/Proxy-KangProxy/https.txt",
        "https://raw.githubusercontent.com/handeveloper1/Proxy/refs/heads/main/Proxy-Tsprnay/https.txt",
        "https://raw.githubusercontent.com/handeveloper1/Proxy/refs/heads/main/Proxy-Zaeem20/https.txt",
        "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/refs/heads/main/proxy_files/https_proxies.txt",
        "https://raw.githubusercontent.com/Vann-Dev/proxy-list/refs/heads/main/proxies/https.txt",
        "https://raw.githubusercontent.com/zloi-user/hideip.me/master/https.txt"
    ],
    "socks4": [
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt",
        "https://raw.githubusercontent.com/gfpcom/free-proxy-list/main/list/socks4.txt",
        "https://raw.githubusercontent.com/zenjahid/FreeProxy4u/master/socks4.txt",
        "https://raw.githubusercontent.com/shiftytr/proxy-list/master/socks4.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/proxylist-to/update-list/main/socks4.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks4_proxies.txt",
        "https://raw.githubusercontent.com/official-proxy/proxies/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/Anonymaron/free-proxy/main/socks4.txt",
        "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks4.txt",
        "https://raw.githubusercontent.com/TuanMinhPay/Proxy-List/main/socks4.txt",
        "https://raw.githubusercontent.com/vmheaven/VMHeaven-Free-Proxy-Updated/refs/heads/main/socks4.txt",
        "https://raw.githubusercontent.com/yemixzy/proxy-list/refs/heads/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/refs/heads/master/socks4.txt",
        "https://raw.githubusercontent.com/handeveloper1/Proxy/refs/heads/main/Proxies-Ercin/socks4.txt",
        "https://raw.githubusercontent.com/ProxyScraper/ProxyScraper/refs/heads/main/socks4.txt",
        "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/refs/heads/main/proxy_files/socks4_proxies.txt",
        "https://raw.githubusercontent.com/Vann-Dev/proxy-list/refs/heads/main/proxies/socks4.txt",
        "https://sunny9577.github.io/proxy-scraper/generated/socks4_proxies.txt",
        "https://raw.githubusercontent.com/zloi-user/hideip.me/master/socks4.txt"
    ],
    "socks5": [
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
        "https://raw.githubusercontent.com/gfpcom/free-proxy-list/main/list/socks5.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/refs/heads/master/proxy.txt",
        "https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/socks5.txt",
        "https://raw.githubusercontent.com/zenjahid/FreeProxy4u/master/socks5.txt",
        "https://raw.githubusercontent.com/shiftytr/proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/proxylist-to/update-list/main/socks5.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks5_proxies.txt",
        "https://raw.githubusercontent.com/official-proxy/proxies/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/Anonymaron/free-proxy/main/socks5.txt",
        "https://raw.githubusercontent.com/HyperBeast/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/TuanMinhPay/Proxy-List/main/socks5.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
        "https://raw.githubusercontent.com/vmheaven/VMHeaven-Free-Proxy-Updated/refs/heads/main/socks5.txt",
        "https://raw.githubusercontent.com/yemixzy/proxy-list/refs/heads/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/refs/heads/master/socks5.txt",
        "https://raw.githubusercontent.com/handeveloper1/Proxy/refs/heads/main/Proxies-Ercin/socks5.txt",
        "https://raw.githubusercontent.com/ProxyScraper/ProxyScraper/refs/heads/main/socks5.txt",
        "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/refs/heads/main/proxy_files/socks5_proxies.txt",
        "https://raw.githubusercontent.com/Vann-Dev/proxy-list/refs/heads/main/proxies/socks5.txt",
        "https://sunny9577.github.io/proxy-scraper/generated/socks5_proxies.txt",
        "https://raw.githubusercontent.com/zloi-user/hideip.me/master/socks5.txt"
    ],
    "mixed": [
        "https://api.getproxylist.com/proxy?anonymity[]=transparent&anonymity[]=anonymous&anonymity[]=elite",
        "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc",
        "https://raw.githubusercontent.com/gitrecon1455/fresh-proxy-list/main/proxylist.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/all.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-working-checked.txt",
        "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/proxies.txt",
        "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies_anonymous/proxies.txt",
        "https://raw.githubusercontent.com/iplocate/free-proxy-list/refs/heads/main/all-proxies.txt",
        "https://raw.githubusercontent.com/berkay-digital/Proxy-Scraper/refs/heads/main/proxies.txt",
        "https://raw.githubusercontent.com/variableninja/proxyscraper/refs/heads/main/proxies/socks.txt",
        "https://raw.githubusercontent.com/BreakingTechFr/Proxy_Free/refs/heads/main/proxies/all.txt",
        "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.txt",
        "https://raw.githubusercontent.com/zloi-user/hideip.me/master/connect.txt"
    ]
}

# Free/Public DNSBL servers for basic blacklist check
# Note: These might have rate limits or not be as comprehensive as paid services.
FREE_DNSBL_SERVERS = [
    "zen.spamhaus.org", # Very common, but might have usage limits for high volume
    "bl.spamcop.net",
    "dnsbl.sorbs.net",
    "b.barracudacentral.org"
]

def fetch_all_proxy_urls():
    """Extracts all proxy URLs from the SOURCES dictionary."""
    all_urls = []
    for category in SOURCES:
        all_urls.extend(SOURCES[category])
    return all_urls

def fetch_proxies_from_url(url):
    """Fetches proxy list from a given GitHub raw URL."""
    try:
        # Some non-GitHub sources might return JSON or other formats,
        # but the current regex expects IP:PORT per line.
        # We'll fetch the text content.
        response = requests.get(url, timeout=30)
        response.raise_for_status() # Raise an exception for HTTP errors
        
        # Look for IP:PORT patterns, which is common for most text-based proxy lists
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
        reversed_ip = ".".join(ip.split('.')[::-1])
        listed_count = 0
        for dnsbl in FREE_DNSBL_SERVERS:
            try:
                # This is a very basic check. A proper DNSBL query would check the response IP range.
                # For this simple implementation, if it resolves, we count it as listed.
                # Using a tiny timeout for DNSBL checks to fail fast if unresolved.
                requests.get(f"http://{reversed_ip}.{dnsbl}", timeout=0.5) 
                listed_count += 1
                # print(f"IP {ip} listed on {dnsbl}") # Uncomment for more verbose output
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
    proxy_urls = fetch_all_proxy_urls()
    print(f"Total proxy source URLs found: {len(proxy_urls)}")

    all_proxies = []
    print("Fetching proxies from all configured URLs...")
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
            
            # Only accept working proxies with 0 DNSBL listings
            if is_working and dnsbl_listings == 0: 
                working_clean_proxies.append(proxy)
            elif not is_working:
                # print(f"Skipping {proxy}: Not working.") # Uncomment for more verbose output
                pass
            else:
                # print(f"Skipping {proxy}: Listed on {dnsbl_listings} DNSBLs.") # Uncomment for more verbose output
                pass

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
    if is_working: # Only check DNSBL if the proxy is working
        dnsbl_listings = check_dnsbl(ip)
    return is_working, dnsbl_listings

if __name__ == "__main__":
    process_proxy_list()
