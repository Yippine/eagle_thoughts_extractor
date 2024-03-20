import os
from pymongo import MongoClient
import requests
import json

# Configuration
API_BASE_URL = "http://localhost:41595/api"
OUTPUT_DIR = "output"

def create_output_folders():
    """Create necessary output folders if they don't exist."""
    for folder in ["converted_data", "folder_list"]:
        folder_path = os.path.join(OUTPUT_DIR, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

def switch_library(library_path):
    """Switch the currently opened library in Eagle."""
    url = f"{API_BASE_URL}/library/switch"
    payload = {"libraryPath": library_path}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print(f"Switched to library: {library_path}")
    else:
        print("Failed to switch library")

def get_folder_list(library_name):
    """Fetch folder list and write to a file."""
    url = f"{API_BASE_URL}/folder/list"
    response = requests.get(url)
    if response.status_code == 200:
        with open(os.path.join(OUTPUT_DIR, "folder_list", f"{library_name}.json"), "w", encoding="utf-8") as file:
            file.write(response.text)
        print(f"Folder list written to {library_name}.json")
        return response.json()
    else:
        print("Failed to fetch folder list")
        return None

def extract_folder_data(data, library_name):
    """Extract 'id' and 'name' from data and write to a new JSON file."""
    converted_data = []
    def process_item(item, parent_id=None):
        new_item = {"id": item["id"], "name": item["name"]}
        if "children" in item:
            new_item["children"] = [process_item(child, item["id"]) for child in item["children"]]
        if parent_id:
            new_item["parent"] = parent_id
        return new_item
    for item in data["data"]:
        converted_data.append(process_item(item))
    output_file = os.path.join(OUTPUT_DIR, "converted_data", f"{library_name}.json")
    with open(output_file, "w", encoding="utf-8") as outfile:
        json.dump(converted_data, outfile, ensure_ascii=False, indent=4)
    print(f"Extracted data written to {output_file}")

def process_libraries():
    """Retrieve library history, switch each library, fetch folder list, and extract data."""
    library_history_url = f"{API_BASE_URL}/library/history"
    history_response = requests.get(library_history_url)
    if history_response.status_code == 200:
        libraries = history_response.json().get('data', [])
        for library_path in libraries:
            switch_library(library_path)
            library_name = os.path.splitext(os.path.basename(library_path))[0]
            folder_data = get_folder_list(library_name)
            if folder_data:
                extract_folder_data(folder_data, library_name)
    else:
        print("Failed to retrieve library history")

def import_json_to_mongodb():
    # MongoDB 連接設定
    client = MongoClient('mongodb://localhost:27017/')
    db = client['eagle']
    collection = db['library']
    # 清空現有集合
    collection.delete_many({})
    # 路徑設定
    output_dir = "output/converted_data"
    # 處理每個 JSON 檔案
    for filename in os.listdir(output_dir):
        if filename.endswith(".json"):
            with open(os.path.join(output_dir, filename), 'r', encoding='utf-8') as file:
                data = json.load(file)
                # 格式化與存入 MongoDB
                doc = {
                    "name": filename.replace('.json', ''),
                    "folder_list": data
                }
                collection.insert_one(doc)
    print("所有資料已成功匯入 MongoDB。")

def main():
    create_output_folders()
    process_libraries()
    import_json_to_mongodb()

if __name__ == "__main__":
    main()
