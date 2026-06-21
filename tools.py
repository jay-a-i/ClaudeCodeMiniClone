import os
from dotenv import load_dotenv
from pathlib import Path
from tavily import AsyncTavilyClient

load_dotenv()

tavily = AsyncTavilyClient(os.getenv("TAVILY_API_KEY"))

async def search_web(query: str):
    response = await tavily.search(
        query=query,
        max_results=3,
        search_depth='advanced')
    content_list = []
    for result in response['results']:
        content_list.append(f"Source: {result['url']}\nContent: {result['content']}")
    return "\n\n".join(content_list)

def read_file(file_path):
    try:
        output_lines = []
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                output_lines.append(f"{line_num:3} | {line}")      
        return "".join(output_lines)
    except FileNotFoundError:
        return "The file does not exist."

def list_directory(dir_path: str, indent_lvl=0, ignore_list=None, output=None):
    if output is None:
        output = []
    if ignore_list is None:
        ignore_list = {".git", ".gitignore", "__pycache__", ".vscode", ".DS_Store", "node_modules", ".venv", ".python-version"}
    try:
        path = Path(dir_path)
        spacer = "    " * indent_lvl
        if indent_lvl == 0:
            output.append(f"{path.name}/")
            indent_lvl += 1
            spacer = "    " * indent_lvl
        filtered_items = [x for x in path.iterdir() if x.name not in ignore_list]
        sorted_items = sorted(filtered_items, key=lambda x: (not x.is_dir(), x.name.lower()))
        for item in sorted_items:
            if item.is_dir():
                output.append(f"{spacer}{item.name}/")
                list_directory(str(item), indent_lvl + 1, ignore_list, output)
            else:
                output.append(f"{spacer}{item.name}")
    except (FileNotFoundError, PermissionError) as e:
        output.append(f"{spacer}[Error: {e.strerror}]")

    if indent_lvl <= 1:
        return "\n".join(output)
    
def write_file(file_path, content):
    try:
        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        with open(f'{file_path}', 'w', encoding='utf-8') as file:
            file.write(content)
            return f"Success: File successfully written at '{file_path}'"
    except Exception as e:
        return f"[Error Occured: {e}]"

def edit_file(file_path, old_content, new_content):
    output = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()
            match_count = file_content.count(old_content)

            if match_count == 0:
                output.append("Error: The old text was not found in the file.")
                return "\n".join(output)
            elif match_count > 1:
                output.append(f"Warning: Found {match_count} matches, replacing only the first occurrence.")
            
            output.append("Found match!")
            updated_content = file_content.replace(old_content, new_content, 1)
            
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(updated_content)
                output.append("Successfully added the new content!")
            except Exception as e:
                    output.append(f"Unable to write anything in the given file!\n[Error: {e}]")    

    except Exception as e:
        output.append(f"[Error: {e}]")
    return "\n".join(output)

def grep(root_dir, search_term, ext_filter=None):
    
    IGNORE_LIST = {
        '.git', 'node_modules', '__pycache__', '.venv', 'venv', 
        '.DS_Store', 'dist', 'build', '.idea', '.vscode',
    }
    BINARY_EXTENSIONS = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.pdf',
        '.zip', '.tar', '.gz', '.7z', '.rar', '.mp3', '.mp4',
        '.pyc', '.exe', '.dll', '.so', '.dylib', '.db', '.sqlite'
    }
    results = []
    total_matches = 0
    
    if ext_filter and not ext_filter.startswith('.'):
        ext_filter = '.' + ext_filter.lower()

    for current_root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_LIST]
        
        for file_name in files:
            if file_name in IGNORE_LIST:
                continue
            
            file_path = os.path.join(current_root, file_name)
            _, ext = os.path.splitext(file_name.lower())

            if ext_filter and ext != ext_filter:
                continue

            if ext in BINARY_EXTENSIONS:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # errors='ignore' helps skip hidden binary characters without throwing a crash
                    
                    for line_num, line in enumerate(f, start=1):
                        if search_term in line:
                            clean_line = line.strip()
                
                            results.append({
                                'file': os.path.relpath(file_path, root_dir),
                                'line': line_num,
                                'text': clean_line
                            })
                            total_matches += 1
                            
            except (PermissionError, FileNotFoundError):
                continue
    if not results:
        return f"No matches found for '{search_term}' in directory: {root_dir}"
        
    output_lines = [
        f"Search Results for '{search_term}'",
        f"Total Matches Found: {total_matches}",
        "-" * 60
    ]
    
    for match in results:
        output_lines.append(f"File: {match['file']} (Line {match['line']})")
        output_lines.append(f"Match: {match['text']}\n")
        
    return "\n".join(output_lines)