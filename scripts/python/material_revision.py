from __future__ import annotations

"""材料资产的统一版本和来源标识计算。"""

import hashlib
import json
from pathlib import Path
from typing import Iterable, Mapping


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash_object(value: object) -> str:
    return sha256_text(_canonical(value))


def file_digest(path: Path) -> str:
    """按材料索引的文本读取规则计算来源文件哈希。"""
    return sha256_text(path.read_text(encoding="utf-8-sig"))


def normalized_source_path(value: str) -> str:
    """把材料路径规范为与 source-index 相同的项目内 POSIX 路径。"""
    return Path(value).as_posix()


def source_id_for(value: str) -> str:
    """根据规范化的材料相对路径生成稳定来源 ID。"""
    return sha256_text(normalized_source_path(value))[:16]


def canonical_sources(sources: Iterable[Mapping[str, object]]) -> list[dict[str, str]]:
    """提取并排序参与版本计算的来源元数据。"""
    result = []
    for item in sources:
        path = normalized_source_path(str(item["path"]))
        result.append({
            "source_id": str(item.get("source_id") or source_id_for(path)),
            "path": path,
            "sha256": str(item["sha256"]),
        })
    return sorted(result, key=lambda item: item["path"])


def material_revision(sources: Iterable[Mapping[str, object]]) -> str:
    """计算统一格式的材料版本。格式固定为 sha256:<64位十六进制>。"""
    return f"sha256:{_hash_object(canonical_sources(sources))}"
