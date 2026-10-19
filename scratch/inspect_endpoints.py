import os
import json
import requests
from bs4 import BeautifulSoup

urls = [
    "http://192.168.0.6/pcp/atrasadas.php",
    "http://192.168.0.6/pcp/consumo_alt.php",
    "http://192.168.0.6/pcp/estoque_lote.php"
]

cookies = {
    "PHPSESSID": "3eeero9cktl23hpo78aba98gai"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

os.makedirs("storage/snapshots", exist_ok=True)
results = {}

for url in urls:
    filename = url.split("/")[-1].replace(".php", "")
    print(f"\n==========================================")
    print(f"Connecting to {url}...")
    try:
        resp = requests.get(url, cookies=cookies, headers=headers, timeout=10)
        print(f"Status: {resp.status_code} | Encoding: {resp.encoding} | Content-Length: {len(resp.content)}")
        
        # Save raw HTML
        snapshot_path = f"storage/snapshots/{filename}.html"
        with open(snapshot_path, "wb") as f:
            f.write(resp.content)
        print(f"Saved snapshot to {snapshot_path}")
        
        # Parse HTML
        soup = BeautifulSoup(resp.content, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else "No Title"
        print(f"Page Title: {title}")
        
        forms_data = []
        forms = soup.find_all("form")
        print(f"Forms found: {len(forms)}")
        
        for i, form in enumerate(forms):
            form_info = {
                "form_index": i + 1,
                "action": form.get("action", ""),
                "method": form.get("method", "GET").upper(),
                "inputs": [],
                "selects": []
            }
            
            for inp in form.find_all("input"):
                form_info["inputs"].append({
                    "name": inp.get("name"),
                    "type": inp.get("type", "text"),
                    "value": inp.get("value", ""),
                    "id": inp.get("id", "")
                })
                
            for sel in form.find_all("select"):
                options = []
                for opt in sel.find_all("option"):
                    options.append({
                        "value": opt.get("value", ""),
                        "text": opt.get_text(strip=True),
                        "selected": opt.has_attr("selected")
                    })
                form_info["selects"].append({
                    "name": sel.get("name"),
                    "id": sel.get("id", ""),
                    "options_count": len(options),
                    "options_sample": options[:10]  # First 10 options
                })
                
            forms_data.append(form_info)
            
        # Check for tables
        tables = soup.find_all("table")
        table_headers = []
        for t in tables[:5]:
            headers_in_table = [th.get_text(strip=True) for th in t.find_all(["th", "td"])]
            table_headers.append(headers_in_table[:10])
            
        results[url] = {
            "status": resp.status_code,
            "title": title,
            "forms": forms_data,
            "table_count": len(tables),
            "table_headers_sample": table_headers
        }
        
    except Exception as e:
        print(f"Error connecting to {url}: {e}")
        results[url] = {"error": str(e)}

with open("storage/snapshots/endpoint_inspection.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\nFinished inspection. Results written to storage/snapshots/endpoint_inspection.json")
