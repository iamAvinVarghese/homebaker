import urllib.request

print("--- FALBACK SERVICE TEST ---")

# Test LoremFlickr
lorem_url = "https://loremflickr.com/800/600/cake,chocolate,red"
print(f"\nTesting LoremFlickr: {lorem_url}")
try:
    req = urllib.request.Request(lorem_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        print(f"LoremFlickr Status: {response.getcode()}")
        print(f"Final URL: {response.geturl()}")
except Exception as e:
    print(f"LoremFlickr Failed: {e}")

# Test Unsplash Source (via redirect)
unsplash_url = "https://source.unsplash.com/800x600/?cake,chocolate"
print(f"\nTesting Unsplash: {unsplash_url}")
try:
    req = urllib.request.Request(unsplash_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        print(f"Unsplash Status: {response.getcode()}")
        print(f"Final URL: {response.geturl()}")
except Exception as e:
    print(f"Unsplash Failed: {e}") 
