from __future__ import annotations
import argparse
import os
import pickle
import struct
import sys
from collections import defaultdict, deque
from statistics import mean
from typing import Any, List, Sequence

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Try to import ensemble, but don't fail if missing (for standalone use)
try:
    from ensemble_compilation.spn_ensemble import read_ensemble
except ImportError:
    read_ensemble = None

PRIMITIVES = (int, float, bool, str, bytes)


def load_pickle(path: str) -> Any:
    with open(path, "rb") as handle:
        return pickle.load(handle)


def extract_roots(obj: Any) -> List[Any]:
    if obj is None:
        return []
    candidates: List[Any] = []
    if isinstance(obj, dict):
        for key in ("model", "root", "roots", "spn", "ensemble", "components"):
            val = obj.get(key)
            if val is None:
                continue
            if isinstance(val, (list, tuple, set)):
                candidates.extend(val)
            else:
                candidates.append(val)
    if not candidates:
        if isinstance(obj, (list, tuple, set)):
            candidates = list(obj)
        else:
            candidates = [obj]
    return [c for c in candidates if c is not None]


def node_like(value: Any) -> bool:
    if value is None or isinstance(value, PRIMITIVES):
        return False
    return hasattr(value, "__dict__") or hasattr(value, "__slots__")


def extract_children(node: Any) -> List[Any]:
    child_attrs = (
        "children",
        "child_nodes",
        "nodes",
        "sub_nodes",
        "subnodes",
        "subtree",
        "factors",
        "branches",
    )
    collected: List[Any] = []
    for attr in child_attrs:
        if hasattr(node, attr):
            value = getattr(node, attr)
            collected.extend(_normalize_children(value))
    for attr in ("left", "right"):
        if hasattr(node, attr):
            collected.extend(_normalize_children(getattr(node, attr)))
    unique = []
    seen = set()
    for child in collected:
        if not node_like(child):
            continue
        if id(child) in seen:
            continue
        seen.add(id(child))
        unique.append(child)
    return unique


def _normalize_children(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, dict):
        iterable = value.values()
    elif isinstance(value, (list, tuple, set)):
        iterable = value
    else:
        iterable = (value,)
    return [item for item in iterable if item is not None]


def detect_kind(node: Any, child_count: int) -> str:
    for attr_name in ("node_type", "type", "kind", "op", "operation"):
        attr = getattr(node, attr_name, None)
        if isinstance(attr, str):
            lowered = attr.lower()
            if "sum" in lowered:
                return "sum"
            if "prod" in lowered or "mul" in lowered:
                return "product"
    class_name = node.__class__.__name__.lower()
    if "sum" in class_name:
        return "sum"
    if "prod" in class_name or "mul" in class_name:
        return "product"
    if child_count == 0:
        return "leaf"
    return "internal"


def extract_weights(node: Any) -> Sequence[float]:
    for attr in ("weights", "w", "probs", "probabilities"):
        if hasattr(node, attr):
            value = getattr(node, attr)
            if value is None:
                continue
            if isinstance(value, PRIMITIVES):
                return [float(value)]
            if isinstance(value, (list, tuple)):
                return [float(v) for v in value]
            if hasattr(value, "tolist"):
                return [float(v) for v in value.tolist()]
    return []


def detect_bitmap_leaf(node: Any) -> bool:
    # Based on code analysis of rspn/structure/leaves.py and rspn/learning/rspn_learning.py
    # The attribute used to store bitmaps is 'unique_vals_ids'
    return hasattr(node, "unique_vals_ids") and node.unique_vals_ids is not None


def extract_scope_size(node: Any) -> int | None:
    for attr in ("scope", "scopes", "variables", "vars", "var_scope"):
        if hasattr(node, attr):
            scope = getattr(node, attr)
            if scope is None:
                continue
            if isinstance(scope, (list, tuple, set)):
                return len(scope)
            if isinstance(scope, dict):
                return len(scope)
            if isinstance(scope, int):
                return 1
    return None


def format_node(node: Any, kind: str, degree: int) -> str:
    label = getattr(node, "name", None) or getattr(
        node, "label", None) or getattr(node, "id", None)
    bits = [kind, node.__class__.__name__, f"deg={degree}"]
    if label is not None:
        bits.append(f"id={label}")
    scope_size = extract_scope_size(node)
    if scope_size is not None:
        bits.append(f"scope={scope_size}")
    return "<" + ", ".join(bits) + ">"


