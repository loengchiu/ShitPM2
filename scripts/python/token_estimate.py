from __future__ import annotations

"""统一的上下文体量估算；仅用于预算和门禁，不替代目标模型 tokenizer。"""


def estimate_tokens(text: str) -> int:
    cjk = sum(
        1
        for char in text
        if (
            '\u3400' <= char <= '\u4dbf'
            or '\u4e00' <= char <= '\u9fff'
            or '\uf900' <= char <= '\ufaff'
            or '\u3040' <= char <= '\u30ff'
            or '\uac00' <= char <= '\ud7af'
        )
    )
    return max(1, int(cjk * 0.6 + (len(text) - cjk) * 0.25 + 0.999999)) if text else 0
