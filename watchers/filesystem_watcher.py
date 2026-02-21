import sys
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class DropFolderHandler(FileSystemEventHandler):
    def __init__(self, vault_path: str):
        super().__init__()
        self.vault_path = Path(vault_path)
        self.needs_action = Path(vault_path) / 'Needs_Action'
        self.logger = logging.getLogger(self.__class__.__name__)

    def on_created(self, event):
        if not event.is_directory:
            source = Path(event.src_path)
            dest = self.needs_action / f'FILE_{source.name}.md'
            try:
                # Wait a bit for file to be fully written
                import time
                time.sleep(0.5)
                # Retry logic for file lock issues on Windows
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        self.create_markdown_file(source, dest)
                        # Also copy original file
                        shutil.copy2(source, self.needs_action / source.name)
                        break
                    except PermissionError as e:
                        if attempt < max_retries - 1:
                            self.logger.warning(f"File locked, retrying ({attempt + 1}/{max_retries}): {source}")
                            time.sleep(1)
                        else:
                            raise
            except Exception as e:
                self.logger.error(f"Error processing file {source}: {e}")

    def create_markdown_file(self, source: Path, dest: Path):
        # Read original content
        content = ""
        try:
            content = source.read_text(encoding='utf-8')
        except:
            content = "File dropped for processing."
        
        # Create markdown with frontmatter and content
        md_content = f"""---
type: file_drop
original_name: {source.name}
size: {source.stat().st_size}
---

{content}
"""
        dest.write_text(md_content, encoding='utf-8')

class FileSystemWatcher:
    def __init__(self, vault_path: str = 'AI_Employee_Vault'):
        self.vault_path = Path(vault_path)
        self.drop_folder = self.vault_path / 'Drop'
        self.needs_action = self.vault_path / 'Needs_Action'
        self.observer = Observer()
        self.handler = DropFolderHandler(str(vault_path))

        # Create directories if they don't exist
        self.drop_folder.mkdir(parents=True, exist_ok=True)
        self.needs_action.mkdir(parents=True, exist_ok=True)

    def run(self):
        self.observer.schedule(self.handler, str(self.drop_folder), recursive=False)
        self.observer.start()
        logging.info(f"Watching {self.drop_folder} for new files...")
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Stopping file system watcher...")
            self.observer.stop()
        self.observer.join()


if __name__ == "__main__":
    watcher = FileSystemWatcher()
    watcher.run()