from __future__ import annotations

from enum import Enum


class ColumnType(Enum):
    INT = "int"
    FLOAT = "float"
    CATEGORY = "category"
    DATETIME = "datetime"
    OBJECT = "object"


DB_COLUMNS: dict[str, ColumnType] = {
    "user_id": ColumnType.OBJECT,
    "order_id": ColumnType.INT,
    "event_id": ColumnType.INT,
    "tickets_count": ColumnType.INT,
    "created_dt_msk": ColumnType.DATETIME,
    "created_ts_msk": ColumnType.DATETIME,
    "currency_code": ColumnType.CATEGORY,
    "revenue": ColumnType.FLOAT,
    "device_type_canonical": ColumnType.CATEGORY,
    "event_type_main": ColumnType.CATEGORY,
    "service_name": ColumnType.CATEGORY,
    "region_name": ColumnType.CATEGORY,
    "days_since_prev": ColumnType.FLOAT,
}

COMPUTED_COLUMNS: dict[str, ColumnType] = {
    "revenue_rub": ColumnType.FLOAT,
}

CATEGORY_THRESHOLD = 0.5
