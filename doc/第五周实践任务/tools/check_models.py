# -*- coding: utf-8 -*-
"""把 model_data.py 与 Django 的真实 model 逐项对比。

校验内容：
1. 每个实体/中间表的 db_table 是否一致；
2. 数据库列名（FK 用 attname，如 author_id）是否齐全、有没有多余列；
3. 列类型是否与 Django 5.2 + MySQL 的映射一致。

在仓库根目录执行：
    .venv/Scripts/python.exe doc/第五周实践任务/tools/check_models.py
"""
import logging
import os
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(TOOLS))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoblog.settings")
import django  # noqa: E402

logging.disable(logging.CRITICAL)
django.setup()

from django.apps import apps  # noqa: E402

from model_data import ENTITIES  # noqa: E402


def expected_type(field):
    it = field.get_internal_type()
    if it == "AutoField":
        return "int"
    if it == "BigAutoField":
        return "bigint"
    if it in ("CharField", "SlugField", "URLField"):
        return f"varchar({field.max_length})"
    if it == "TextField":
        return "longtext"
    if it == "DateTimeField":
        return "datetime(6)"
    if it == "BooleanField":
        return "tinyint(1)"
    if it == "IntegerField":
        return "int"
    if it == "PositiveIntegerField":
        return "int unsigned"
    if it == "JSONField":
        return "json"
    if field.is_relation:
        pk = field.target_field
        return "bigint" if pk.get_internal_type() == "BigAutoField" else "int"
    return "?" + it


def get_model(key, entity):
    if key == "Session":
        return apps.get_model("sessions", "Session")
    if entity["model"] is None:
        article = apps.get_model("blog", "Article")
        return article._meta.get_field("tags").remote_field.through
    return apps.get_model(entity["app"], entity["model"])


def main():
    problems = []
    for key, entity in ENTITIES.items():
        model = get_model(key, entity)
        if model._meta.db_table != entity["table"]:
            problems.append(f"{key}: db_table={model._meta.db_table}，应为 {entity['table']}")

        ours = {f[0]: f for f in entity["fields"]}
        actual = [f.attname for f in model._meta.concrete_fields]
        for col in actual:
            if col not in ours:
                problems.append(f"{key}: 缺少列 {col}")
                continue
            exp = expected_type(next(f for f in model._meta.concrete_fields if f.attname == col))
            got = ours[col][2]
            if exp != got:
                problems.append(f"{key}.{col}: 类型写的是 {got}，实际应为 {exp}")
        for col in ours:
            if col not in actual:
                problems.append(f"{key}: 多出列 {col}")

    if problems:
        print(f"FAIL：发现 {len(problems)} 处不一致")
        for p in problems:
            print(" -", p)
        return 1

    print(f"OK：{len(ENTITIES)} 个实体/中间表的表名、列名、列类型全部一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
