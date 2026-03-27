import urllib.request
import os
import ssl

urls = [
    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/FSSAI_logo.svg/320px-FSSAI_logo.svg.png",
    "https://upload.wikimedia.org/wikipedia/commons/e/e2/FSSAI_logo.svg",
    "https://seeklogo.com/images/F/fssai-logo-8A19D73719-seeklogo.com.png"
]
dest_base = r"d:\HomeBakerProject\homebaker\static\images\fssai_logo"

context = ssl._create_unverified_context()

for url in urls:
    try:
        print(f"Trying {url}...")
        ext = ".svg" if url.endswith(".svg") else ".png"
        dest = dest_base + ext
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=context) as response:
            with open(dest, 'wb') as f:
                f.write(response.read())
        print(f"Successfully downloaded from {url} to {dest}")
        print(f"File size: {os.path.getsize(dest)} bytes")
        # Ensure we have a .png if needed, but for now just break
        break
    except Exception as e:
        print(f"Failed {url}: {e}")
