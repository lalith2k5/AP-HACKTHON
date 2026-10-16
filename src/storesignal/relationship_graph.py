"""
StoreSignal AI — Relationship Graph (P2 stretch)
================================================
Builds a NetworkX graph linking:
  - regions -> stores -> incidents -> categories -> owners

Exports:
  data/processed/relationship_graph.graphml
  data/processed/relationship_graph.json  (node-link JSON, for UI)
"""

import json

import networkx as nx
import pandas as pd

from storesignal.paths import (
    CODE_ROOT,
    PROCESSED_DIR,
    REFERENCE_DIR,
)

ROOT = CODE_ROOT
PROC = PROCESSED_DIR
REF = REFERENCE_DIR

OUT_GRAPHML = PROC / "relationship_graph.graphml"
OUT_JSON = PROC / "relationship_graph.json"
REPORT = PROC / "graph_report.json"


def build():
    incidents = pd.read_parquet(PROC / "incidents.parquet", engine="pyarrow")
    stores = pd.read_csv(REF / "store_master.csv", dtype=str)

    G = nx.Graph()

    # Add regions
    for region_id, region_name in stores[["region_id", "region_name"]].drop_duplicates().itertuples(index=False):
        G.add_node(region_id, kind="region", label=region_name)

    # Add stores + region->store edges
    for row in stores.itertuples(index=False):
        G.add_node(row.store_id, kind="store", label=row.store_name,
                   region_id=row.region_id, size_band=row.size_band)
        G.add_edge(row.region_id, row.store_id, kind="contains")

    # Add categories + owners
    for _, r in incidents.iterrows():
        G.add_node(r["predicted_category"], kind="category", label=r["predicted_category"])
        G.add_node(r["owner_function"], kind="owner", label=r["owner_function"])
        G.add_edge(r["predicted_category"], r["owner_function"], kind="routed_to")

    # Add incident nodes and edge store/category
    for _, r in incidents.iterrows():
        inc_id = r["incident_id"]
        G.add_node(inc_id, kind="incident", severity=r["severity"],
                   record_count=int(r["record_count"]))
        G.add_edge(r["store_id"], inc_id, kind="reported")
        G.add_edge(inc_id, r["predicted_category"], kind="categorized_as")

    nx.write_graphml(G, OUT_GRAPHML)

    data = nx.node_link_data(G, edges="links")
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    # Compute basic stats
    degrees = dict(G.degree())
    hubs = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:10]

    report = {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "regions": sum(1 for _, d in G.nodes(data=True) if d.get("kind") == "region"),
        "stores": sum(1 for _, d in G.nodes(data=True) if d.get("kind") == "store"),
        "categories": sum(1 for _, d in G.nodes(data=True) if d.get("kind") == "category"),
        "owners": sum(1 for _, d in G.nodes(data=True) if d.get("kind") == "owner"),
        "incidents": sum(1 for _, d in G.nodes(data=True) if d.get("kind") == "incident"),
        "top_hubs": [{"node": n, "degree": d} for n, d in hubs],
    }
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"[graph] Wrote {OUT_GRAPHML}")
    print(f"[graph] Wrote {OUT_JSON}")
    print(f"[graph] Wrote {REPORT}")
    print(f"[graph] Nodes={report['nodes']} Edges={report['edges']}")
    print(f"[graph] Top hubs: {report['top_hubs'][:5]}")


if __name__ == "__main__":
    build()
