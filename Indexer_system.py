import os
import re
import time
import sys
from collections import defaultdict
from colorama import init, Fore, Back, Style

# Initialize colorama
init(autoreset=True)

# --- Configuration ---
FILES_DIR = 'documents'

# --- B-Tree Logic (Identical to app.py) ---
class BTreeNode:
    def __init__(self, leaf=False):
        self.leaf = leaf
        self.keys = []
        self.children = []

class BTree:
    def __init__(self, t):
        self.root = BTreeNode(True)
        self.t = t

    def insert(self, k):
        root = self.root
        if len(root.keys) == (2 * self.t) - 1:
            temp = BTreeNode()
            self.root = temp
            temp.children.insert(0, root)
            self.split_child(temp, 0)
            self.insert_non_full(temp, k)
        else:
            self.insert_non_full(root, k)

    def insert_non_full(self, x, k):
        i = len(x.keys) - 1
        if x.leaf:
            x.keys.append(None)
            while i >= 0 and k < x.keys[i]:
                x.keys[i + 1] = x.keys[i]
                i -= 1
            x.keys[i + 1] = k
        else:
            while i >= 0 and k < x.keys[i]:
                i -= 1
            i += 1
            if len(x.children[i].keys) == (2 * self.t) - 1:
                self.split_child(x, i)
                if k > x.keys[i]:
                    i += 1
            self.insert_non_full(x.children[i], k)

    def split_child(self, x, i):
        t = self.t
        y = x.children[i]
        z = BTreeNode(y.leaf)
        x.children.insert(i + 1, z)
        x.keys.insert(i, y.keys[t - 1])
        z.keys = y.keys[t: (2 * t) - 1]
        y.keys = y.keys[0: t - 1]
        if not y.leaf:
            z.children = y.children[t: 2 * t]
            y.children = y.children[0: t]

    def search(self, k, x=None):
        if x is None:
            x = self.root
        i = 0
        while i < len(x.keys) and k > x.keys[i]:
            i += 1
        if i < len(x.keys) and k == x.keys[i]:
            return True
        elif x.leaf:
            return False
        else:
            return self.search(k, x.children[i])

# --- Terminal UI Helpers ---
class NeonUI:
    MAGENTA = Fore.MAGENTA + Style.BRIGHT
    CYAN = Fore.CYAN + Style.BRIGHT
    WHITE = Fore.WHITE + Style.BRIGHT
    DIM = Fore.WHITE + Style.DIM
    RESET = Style.RESET_ALL

    @staticmethod
    def banner():
        print(f"\n{NeonUI.MAGENTA}" + "╔" + "═"*78 + "╗")
        print(f"{NeonUI.MAGENTA}║ {NeonUI.CYAN}   NEON INDEXER SYSTEM v2.0   {NeonUI.MAGENTA}" + " "*46 + "║")
        print(f"{NeonUI.MAGENTA}║ {NeonUI.DIM}   Advanced Inverted Index & B-Tree Visualization   {NeonUI.MAGENTA}" + " "*26 + "║")
        print(f"{NeonUI.MAGENTA}" + "╚" + "═"*78 + "╝" + NeonUI.RESET)

    @staticmethod
    def section(title):
        print(f"\n{NeonUI.CYAN}>> {title} {NeonUI.MAGENTA}" + "-"*(75-len(title)) + NeonUI.RESET)

    @staticmethod
    def success(msg):
        print(f"{NeonUI.MAGENTA}[+] {NeonUI.WHITE}{msg}{NeonUI.RESET}")

    @staticmethod
    def error(msg):
        print(f"{Fore.RED}[!] {msg}{NeonUI.RESET}")

    @staticmethod
    def info(key, value):
        print(f" {NeonUI.MAGENTA}• {NeonUI.CYAN}{key:<25} : {NeonUI.WHITE}{value}{NeonUI.RESET}")