def collect_spn_stats(
    root: Any,
    snapshot_depth: int,
    snapshot_width: int,
) -> dict[str, Any]:
    queue = deque([(root, 0)])
    visited = set()
    layer_counts = defaultdict(lambda: defaultdict(int))
    layer_branching = defaultdict(list)
    snapshots = defaultdict(list)

    totals = {
        "nodes": 0,
        "sum": 0,
        "product": 0,
        "leaf": 0,
        "internal": 0,
        "bitmap_leaves": 0,
    }
    sum_max_branch = 0
    prod_max_branch = 0
    leaf_scope_sizes: List[int] = []
    sum_weights_stats: List[Sequence[float]] = []

    max_depth = 0

    while queue:
        node, depth = queue.popleft()
        node_id = id(node)
        if node_id in visited:
            continue
        visited.add(node_id)

        children = extract_children(node)
        degree = len(children)
        kind = detect_kind(node, degree)

        totals["nodes"] += 1
        totals[kind] = totals.get(kind, 0) + 1
        layer_counts[depth][kind] += 1
        if degree:
            layer_branching[depth].append(degree)

        if depth <= snapshot_depth and len(snapshots[depth]) < snapshot_width:
            snapshots[depth].append(format_node(node, kind, degree))

        if kind == "sum":
            sum_max_branch = max(sum_max_branch, degree)
            weights = extract_weights(node)
            if weights:
                sum_weights_stats.append(weights)
        elif kind == "product":
            prod_max_branch = max(prod_max_branch, degree)
        elif degree == 0:
            totals["leaf"] += 0  # already incremented
            if detect_bitmap_leaf(node):
                totals["bitmap_leaves"] += 1
            scope_size = extract_scope_size(node)
            if scope_size is not None:
                leaf_scope_sizes.append(scope_size)

        max_depth = max(max_depth, depth)
        for child in children:
            queue.append((child, depth + 1))

    sum_weight_flat = [w for seq in sum_weights_stats for w in seq]
    sum_weight_info = {}
    if sum_weight_flat:
        sum_weight_info = {
            "count": len(sum_weight_flat),
            "min": min(sum_weight_flat),
            "max": max(sum_weight_flat),
            "avg": sum(sum_weight_flat) / len(sum_weight_flat),
        }

    branch_info = {}
    for depth, degrees in layer_branching.items():
        branch_info[depth] = {
            "min": min(degrees),
            "max": max(degrees),
            "avg": round(mean(degrees), 2),
        }

    scope_info = {}
    if leaf_scope_sizes:
        scope_info = {
            "min": min(leaf_scope_sizes),
            "max": max(leaf_scope_sizes),
            "avg": round(mean(leaf_scope_sizes), 2),
        }

    return {
        "totals": totals,
        "max_depth": max_depth,
        "sum_max_branch": sum_max_branch,
        "prod_max_branch": prod_max_branch,
        "layer_counts": layer_counts,
        "branch_info": branch_info,
        "snapshots": snapshots,
        "sum_weight_info": sum_weight_info,
        "scope_info": scope_info,
    }


