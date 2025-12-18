#!/usr/bin/env python3
"""
Simple Notebook System for Writing Notes
"""

import json
import datetime
from pathlib import Path

class Notebook:
    def __init__(self, notebook_file="notes.json"):
        self.notebook_file = Path(notebook_file)
        self.notes = self._load_notes()
    
    def _load_notes(self):
        if self.notebook_file.exists():
            with open(self.notebook_file, 'r') as f:
                return json.load(f)
        return {"entries": []}
    
    def _save_notes(self):
        with open(self.notebook_file, 'w') as f:
            json.dump(self.notes, f, indent=2, default=str)
    
    def add_note(self, title, content, tags=None):
        """Add a new note"""
        entry = {
            "id": len(self.notes["entries"]) + 1,
            "timestamp": datetime.datetime.now().isoformat(),
            "title": title,
            "content": content,
            "tags": tags or []
        }
        
        self.notes["entries"].append(entry)
        self._save_notes()
        print(f"✓ Note added: {title}")
    
    def list_notes(self):
        """List all notes"""
        if not self.notes["entries"]:
            print("No notes found.")
            return
            
        for entry in self.notes["entries"]:
            print(f"\n[{entry['id']}] {entry['title']}")
            print(f"Date: {entry['timestamp'][:19]}")
            if entry['tags']:
                print(f"Tags: {', '.join(entry['tags'])}")
            print(f"Content: {entry['content']}")
    
    def search_notes(self, keyword):
        """Search notes by keyword"""
        results = []
        for entry in self.notes["entries"]:
            if (keyword.lower() in entry["title"].lower() or 
                keyword.lower() in entry["content"].lower()):
                results.append(entry)
        
        if results:
            print(f"\nFound {len(results)} notes matching '{keyword}':")
            for entry in results:
                print(f"[{entry['id']}] {entry['title']}")
        else:
            print(f"No notes found matching '{keyword}'")

def main():
    """Interactive notebook"""
    notebook = Notebook()
    
    print("📝 Notebook System")
    print("Commands: add, list, search, quit")
    
    while True:
        cmd = input("\n> ").strip().lower()
        
        if cmd == "quit":
            break
        elif cmd == "add":
            title = input("Title: ")
            content = input("Content: ")
            tags_input = input("Tags (comma-separated, optional): ")
            tags = [t.strip() for t in tags_input.split(",") if t.strip()]
            notebook.add_note(title, content, tags)
        elif cmd == "list":
            notebook.list_notes()
        elif cmd == "search":
            keyword = input("Search keyword: ")
            notebook.search_notes(keyword)
        else:
            print("Commands: add, list, search, quit")

if __name__ == "__main__":
    main()