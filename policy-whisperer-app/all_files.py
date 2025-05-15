import os

EXCLUDED_DIRS = {'.git', '__pycache__', '.venv', '.idea', '.DS_Store'}

def print_tree_with_contents(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Modify dirnames in-place to skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]

        for filename in filenames:
            if filename.startswith('.') or filename in EXCLUDED_DIRS:
                continue

            file_path = os.path.join(dirpath, filename)
            print(f"\n{'=' * 80}")
            print(f"File: {file_path}")
            print(f"{'-' * 80}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    print(f.read())
            except Exception as e:
                print(f"Could not read file: {e}")


if __name__ == "__main__":
    print_tree_with_contents(".")  # or replace "." with a specific path