def print_stats(index: int, root: Any, stats: dict[str, Any]) -> None:
    print(f"\n=== Component #{index} ({root.__class__.__name__}) ===")
    print(f"Total nodes: {stats['totals']['nodes']}")
    print(f"Max depth: {stats['max_depth']}")
    print(
        "Node breakdown: sum={sum}, product={product}, leaf={leaf}, other={internal}".format(
            **stats["totals"]
        )
    )
    print(
        f"Sum fan-out max: {stats['sum_max_branch']}, "
        f"Product fan-out max: {stats['prod_max_branch']}"
    )
    print(
        f"Leaf nodes with bitmap payload: {stats['totals']['bitmap_leaves']} / {stats['totals']['leaf']}"
    )
    if stats["scope_info"]:
        info = stats["scope_info"]
        print(
            f"Leaf scope size stats: min={info['min']}, max={info['max']}, avg={info['avg']}")
    if stats["sum_weight_info"]:
        info = stats["sum_weight_info"]
        print(
            "Sum weight stats: count={count}, min={min:.4f}, max={max:.4f}, avg={avg:.4f}".format(
                **info)
        )

    # --- NEW: Print one example bitmap leaf ---
    # if stats['totals']['bitmap_leaves'] > 0:
    if True:
        print("\n[Example Bitmap Leaf Data]")
        # We need to find one leaf with a bitmap. We can do a quick search again or store it during collection.
        # Since we don't want to re-traverse, let's just do a quick BFS here to find the first one.
        queue = deque([root])
        found = False
        visited = set()
        while queue:
            node = queue.popleft()
            if id(node) in visited:
                continue
            visited.add(id(node))

            children = extract_children(node)
            degree = len(children)
            kind = detect_kind(node, degree)

            if kind == "leaf" and detect_bitmap_leaf(node):
                print(f"Node Class: {node.__class__.__name__}")
                print(f"Scope: {extract_scope_str(node)}")

                # Try to print specific bitmap attributes
                attr = "unique_vals_ids"
                if hasattr(node, attr):
                    val = getattr(node, attr)
                    if val is not None:
                        print(f"Attribute '{attr}':")
                        if isinstance(val, dict):
                            # Likely unique_vals_ids dictionary
                            print(f"  Type: dict with {len(val)} keys")
                            # Print first few entries
                            for i, (k, v) in enumerate(val.items()):
                                if i >= 5:
                                    print("  ... (more entries)")
                                    break
                                # print(f"  Key: {k} -> Val: {v}")
                                # Visualize as bits (first 50)
                                try:
                                    limit = 50
                                    bits_str = "".join(
                                        ["1" if b in v else "0" for b in range(limit)])
                                    print(
                                        f"  Key: {k} -> Bits[0-{limit-1}]: {bits_str}...")
                                except TypeError:
                                    pass
                        elif hasattr(val, "tolist"):
                            # Tensor/Array
                            lst = val.tolist()
                            print(
                                f"  Type: Tensor/Array, Shape: {val.shape if hasattr(val, 'shape') else 'N/A'}")
                            print(f"  Data (first 20): {lst[:20]} ...")
                        elif isinstance(val, (list, tuple, set)):
                            # List/Set
                            lst = list(val)
                            print(
                                f"  Type: {type(val).__name__}, Length: {len(lst)}")
                            print(f"  Data (first 20): {lst[:20]} ...")
                        else:
                            # Other
                            print(f"  Value: {val}")
                found = True
                break

            for child in children:
                queue.append(child)

        if not found:
            print("  (Could not re-locate a bitmap leaf for printing)")
    # ------------------------------------------

    print("\nLayer summary:")
    for depth in sorted(stats["layer_counts"]):
        counts = stats["layer_counts"][depth]
        branch = stats["branch_info"].get(depth)
        branch_txt = ""
        if branch:
            branch_txt = f" | degree(avg={branch['avg']}, min={branch['min']}, max={branch['max']})"
        print(
            f"  L{depth:02d}: sum={counts.get('sum', 0)}, "
            f"product={counts.get('product', 0)}, "
            f"leaf={counts.get('leaf', 0)}, "
            f"other={counts.get('internal', 0)}{branch_txt}"
        )

    print("\nLayer snapshots:")
    for depth in sorted(stats["snapshots"]):
        line = "; ".join(stats["snapshots"][depth])
        print(f"  L{depth:02d}: {line}")
    if not stats["snapshots"]:
        print("  (no snapshots captured)")


# -------------------------------------------------------------------------
# EXPORT FUNCTIONALITY
# -------------------------------------------------------------------------

