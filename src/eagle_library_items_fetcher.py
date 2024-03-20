import requests
from pymongo import MongoClient

class EagleItemsFetcher:
    def __init__(self, db_url='mongodb://localhost:27017/', library_name='My Knowledge Palace'):
        self.client = MongoClient(db_url)
        self.db = self.client['eagle']
        self.library_name = library_name

    def fetch_folders(self):
        collection = self.db['library']
        library_doc = collection.find_one({"name": self.library_name})
        return library_doc.get("folder_list", []) if library_doc else []

    @staticmethod
    def find_folder_ids(folder_id, folders, folder_ids=None):
        def recursive_search(search_id, folder, found_ids):
            children = folder.get("children", [])
            if folder.get("parent") == search_id:
                folder_id_tmp = folder.get("id")
                EagleItemsFetcher.find_folder_ids(folder_id_tmp, children, folder_ids)
            for child in children:
                recursive_search(search_id, child, found_ids)
        
        if folder_ids is None:
            folder_ids = []
        folder_ids.append(folder_id)
        for folder in folders:
            recursive_search(folder_id, folder, folder_ids)
        return folder_ids

    def fetch_items(self, folder_ids):
        url = f"http://localhost:41595/api/item/list?folders={','.join(folder_ids)}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json().get("data", [])
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return []

def print_folder_items(items):
    for item in items:
        print(f"folder: {item['id']}")
        print(f"name: {item['name']}")
        print(f"ext: {item['ext']}")

def main(folder_id):
    fetcher = EagleItemsFetcher()
    folders = fetcher.fetch_folders()
    folder_ids = fetcher.find_folder_ids(folder_id, folders)
    items = fetcher.fetch_items(folder_ids)
    return items

if __name__ == "__main__":
    # folder_id = "LOR7CNQXIBVQ7"
    folder_id = input("Enter the folder ID: ")
    items = main(folder_id)
    print_folder_items(items)
