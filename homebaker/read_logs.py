import sys

def read_file(filepath):
    print(f"Reading {filepath}...")
    try:
        # Try different encodings
        for enc in ['utf-16', 'utf-8', 'cp1252']:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    content = f.read()
                    print(f"--- Content (encoding: {enc}) ---")
                    print(content)
                    return
            except UnicodeDecodeError:
                continue
        print("Could not decode file with common encodings.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        read_file(sys.argv[1])
    else:
        print("Usage: python read_logs.py <filepath>")