def extract_bitmap_str(node: Any) -> str:
    """Extracts bitmap data and converts it to a clean string format."""
    # Based on code analysis of rspn/structure/leaves.py and rspn/learning/rspn_learning.py
    # The attribute used to store bitmaps is 'unique_vals_ids'
    attr = "unique_vals_ids"
    if hasattr(node, attr):
        val = getattr(node, attr)
        if val is None:
            return "none"

        # C++ Readable Binary Hex Format
        # Format: [NumEntries:4][KeyType:1][Key:8][Count:4][Ids:4*Count]...
        if isinstance(val, dict):
            output = bytearray()
            output.extend(struct.pack('<I', len(val)))

            try:
                sorted_keys = sorted(val.keys())
            except Exception:
                sorted_keys = val.keys()

            for k in sorted_keys:
                # Key
                if isinstance(k, float):
                    output.extend(struct.pack('<B', 1))  # Type 1: float
                    output.extend(struct.pack('<d', k))
                elif isinstance(k, int):
                    output.extend(struct.pack('<B', 0))  # Type 0: int
                    output.extend(struct.pack('<q', k))  # int64
                else:
                    # Fallback/Unknown
                    output.extend(struct.pack('<B', 2))
                    output.extend(struct.pack('<q', 0))

                # Bitmap
                v = val[k]
                ids = []
                if hasattr(v, "tolist"):
                    ids = v.tolist()
                elif isinstance(v, (set, list, tuple)):
                    ids = list(v)
                else:
                    # Try to iterate (RoaringBitmap)
                    try:
                        ids = list(v)
                    except TypeError:
                        ids = [v]

                # Count
                output.extend(struct.pack('<I', len(ids)))
                # Ids
                if ids:
                    try:
                        # Try packing all at once
                        output.extend(struct.pack(
                            f'<{len(ids)}I', *[int(x) for x in ids]))
                    except Exception:
                        # Fallback: pack one by one
                        for x in ids:
                            output.extend(struct.pack('<I', int(x)))

            return f"hex:{output.hex()}"

        # Handle tensors or numpy arrays
        if hasattr(val, "tolist"):
            val = val.tolist()

        # Handle iterables (list, tuple, set, RoaringBitmap)
        ids = None
        if isinstance(val, (list, tuple, set)):
            ids = list(val)
        else:
            try:
                if not isinstance(val, (str, bytes)):
                    ids = list(val)
            except TypeError:
                pass

        if ids is not None:
            output = bytearray()
            output.extend(struct.pack('<I', len(ids)))
            if ids:
                try:
                    output.extend(struct.pack(
                        f'<{len(ids)}I', *[int(x) for x in ids]))
                except Exception:
                    for x in ids:
                        output.extend(struct.pack('<I', int(x)))
            return f"hexlist:{output.hex()}"

        return str(val)

    return "none"


def extract_scope_str(node: Any) -> str:
    for attr in ("scope", "scopes", "variables", "vars", "var_scope"):
        if hasattr(node, attr):
            scope = getattr(node, attr)
            if scope is None:
                continue
            if isinstance(scope, (list, tuple, set)):
                return ",".join(map(str, scope))
            if isinstance(scope, int):
                return str(scope)
    return "none"


def compress_list(lst: List[str], target: str = "none") -> str:
    """Compresses consecutive occurrences of `target` in the list."""
    result = []
    count = 0
    for item in lst:
        if item == target:
            count += 1
        else:
            if count > 0:
                result.append(f"{target}:{count}" if count > 1 else target)
                count = 0
            result.append(item)
    if count > 0:
        result.append(f"{target}:{count}" if count > 1 else target)
    return " ".join(result)


def ids_to_hex_bitmap(ids: Any, total_rows: int) -> str:
    """
    Converts a collection of row IDs into a hexadecimal string representation of a bit vector.
    The bit vector has length `total_rows`.
    The bit at index `i` is 1 if `i` is in `ids`, else 0.
    The output is a hex string (without '0x' prefix).
    """
    if total_rows <= 0:
        return "0"

    # Convert distinct IDs to a sorted list of integers
    if hasattr(ids, "tolist"):
        id_list = ids.tolist()
    elif isinstance(ids, (set, list, tuple)):
        id_list = list(ids)
    else:
        try:
            id_list = list(ids)
        except TypeError:
            id_list = [ids]
    
    # Use a large integer to represent the bitmap
    # We want bit 'i' to be the i-th bit from the *least significant bit* (LSB) or MSB?
    # Convention: usually bit 0 is LSB. Let's stick to standard integer representation.
    # bit `i` corresponds to value 2^i.
    
    bitmap_int = 0
    for i in id_list:
        if 0 <= i < total_rows:
             bitmap_int |= (1 << i)
    
    # Convert to hex. 
    # Determine the number of hex digits needed.
    # Each hex digit represents 4 bits.
    # total_rows bits require ceil(total_rows / 4) hex digits.
    # But Python's hex() produces variable length.
    # To make it consistent for C++ parsing (if it expects fixed size block or just big int parsing),
    # usually printing just hex(val) is fine, but padding might be safer if C++ reads fixed bytes.
    # Let's just output standard hex string.
    
    hex_str = hex(bitmap_int)[2:] # remove '0x'
    # Ensure even length for byte-alignment if needed, or expected length?
    # Let's just return the compact hex. C++ can parse hex string to big int or bitset.
    return hex_str


