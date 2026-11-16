#!/usr/bin/env python3
"""Prior-art queries for the two novelty stakes of issue 17, via arXiv API.

Prints query, hit count and titles. Run 2026-11-15; output in lit-search.out.
Absence in these results is absence in this search, not in the literature.
"""
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

QUERIES = [
    'all:"fraud proof" AND all:"machine learning"',
    'all:"optimistic machine learning"',
    'all:"model update" AND all:"verification" AND all:"bound"',
    'all:"neuron transplantation"',
    'all:"transplant" AND all:"independently trained" AND all:"neural"',
    'all:"weight space" AND all:"skill transfer"',
    'all:"commit reveal" AND all:"test set" AND all:"machine learning"',
    'all:"bit exact" AND all:"training reproducibility"',
    'all:"behavioural equivalence" AND all:"neural network" AND all:"verification"',
    'all:"model grafting" AND all:"neural"',
]
NS = {"a": "http://www.w3.org/2005/Atom", "o": "http://a9.com/-/spec/opensearch/1.1/"}

for q in QUERIES:
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {"search_query": q, "max_results": 5})
    with urllib.request.urlopen(url, timeout=30) as r:
        root = ET.fromstring(r.read())
    total = root.find("o:totalResults", NS).text
    titles = [" ".join(e.find("a:title", NS).text.split()) for e in root.findall("a:entry", NS)]
    print(f"QUERY {q}\n  total {total}")
    for t in titles:
        print(f"  - {t}")
