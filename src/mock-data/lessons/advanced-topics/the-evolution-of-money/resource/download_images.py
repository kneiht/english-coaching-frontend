import urllib.request
import os

images = {
    "reading-image2.webp": "https://images.unsplash.com/photo-1610375461246-83df859d849d?auto=format&fit=crop&w=800&q=80&fm=webp",
    "reading-image3.webp": "https://images.unsplash.com/photo-1553729459-uj4872b4882e?auto=format&fit=crop&w=800&q=80&fm=webp",
    "reading-image4.webp": "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?auto=format&fit=crop&w=800&q=80&fm=webp"
}

output_dir = "src/mock-data/lessons/advanced-topics/the-evolution-of-money/images"
os.makedirs(output_dir, exist_ok=True)

for filename, url in images.items():
    filepath = os.path.join(output_dir, filename)
    print(f"Downloading {url} to {filepath}...")
    try:
        urllib.request.urlretrieve(url, filepath)
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