# --- Main System Class ---
class TerminalIRSystem:
    def __init__(self):
        self.documents = {}
        self.inverted_index = defaultdict(list)
        self.term_counts = defaultdict(int)
        self.btree = BTree(3)

    def run(self):
        NeonUI.banner()
        
        # 1. Load & Process
        NeonUI.section("INITIALIZING SYSTEM")
        self.load_documents()
        
        # 2. Stats
        NeonUI.section("SYSTEM STATISTICS")
        self.display_stats()

        # 3. Index Preview
        NeonUI.section("INVERTED INDEX PREVIEW (Top 10 by Freq)")
        self.display_index_preview()

        # 4. B-Tree Viz
        NeonUI.section("B-TREE STRUCTURE")
        self.visualize_btree(self.btree.root)

        # 5. Interactive Search
        self.interactive_loop()

    def load_documents(self):
        start_time = time.time()
        if not os.path.exists(FILES_DIR):
            NeonUI.error(f"Directory '{FILES_DIR}' not found!")
            return

        files = [f for f in os.listdir(FILES_DIR) if f.endswith('.txt')]
        if not files:
            NeonUI.error("No text files found.")
            return

        print(f"{NeonUI.DIM}Loading files from: {FILES_DIR}/{NeonUI.RESET}")
        
        for filename in files:
            filepath = os.path.join(FILES_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                self.documents[filename] = content
                self._index_content(filename, content)
                print(f" {NeonUI.MAGENTA}→ {NeonUI.WHITE}Indexed: {filename:<20} {NeonUI.DIM}({len(content)} chars){NeonUI.RESET}")

        elapsed = time.time() - start_time
        NeonUI.success(f"Successfully processed {len(files)} documents in {elapsed:.4f}s")

    def _index_content(self, filename, content):
        tokens = re.findall(r'\b\w+\b', content.lower())
        for token in tokens:
            self.term_counts[token] += 1
            if filename not in self.inverted_index[token]:
                self.inverted_index[token].append(filename)
            if not self.btree.search(token):
                self.btree.insert(token)

    def display_stats(self):
        total_terms = len(self.inverted_index)
        total_occurrences = sum(self.term_counts.values())
        
        NeonUI.info("Total Documents", len(self.documents))
        NeonUI.info("Unique Terms", f"{total_terms:,}")
        NeonUI.info("Total Token Count", f"{total_occurrences:,}")
        NeonUI.info("B-Tree Degree", self.btree.t)

    def display_index_preview(self):
        # Sort by frequency
        sorted_terms = sorted(self.inverted_index.items(), key=lambda x: self.term_counts[x[0]], reverse=True)[:10]
        
        print(f"{NeonUI.MAGENTA} {'TERM':<20} | {'FREQ':<8} | {'DOCS'}")
        print(f"{NeonUI.MAGENTA}" + "-"*60)
        
        for term, docs in sorted_terms:
            count = self.term_counts[term]
            doc_str = ", ".join(docs)
            if len(doc_str) > 30: doc_str = doc_str[:27] + "..."
            print(f" {NeonUI.CYAN}{term:<20} {NeonUI.MAGENTA}| {NeonUI.WHITE}{count:<8} {NeonUI.MAGENTA}| {NeonUI.DIM}{doc_str}")

    def visualize_btree(self, node, level=0, prefix="Root: "):
        if node is None: return
        
        indent = " " * (level * 4)
        keys_str = f"[{', '.join(str(k) for k in node.keys if k is not None)}]"
        
        color = NeonUI.CYAN if level == 0 else NeonUI.WHITE
        if node.leaf: color = NeonUI.DIM
        
        print(f"{indent}{NeonUI.MAGENTA}└─ {color}{keys_str}")
        
        if not node.leaf:
            for child in node.children:
                self.visualize_btree(child, level + 1)

    def interactive_loop(self):
        NeonUI.section("INTERACTIVE SEARCH CONSOLE")
        print(f"{NeonUI.DIM}Type 'exit' to quit.{NeonUI.RESET}\n")

        while True:
            try:
                query = input(f"{NeonUI.MAGENTA}Search > {NeonUI.CYAN}").strip().lower()
                
                if query in ['exit', 'quit', 'q']:
                    print(f"\n{NeonUI.MAGENTA}Shutting down... Goodbye!{NeonUI.RESET}")
                    break
                
                if not query: continue

                self.perform_search(query)

            except KeyboardInterrupt:
                break

    def perform_search(self, term):
        print(f"{NeonUI.MAGENTA}" + "-"*40)
        
        # 1. B-Tree Lookup
        found = self.btree.search(term)
        status = f"{NeonUI.CYAN}FOUND" if found else f"{Fore.RED}NOT FOUND"
        print(f" B-Tree Lookup: {status}")

        if found:
            # 2. Stats
            count = self.term_counts[term]
            docs = self.inverted_index[term]
            print(f" Frequency:     {NeonUI.WHITE}{count}")
            print(f" Documents:     {NeonUI.WHITE}{', '.join(docs)}")
            
            # 3. Context
            print(f"\n {NeonUI.MAGENTA}[ Context Snippets ]{NeonUI.RESET}")
            for doc in docs:
                content = self.documents[doc]
                snippet = self._get_snippet(content, term)
                print(f" {NeonUI.CYAN}{doc:<15} {NeonUI.MAGENTA}│ {NeonUI.DIM}{snippet}")
        
        print(f"{NeonUI.MAGENTA}" + "-"*40 + "\n")

    def _get_snippet(self, content, term):
        try:
            lower = content.lower()
            idx = lower.find(term)
            if idx == -1: return ""
            
            start = max(0, idx - 30)
            end = min(len(content), idx + len(term) + 30)
            text = content[start:end].replace('\n', ' ')
            return f"...{text}..."
        except:
            return ""

if __name__ == "__main__":
    app = TerminalIRSystem()
    app.run()
