import deepl
import os
from urllib.parse import unquote
import requests
from xmindparser import xmind_to_dict
from eagle_library_items_fetcher import EagleItemsFetcher
from decouple import config

def get_file_path(item):
    url = f"http://localhost:41595/api/item/thumbnail?id={item['id']}"
    response = requests.get(url)
    response.raise_for_status()
    thumbnail_path = unquote(response.json()['data'])
    file_path = os.path.join(os.path.dirname(thumbnail_path), item['name'] + '.xmind')
    return file_path

def format_topic(topic, level=0):
    indent = "\t" * level
    formatted = f"{indent}{topic['title']}\n"
    if 'topics' in topic:
        for subtopic in topic['topics']:
            formatted += format_topic(subtopic, level + 1)
    return formatted

def translate_to_english(text):
    auth_key = config('DEEPL_API_KEY')
    translator = deepl.Translator(auth_key)
    result = translator.translate_text(text, target_lang="EN-US")
    return result.text

def export_xmind_to_txt(file_path, output_path):
    data = xmind_to_dict(file_path)
    plain_text = ""
    for sheet in data:
        if 'topic' in sheet:
            main_topic = sheet['topic']
            plain_text += format_topic(main_topic)
    workspace_folder = os.path.dirname(os.path.abspath(__file__))
    file_name = os.path.basename(file_path).rsplit('.', 1)[0]
    eng_file_name = translate_to_english(file_name)
    out_file = os.path.join(workspace_folder, output_path, eng_file_name + ".txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(plain_text)
    print(f"Exported mind map to '{out_file}'")
    return out_file

def upload_to_eagle(file_path, folder_id):
    data = {
        "path": file_path,
        "folderId": folder_id
    }
    try:
        response = requests.post("http://localhost:41595/api/item/addFromPath", json=data)
        response.raise_for_status()
        print(f"Uploaded {file_path} to Eagle successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to upload {file_path} to Eagle: {e}")

def process_items(folder_id):
    fetcher = EagleItemsFetcher()
    folders = fetcher.fetch_folders()
    folder_ids = fetcher.find_folder_ids(folder_id, folders)
    items = fetcher.fetch_items(folder_ids)
    output_path = 'output/plain_text'
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    print(folder_ids)
    for item in items:
        if item['ext'].lower() == 'xmind':
            file_path = get_file_path(item)
            text_file_path = export_xmind_to_txt(file_path, output_path)
            upload_to_eagle(text_file_path, item['folders'])

if __name__ == "__main__":
    # folder_id = "LOR996EAMOMN5"
    folder_id = input("Enter the folder ID: ")
    process_items(folder_id)