def serialize_bspn_component(root: Any, tree_id: int) -> List[str]:
    """
    Linearizes the SPN component into a node-per-line text format.
    Format per line: id=<id> type=<type> [attr=val ...]
    """
    # Get total cardinality from root for bitmap generation
    total_cardinality = int(getattr(root, "cardinality", 0))

    queue = deque([root])
    # Map object id to linear ID (0, 1, 2...)
    visited = {id(root): 0}
    nodes_list = [root]

    # 1. BFS to collect all nodes and assign IDs
    while queue:
        node = queue.popleft()
        children = extract_children(node)
        for child in children:
            if id(child) not in visited:
                visited[id(child)] = len(nodes_list)
                nodes_list.append(child)
                queue.append(child)

    # 2. Format output lines
    lines = []
    lines.append(f"Tree={tree_id}")
    lines.append(f"num_nodes={len(nodes_list)}")

    for idx, node in enumerate(nodes_list):
        node_type = type(node).__name__
        children = extract_children(node)
        child_ids = [visited[id(c)] for c in children]

        items = []
        items.append(f"id={idx}")
        items.append(f"type={node_type}")

        # Scope
        scope_str = extract_scope_str(node)
        # Remove spaces in scope string if any (e.g. "1, 2") -> "1,2"
        scope_str = scope_str.replace(" ", "")
        items.append(f"scope={scope_str}")

        # Cardinality
        if hasattr(node, "cardinality"):
            items.append(f"cardinality={node.cardinality}")

        # Children
        if child_ids:
            items.append(f"children={','.join(map(str, child_ids))}")

        # Weights (Sum)
        if node_type == "Sum" or hasattr(node, "weights"):
            w = extract_weights(node)
            if w:
                items.append(f"weights={','.join(map(str, w))}")

        # IdentityNumericLeaf
        if node_type == "IdentityNumericLeaf":
            # 改进后的区间-位图导出格式，方便 C++ 解析
            # 格式: intervals=start:end,start:end... bitmaps=id|id|...;id|id|...
            # 如果是单个值，start:end 其中 start=end
            
            if hasattr(node, "unique_vals_ids") and node.unique_vals_ids:
                intervals_str = []
                bitmaps_str = []
                
                # 按照 key 排序以保证确定性 (Tuple 排序: 先比第0个元素, 再比第1个...)
                try:
                    sorted_items = sorted(node.unique_vals_ids.items(), key=lambda x: x[0])
                except Exception:
                    # 如果排序失败（例如混合类型），尝试转字符串后排序或保持原样
                    sorted_items = node.unique_vals_ids.items()

                for k, v in sorted_items:
                    # 1. 处理区间 Key
                    if isinstance(k, (tuple, list)) and len(k) == 2:
                        # (start, end)
                        intervals_str.append(f"{k[0]}:{k[1]}")
                    else:
                        # 单个值视为 [val, val]
                        intervals_str.append(f"{k}:{k}")

                    # 2. 处理 Bitmap Value
                    ids = []
                    if hasattr(v, "tolist"):
                        ids = v.tolist()
                    elif isinstance(v, (set, list, tuple)):
                        ids = list(v)
                    else:
                        # Try to iterate (RoaringBitmap) or single value
                        try:
                            # Use list if it's iterable
                            ids_list = list(v)
                        except TypeError:
                            ids_list = [v]

                    if ids_list:
                        # Convert to string joined by |
                        # Example: 1|5|10
                        if hasattr(ids_list, "sort"):
                            ids_list.sort() # Ensure sorted order
                        else:
                            ids_list = sorted(list(ids_list))
                            
                        bitmaps_str.append("|".join(str(x) for x in ids_list))
                    else:
                        bitmaps_str.append("")

                items.append(f"intervals={','.join(intervals_str)}")
                items.append(f"bitmaps={';'.join(bitmaps_str)}")

        # Categorical
        if node_type == "Categorical":
            if hasattr(node, "p"):
                items.append(f"probabilities={','.join(map(str, node.p))}")

            if hasattr(node, "unique_vals_ids") and node.unique_vals_ids:
                sorted_keys = sorted(node.unique_vals_ids.keys())
                
                # 保持原有的 cat_values 输出，但也可以统一风格
                items.append(f"cat_values={','.join(map(str, sorted_keys))}")

                bitmaps_str = []
                for k in sorted_keys:
                    ids = node.unique_vals_ids[k]
                    
                    ids_list = []
                    if hasattr(ids, "tolist"):
                         ids_list = ids.tolist()
                    elif isinstance(ids, (set, list, tuple)):
                         ids_list = list(ids)
                    else:
                        try:
                            ids_list = list(ids)
                        except TypeError:
                            ids_list = [ids]
                    
                    if ids_list:
                         if hasattr(ids_list, "sort"):
                            ids_list.sort()
                         else:
                            ids_list = sorted(list(ids_list))
                         bitmaps_str.append("|".join(str(x) for x in ids_list))
                    else:
                         bitmaps_str.append("")
                
                # C++ 解析建议: cat_values 和 cat_bitmaps 通过索引一一对应
                items.append(f"cat_bitmaps={';'.join(bitmaps_str)}")

        lines.append(" ".join(items))

    return lines


