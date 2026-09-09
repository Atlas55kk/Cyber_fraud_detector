import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import time
import os

queries = [
    'all:"taint analysis" AND all:"blockchain"',
    'all:"money laundering" AND all:"Ethereum"',
    'all:"subgraph" AND all:"money laundering" AND all:"blockchain"',
    'all:"peel chain" OR all:"smurfing" AND all:"cryptocurrency"',
    'all:"Tornado Cash" AND (all:"trace" OR all:"deanonymize" OR all:"heuristic")',
    'all:"Graph Neural Network" AND all:"Anti-Money Laundering" AND all:"blockchain"',
    'all:"account-based" AND all:"blockchain" AND (all:"tracing" OR all:"forensics")',
    'all:"clustering heuristics" AND all:"Bitcoin" OR all:"Ethereum"'
]

papers = []
seen_titles = set()

print(f"[*] Querying arXiv API across {len(queries)} specific research areas...")

for q in queries:
    encoded_q = urllib.parse.quote(q)
    url = f"http://export.arxiv.org/api/query?search_query={encoded_q}&start=0&max_results=6&sortBy=relevance&sortOrder=descending"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'CryptoForensicsResearch/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            root = ET.fromstring(data)
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip().replace('\n', ' ')
                title_clean = " ".join(title.split())
                if title_clean.lower() in seen_titles:
                    continue
                seen_titles.add(title_clean.lower())
                
                arxiv_id = entry.find('{http://www.w3.org/2005/Atom}id').text.strip()
                published = entry.find('{http://www.w3.org/2005/Atom}published').text.strip()[:10]
                summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip().replace('\n', ' ')
                summary_clean = " ".join(summary.split())
                
                authors = [a.find('{http://www.w3.org/2005/Atom}name').text.strip() for a in entry.findall('{http://www.w3.org/2005/Atom}author')]
                
                papers.append({
                    'title': title_clean,
                    'authors': authors,
                    'published': published,
                    'arxiv_id': arxiv_id,
                    'summary': summary_clean
                })
        time.sleep(1) # respectful API delay
    except Exception as e:
        print(f"Error querying {q}: {e}")

print(f"[+] Total unique relevant papers found: {len(papers)}")

# Save to papers_read.txt
txt_path = "research/papers_read.txt"
with open(txt_path, "w", encoding="utf-8") as f:
    f.write("="*80 + "\n")
    f.write("CRYPTOCURRENCY FRAUD TRACING & FORENSICS: RESEARCH LITERATURE LOG\n")
    f.write(f"Total Papers Surveyed: {len(papers)}\n")
    f.write("="*80 + "\n\n")
    
    for i, p in enumerate(papers, 1):
        f.write(f"[{i}] {p['title']}\n")
        f.write(f"    Authors: {', '.join(p['authors'])}\n")
        f.write(f"    Date: {p['published']} | ID: {p['arxiv_id']}\n")
        f.write(f"    Abstract Summary:\n    {p['summary']}\n")
        f.write("-" * 80 + "\n\n")

print(f"[+] Successfully wrote {len(papers)} papers to {txt_path}")
