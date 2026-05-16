
from __future__ import annotations
import argparse
import os
import pickle
import sys
from typing import Any, List

# 基础路径设置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# 尝试导入 ensemble
try:
    from ensemble_compilation.spn_ensemble import read_ensemble
except ImportError:
    read_ensemble = None

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

def write_line(file_handle, text: str):
    """同时输出到控制台和文件"""
    print(text)
    if file_handle:
        file_handle.write(text + "\n")

def print_spn_tree(node: Any, file_handle, prefix: str = "", is_last: bool = True):
    """
    递归打印树结构
    """
    node_cls_name = node.__class__.__name__
    
    if "Sum" in node_cls_name:
        node_type = "TYPE_SUM"
    elif "Product" in node_cls_name or "Prod" in node_cls_name:
        node_type = "TYPE_PROD"
    # elif "Leaf" in node_cls_name or "Categorical" in node_cls_name:
    #     node_type = "TYPE_LEAF"
    else:
        # node_type = f"UNKNOWN({node_cls_name})"
        return

    cardinality = getattr(node, "cardinality", "N/A")
    scope = getattr(node, "scope", "N/A")

    connector = "└── " if is_last else "├── "
    info_str = f"Type: {node_type}, Rows: {cardinality}, Scope: {scope}"
    
    # 输出当前节点
    write_line(file_handle, f"{prefix}{connector}{info_str}")

    children = getattr(node, "children", [])
    
    if children:
        new_prefix = prefix + ("    " if is_last else "│   ")
        count = len(children)
        for i, child in enumerate(children):
            is_last_child = (i == count - 1)
            print_spn_tree(child, file_handle, prefix=new_prefix, is_last=is_last_child)

def main() -> None:
    parser = argparse.ArgumentParser(description="Print SPN tree structure to file.")
    parser.add_argument("model", help="Path to the .pkl model file.")
    parser.add_argument("--output", default="out.txt", help="Output file path (default: out.txt)")
    args = parser.parse_args()

    print(f"Loading model from {args.model}...")
    
    roots = []
    if read_ensemble:
        try:
            ensemble = read_ensemble(args.model, build_reverse_dict=False)
            for spn in getattr(ensemble, "spns", []) or []:
                root = getattr(spn, "mspn", spn)
                if root:
                    roots.append(root)
        except Exception:
            pass

    if not roots:
        obj = load_pickle(args.model)
        roots = extract_roots(obj)

    if not roots:
        raise RuntimeError("No SPN roots found in the provided model.")

    print(f"Found {len(roots)} root node(s). Writing to {args.output}...\n")

    # 打开文件准备写入
    with open(args.output, "w", encoding="utf-8") as f:
        for idx, root in enumerate(roots):
            header = f"--- Tree #{idx} ---"
            write_line(f, header)
            print_spn_tree(root, file_handle=f, prefix="", is_last=True)
            write_line(f, "") # 空行分隔

    print(f"Done! Result saved to {args.output}")

if __name__ == "__main__":
    main()