def print_export_examples(export_lines: List[str]) -> None:
    """
    Parses the exported lines and prints examples of SUM, PRODUCT, and leaf nodes.
    Truncates long lists/bitmaps for readability.
    """
    example_sum = None
    example_prod = None
    example_leaf = None

    for line in export_lines:
        line = line.strip()
        if not line or line.startswith("Tree=") or line.startswith("num_nodes=") or line.startswith("model_type="):
            continue

        parts = line.split(" ")
        node_type = ""
        for part in parts:
            if part.startswith("type="):
                node_type = part.split("=")[1]
                break

        if node_type == "Sum" and example_sum is None:
            example_sum = line
        elif node_type == "Product" and example_prod is None:
            example_prod = line
        elif (node_type == "IdentityNumericLeaf" or node_type == "Categorical") and example_leaf is None:
            example_leaf = line
        
        if example_sum and example_prod and example_leaf:
            break
    
    print("\n[Export Examples]")
    
    def truncate_node_line(line_str: str, node_type: str = "") -> str:
        # Special handling for nodes to truncate long lists
        parts = line_str.split(" ")
        new_parts = []
        for part in parts:
            if part.startswith("id=") or part.startswith("type=") or part.startswith("scope=") or part.startswith("cardinality="):
                new_parts.append(part)
                continue
            
            if part.startswith("intervals="):
                prefix, content = part.split("=", 1)
                items = content.split(",")
                if len(items) > 5:
                    content = ",".join(items[:5]) + ",..."
                new_parts.append(f"{prefix}={content}")
            
            elif part.startswith("bitmaps=") or part.startswith("cat_bitmaps="):
                prefix, content = part.split("=", 1)
                items = content.split(";")
                trunc_items = []
                # Only take first 5 bitmaps
                limit = min(len(items), 5)
                for i in range(limit):
                    b = items[i]
                    # Keep first 3 and last 3 chars if long
                    if len(b) > 6:
                        trunc_items.append(b[:3] + "..." + b[-3:])
                    else:
                        trunc_items.append(b)
                if len(items) > 5:
                    trunc_items.append("...")
                new_parts.append(f"{prefix}={';'.join(trunc_items)}")
            
            elif part.startswith("cat_values="):
                 prefix, content = part.split("=", 1)
                 items = content.split(",")
                 if len(items) > 5:
                    content = ",".join(items[:5]) + ",..."
                 new_parts.append(f"{prefix}={content}")
            
            elif part.startswith("probabilities="):
                 prefix, content = part.split("=", 1)
                 items = content.split(",")
                 if len(items) > 5:
                    content = ",".join(items[:5]) + ",..."
                 new_parts.append(f"{prefix}={content}")
            
            elif part.startswith("weights=") or part.startswith("children="):
                 prefix, content = part.split("=", 1)
                 items = content.split(",")
                 if len(items) > 10:
                    content = ",".join(items[:10]) + f",...(+{len(items)-10})"
                 new_parts.append(f"{prefix}={content}")
            
            else:
                 # Generic truncation for unknown long fields
                 if len(part) > 50:
                      new_parts.append(part[:20] + "..." + part[-20:])
                 else:
                      new_parts.append(part)
        return " ".join(new_parts)


    print(f"\n[Export Examples]")
    if example_sum:
        # Re-parse type just in case
        print(f"SUM Node:     {truncate_node_line(example_sum)}")
    else:
        print("SUM Node:     (not found)")

    if example_prod:
        print(f"PRODUCT Node: {truncate_node_line(example_prod)}")
    else:
        print("PRODUCT Node: (not found)")

    if example_leaf:
         print(f"LEAF Node:    {truncate_node_line(example_leaf)}")
    else:
         print("LEAF Node:    (not found)")


