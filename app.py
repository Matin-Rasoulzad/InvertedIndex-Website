from flask import Flask, render_template, jsonify, request
import os
import re
from collections import defaultdict

app = Flask(__name__)

# --- Configuration ---
FILES_DIR = 'documents'

# --- B-Tree Implementation ---
class BTreeNode:
    def __init__(self, leaf=False):
        self.leaf = leaf
        self.keys = []
        self.children = []

    def to_dict(self):
        return {
            "keys": self.keys,
            "children": [child.to_dict() for child in self.children],
            "leaf": self.leaf
        }

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
            
    def to_dict(self):
        return self.root.to_dict()

# --- IR System Logic ---
class IRSystem:
    def __init__(self):
        self.documents = {}
        self.inverted_index = defaultdict(list)
        self.term_counts = defaultdict(int)  # Track total frequency of each term
        self.btree = BTree(3)
        self.load_data()

    def load_data(self):
        if not os.path.exists(FILES_DIR):
            os.makedirs(FILES_DIR)
            return

        for filename in os.listdir(FILES_DIR):
            filepath = os.path.join(FILES_DIR, filename)
            if os.path.isfile(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.documents[filename] = content
                    self._index_document(filename, content)

    def _tokenize(self, text):
        return re.findall(r'\b\w+\b', text.lower())

    def _index_document(self, filename, content):
        tokens = self._tokenize(content)
        for token in tokens:
            self.term_counts[token] += 1  # Increment global term count
            
            if filename not in self.inverted_index[token]:
                self.inverted_index[token].append(filename)
            
            # Insert into B-Tree (only unique terms)
            if not self.btree.search(token):
                self.btree.insert(token)

    def search(self, query):
        query = query.lower().strip()
        if not query:
            return {"found": False, "results": []}
            
        found = self.btree.search(query)
        results = []
        
        if found:
            doc_list = self.inverted_index.get(query, [])
            for doc_name in doc_list:
                content = self.documents[doc_name]
                # Get context
                snippet = self._get_context(content, query)
                results.append({
                    "document": doc_name,
                    "snippet": snippet,
                    "count": len(re.findall(r'\b' + re.escape(query) + r'\b', content.lower()))
                })
                
        return {
            "found": found,
            "term": query,
            "results": results
        }

    def _get_context(self, content, term, context_chars=50):
        lower_content = content.lower()
        try:
            idx = lower_content.index(term)
            start = max(0, idx - context_chars)
            end = min(len(content), idx + len(term) + context_chars)
            return "..." + content[start:end] + "..."
        except ValueError:
            return ""

    def get_index_stats(self):
        # Create a list of dicts for easier sorting in frontend or backend
        stats = []
        for term, docs in self.inverted_index.items():
            stats.append({
                "term": term,
                "count": self.term_counts[term],
                "doc_count": len(docs),
                "docs": docs
            })
        
        # Sort by count (most to least)
        stats.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            "total_documents": len(self.documents),
            "total_terms": len(self.inverted_index),
            "terms": stats
        }
    
    def get_document(self, filename):
        return self.documents.get(filename, "")

ir_system = IRSystem()

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search')
def search():
    query = request.args.get('q', '')
    return jsonify(ir_system.search(query))

@app.route('/api/index-data')
def index_data():
    return jsonify(ir_system.get_index_stats())

@app.route('/api/btree-data')
def btree_data():
    return jsonify(ir_system.btree.to_dict())

@app.route('/api/document/<filename>')
def get_document(filename):
    content = ir_system.get_document(filename)
    return jsonify({"filename": filename, "content": content})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
