import re
import requests

def extract_github_url(text):
    # Regex genérica para capturar URLs GitHub com /blob/ e qualquer extensão de arquivo
    url_pattern = r"https?://github\.com(?:/[\w\-./%]+)+/blob/(?:[\w\-./%() ]+?\.(?:js|py|html|css|txt|md|json|java|cpp|c|php|rb))"
    match = re.search(url_pattern, text, re.IGNORECASE)
    return match.group(0).strip() if match else None

def download_file_content(file_url, valid_extensions=None):
    if valid_extensions is None:
        valid_extensions = [".js", ".py", ".html", ".css", ".txt", ".md", ".json", ".java", ".cpp", ".c", ".php", ".rb"]
    extension = "." + file_url.split(".")[-1].lower()
    if not file_url or "/blob/" not in file_url or extension not in valid_extensions:
        print(f"Link inválido ou extensão não suportada ({extension}): {file_url}. Verifique o link. Extensões válidas: {valid_extensions}")
        return None
    raw_url = file_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    print(f"Baixando de: {raw_url}")
    try:
        response = requests.get(raw_url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Falha ao baixar {raw_url}: {e}")
        return None