def export_bspn_to_txt(roots: List[Any], filename: str):
    print(f"\nExporting {len(roots)} components to {filename}...")
    try:
        all_lines = []
        with open(filename, "w", encoding="utf-8") as f:
            f.write("model_type=BSPN_Full_Export\n")
            f.write(f"num_trees={len(roots)}\n")

            for idx, root in enumerate(roots):
                f.write("\n")
                lines = serialize_bspn_component(root, idx)
                f.write("\n".join(lines) + "\n")
                if len(all_lines) < 1000: # Only keep some lines for example printing
                     all_lines.extend(lines)
        
        print("Export successful.")
        print_export_examples(all_lines)

    except Exception as e:
        print(f"Error during export: {e}")
        import traceback
        traceback.print_exc()

# -------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect SPN ensemble structure from a pickle model."
    )
    parser.add_argument("model", 
                        help="Path to the .pkl model file.")
    parser.add_argument(
        "--snapshot-depth",
        type=int,
        default=3,
        help="How many layers to preview.",
    )
    parser.add_argument(
        "--snapshot-width",
        type=int,
        default=6,
        help="How many nodes per layer to show in the snapshot.",
    )
    parser.add_argument(
        "--export",
        type=str,
        default="",
        help="Path to export the BSPN structure to a text file (e.g., dump.txt).",
    )
    return parser.parse_args()


def _load_roots(model_path: str) -> tuple[List[Any], str]:
    # Prioritize direct pickle loading if read_ensemble is not available
    if read_ensemble:
        try:
            ensemble = read_ensemble(model_path, build_reverse_dict=False)
            roots: List[Any] = []
            for spn in getattr(ensemble, "spns", []) or []:
                root = getattr(spn, "mspn", spn)
                if root is not None:
                    roots.append(root)
            return roots, "SPNEnsemble"
        except Exception:
            pass  # Fallback to standard pickle load

    obj = load_pickle(model_path)
    roots = extract_roots(obj)
    return roots, f"pickle object ({type(obj).__name__})"


def inspect_all_node_types(roots: List[Any]) -> None:
    print("\n=== Inspecting Node Attributes by Type ===")
    seen_types = set()
    queue = deque(roots)
    visited = set()

    while queue:
        node = queue.popleft()
        if id(node) in visited:
            continue
        visited.add(id(node))

        node_type = type(node).__name__

        if node_type not in seen_types:
            seen_types.add(node_type)
            print(f"\n[Type: {node_type}]")
            print(f"  Class: {node.__class__}")

            if hasattr(node, "__dict__"):
                print("  Instance Attributes (vars):")
                for k, v in sorted(vars(node).items()):
                    val_str = str(v)
                    if len(val_str) > 200:
                        val_str = val_str[:200] + "..."
                    print(f"    {k}: {type(v).__name__} = {val_str}")

            if hasattr(node, "__slots__"):
                print(f"  Slots: {node.__slots__}")
                for slot in node.__slots__:
                    if hasattr(node, slot):
                        val = getattr(node, slot)
                        val_str = str(val)
                        if len(val_str) > 200:
                            val_str = val_str[:200] + "..."
                        print(f"    {slot}: {type(val).__name__} = {val_str}")

        children = extract_children(node)
        for child in children:
            queue.append(child)


def main() -> None:
    args = parse_args()
    roots, origin = _load_roots(args.model)
    if not roots:
        raise RuntimeError("No SPN roots found in the provided model.")
    print(f"Loaded from {origin}, components detected: {len(roots)}")

    # 1. Print Statistics
    for idx, root in enumerate(roots, start=0):
        stats = collect_spn_stats(
            root, args.snapshot_depth, args.snapshot_width)
        print_stats(idx, root, stats)

    # 2. Export if requested
    if args.export:
        export_bspn_to_txt(roots, args.export)

    # inspect_all_node_types(roots)


if __name__ == "__main__":
    main()

