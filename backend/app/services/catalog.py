"""Static catalog exposed to the frontend (no hardcoded labels on the client)."""

from __future__ import annotations

from ..data.universe import (
    BENCHMARK,
    GROUP_META,
    GROUPS,
    INDICES,
    RANGE_META,
)


def get_catalog() -> dict:
    groups = []
    for meta in GROUP_META:
        groups.append(
            {
                **meta,
                "items": GROUPS.get(meta["key"], []),
            }
        )
    return {
        "groups": groups,
        "ranges": RANGE_META,
        "benchmark": BENCHMARK,
        "indices": [
            {"symbol": i["symbol"], "label": i["label"], "kind": i["kind"]}
            for i in INDICES
        ],
        "disclaimer": (
            "ข้อมูลหน่วงจากผู้ให้บริการฟรี ตัวเลขกระแสเงินเป็นประมาณการจากราคาและมูลค่าซื้อขาย "
            "ไม่ใช่ข้อมูล fund flow จริง และไม่ใช่คำแนะนำการลงทุน"
        ),
    }
