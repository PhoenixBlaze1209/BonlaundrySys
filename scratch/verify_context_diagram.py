"""
scratch/verify_context_diagram.py
Comprehensive integrity and validation test for Context Diagram (16 flows).
"""

import xml.etree.ElementTree as ET
from pathlib import Path

DIAGRAM_FILE = Path(r"c:\Users\genes\bon-laundry\docs\diagrams\context_diagram.drawio")


def test_context_diagram():
    assert DIAGRAM_FILE.exists(), f"File does not exist: {DIAGRAM_FILE}"
    content = DIAGRAM_FILE.read_text(encoding="utf-8")
    root = ET.fromstring(content)

    cells = root.findall(".//mxCell")
    print(f"Total mxCell elements: {len(cells)}")

    vertices = {}
    edges = []

    for cell in cells:
        cid = cell.get("id")
        val = cell.get("value", "")
        if cell.get("vertex") == "1":
            vertices[cid] = val
        elif cell.get("edge") == "1":
            edges.append(cell)

    print(f"Vertices count: {len(vertices)}")
    print(f"Edges count: {len(edges)}")

    assert len(vertices) == 5, f"Expected 5 vertices (sysh, sysb, e_cust, e_staff, e_mgr), got {len(vertices)}"
    assert len(edges) == 16, f"Expected 16 edges, got {len(edges)}"

    # Check Process 0 label
    assert vertices["sysh"] == "0", f"Expected Process number '0', got '{vertices['sysh']}'"

    # Verify each edge
    process_nodes = {"sysh", "sysb"}
    external_entities = {"e_cust", "e_staff", "e_mgr"}

    cust_edges = []
    staff_edges = []
    mgr_edges = []

    for edge in edges:
        eid = edge.get("id")
        val = edge.get("value", "").strip()
        src = edge.get("source")
        tgt = edge.get("target")

        assert val, f"Edge {eid} has empty label!"
        assert src in vertices, f"Edge {eid} source {src} not found in vertices!"
        assert tgt in vertices, f"Edge {eid} target {tgt} not found in vertices!"

        # DFD Context Diagram Rule: Every edge must connect an external entity to the central process
        is_entity_to_proc = (src in external_entities and tgt in process_nodes)
        is_proc_to_entity = (src in process_nodes and tgt in external_entities)
        assert is_entity_to_proc or is_proc_to_entity, (
            f"Edge {eid} ('{val}') violates DFD rule: connects {src} to {tgt}"
        )

        ent = src if src in external_entities else tgt
        direction = "in" if is_entity_to_proc else "out"

        if ent == "e_cust":
            cust_edges.append((eid, val, direction))
            assert "register" not in val.lower(), f"Customer flow has forbidden 'register': {val}"
            assert "login" not in val.lower(), f"Customer flow has forbidden 'login': {val}"
        elif ent == "e_staff":
            staff_edges.append((eid, val, direction))
        elif ent == "e_mgr":
            mgr_edges.append((eid, val, direction))

    print(f"\nCustomer Edges ({len(cust_edges)}):")
    for eid, val, d in cust_edges:
        print(f"  [{d.upper()}] {eid}: {val}")

    print(f"\nStaff Edges ({len(staff_edges)}):")
    for eid, val, d in staff_edges:
        print(f"  [{d.upper()}] {eid}: {val}")

    print(f"\nManager Edges ({len(mgr_edges)}):")
    for eid, val, d in mgr_edges:
        print(f"  [{d.upper()}] {eid}: {val}")

    assert len(cust_edges) == 6, f"Expected 6 customer edges, got {len(cust_edges)}"
    assert len(staff_edges) == 6, f"Expected 6 staff edges, got {len(staff_edges)}"
    assert len(mgr_edges) == 4, f"Expected 4 manager edges, got {len(mgr_edges)}"

    # Check balanced in/out
    cust_in = sum(1 for _, _, d in cust_edges if d == "in")
    cust_out = sum(1 for _, _, d in cust_edges if d == "out")
    staff_in = sum(1 for _, _, d in staff_edges if d == "in")
    staff_out = sum(1 for _, _, d in staff_edges if d == "out")
    mgr_in = sum(1 for _, _, d in mgr_edges if d == "in")
    mgr_out = sum(1 for _, _, d in mgr_edges if d == "out")

    assert cust_in == 3 and cust_out == 3, f"Customer not balanced: in={cust_in}, out={cust_out}"
    assert staff_in == 3 and staff_out == 3, f"Staff not balanced: in={staff_in}, out={staff_out}"
    assert mgr_in == 2 and mgr_out == 2, f"Manager not balanced: in={mgr_in}, out={mgr_out}"

    print("\nALL 16 CONTEXT DIAGRAM DATA FLOW CHECKS PASSED (NO MIRACLES, NO BLACK HOLES, STRICT DFD RULES)!")


if __name__ == "__main__":
    test_context_diagram()
