from __future__ import annotations

import pandas as pd
import phik

from src.processing.constants import CATEGORY_THRESHOLD, ColumnType

class BaseProcessor:
    """Базовый класс с общими методами для работы с DataFrame."""

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df

    def remove_outliers_by_bounds(
        self,
        column: str,
        left: str | float | None = None,
        right: str | float | None = None,
        inclusive: bool | tuple[bool, bool] = True,
    ) -> "BaseProcessor":
        """Удаляет строки, где column выходит за пределы [left, right].

        Args:
            column: Имя колонки.
            left: Нижняя граница: число, 'q01'..'q99' или None.
            right: Верхняя граница: число, 'q01'..'q99' или None.
            inclusive: True — обе границы включены, False — обе исключены,
                (left_inc, right_inc) — по отдельности.
        """
        if left is None and right is None:
            raise ValueError("Укажите хотя бы один порог: left или right.")
        if column not in self.df.columns:
            raise ValueError(f"Колонка '{column}' не найдена.")

        if isinstance(inclusive, tuple):
            inc_left, inc_right = inclusive
        else:
            inc_left = inc_right = inclusive

        col = self.df[column]
        lo = self._resolve_bound(col, left)
        hi = self._resolve_bound(col, right)

        mask = col.notna()
        if lo is not None:
            mask &= col >= lo if inc_left else col > lo
        if hi is not None:
            mask &= col <= hi if inc_right else col < hi

        before = len(self.df)
        self.df = self.df[mask]
        removed = before - len(self.df)

        lo_s = f"{'[' if inc_left else '('}{lo}" if lo is not None else "(-∞"
        hi_s = f"{hi}{']' if inc_right else ')'}" if hi is not None else "+∞)"
        print(
            f"\nУдаление выбросов в столбце {column}: {lo_s}, {hi_s}"
            f": {removed} из {before}"
        )
        return self

    def _resolve_bound(self, series: pd.Series, value: str | float | None) -> float | None:
        """Превращает границу в число.

        Поддерживает:
        * None         → None (граница не задана)
        * число        → float
        * "q01".."q99" → квантиль колонки series
        * "Q50"        → то же самое (регистр не важен)
        * пробелы вокруг → игнорируются

        Args:
            series: колонка, по которой считаем квантиль.
            value: граница из аргументов метода.

        Returns:
            float или None.
        """
        if value is None:
            return None

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)

        if isinstance(value, str):
            s = value.strip().lower()
            if s.startswith("q"):
                try:
                    q = float(s[1:]) / 100.0
                except ValueError:
                    q = -1.0
                if 0.0 <= q <= 1.0:
                    return float(series.quantile(q))

        raise ValueError(
            f"Некорректная граница: {value!r}. "
            f"Ожидается число или строка вида 'q01'..'q99'."
        )


    def drop_duplicates(
        self,
        subset: str | list[str] | None = None,
        keep: str | bool = "first",
        ignore_index: bool = False,
    ) -> "BaseProcessor":
        """Удаляет дубликаты строк, как pd.DataFrame.drop_duplicates.

        Args:
            subset: Столбец или список столбцов для проверки дубликатов.
            keep: {'first', 'last', False}.
            ignore_index: Если True, нумерация строк сбрасывается на 0..N-1.
        """
        before = len(self.df)

        self.df = self.df.drop_duplicates(
            subset=subset,
            keep=keep,
            ignore_index=ignore_index,
        )

        removed = before - len(self.df)
        pct = f"{removed / before:.1%}" if before else "n/a"

        print(
            f"\nУдаление дубликатов: \n[subset={subset!r}, keep={keep!r}, ignore_index={ignore_index}]"
            f"\nУдалено {removed} дубликатов ({pct})"
        )

        return self

    def optimize_dtypes(
        self,
        columns: dict,
        threshold: float = CATEGORY_THRESHOLD,
    ) -> "BaseProcessor":
        """Оптимизирует типы колонок.

        Args:
            columns: Справочник {col_name: ColumnType}.
            threshold: Порог уникальных значений для category.
        """
        before = self.df.memory_usage(deep=True).sum() / 1024**2
        print("\nОптимизация типов")
        print(f"Объем занимаемой памяти: \n\t- до оптимизации {before:.1f} МБ")

        for col, col_type in columns.items():
            if col not in self.df.columns:
                continue

            if col_type == ColumnType.INT:
                self.df[col] = pd.to_numeric(self.df[col], downcast="integer")
            elif col_type == ColumnType.FLOAT:
                self.df[col] = pd.to_numeric(self.df[col], downcast="float")
            elif col_type == ColumnType.CATEGORY:
                if self.df[col].nunique() < len(self.df) * threshold:
                    self.df[col] = self.df[col].astype("category")
            elif col_type == ColumnType.DATETIME:
                self.df[col] = pd.to_datetime(self.df[col])

        after = self.df.memory_usage(deep=True).sum() / 1024**2
        print(f"\t- после оптимизации {after:.1f} МБ")
        return self

    def create_segment_column(
        self,
        column: str,
        segments: list[tuple[float | None, float | None, str]],
        new_column: str | None = None,
    ) -> "BaseProcessor":
        """Создаёт категориальную колонку по числовой.

        Args:
            column: числовая колонка-источник.
            segments: [(lo, hi, label), ...] — границы включительно, None = открыто.
                Сегменты проверяются по порядку; побеждает первое совпадение,
                поэтому пересечения не перезаписывают друг друга.
            new_column: имя новой колонки (по умолчанию f"{column}_segment").

        Example:
            df.create_segment_column(
                "total_orders",
                segments=[
                    (1, 1, "1 заказ"),
                    (2, 2, "2 заказа"),
                    (3, 4, "от 3 до 4 заказов"),
                    (5, None, "от 5 и выше"),
                ],
            )
        """
        if column not in self.df.columns:
            raise ValueError(f"Колонка '{column}' не найдена.")
        if not segments:
            raise ValueError("segments пуст.")

        new_column = new_column or f"{column}_segment"
        values = self.df[column]
        result = pd.Series(pd.NA, index=self.df.index, dtype="object")

        for lo, hi, label in segments:
            mask = values.notna() & result.isna()     # только ещё не размеченные
            if lo is not None:
                mask &= values >= lo
            if hi is not None:
                mask &= values <= hi
            result[mask] = label

        self.df[new_column] = result

        total = len(result)
        counts = result.value_counts(dropna=False)
        print(f"\nСегменты по '{column}' → '{new_column}' (всего {total}):")
        for label, cnt in counts.items():
            name = label if pd.notna(label) else "NaN"
            print(f"  {name}: {cnt} ({cnt / total:.1%})")

        unmatched = result.isna() & values.notna()
        if unmatched.any():
            print(f"  ⚠ не попали ни в один сегмент: {int(unmatched.sum())}")

        return self

    def segment_stats(
        self,
        column: str,
        top_n: int | None = None,
        other_name: str = "Остальные",
        agg: dict[str, str | list[str]] | None = None,
    ) -> pd.DataFrame:
        if column not in self.df.columns:
            raise ValueError(f"Колонка '{column}' не найдена.")
        if self.df.empty:
            return pd.DataFrame(columns=["segment", "count", "share"])

        seg = self.df[column].astype("string").fillna("<NA>")

        if top_n is not None:
            top = seg.value_counts().head(top_n).index
            in_top = seg.isin(top)
            seg = seg.where(in_top, other_name)

            if other_name in set(top):
                print(f"⚠ other_name={other_name!r} входит в топ-{top_n}")

        total = len(seg)
        result = (
            seg.value_counts(dropna=False)
            .rename_axis("segment")
            .reset_index(name="count")
        )
        result["share"] = (result["count"] / total).round(4)

        if agg:
            valid = {c: f for c, f in agg.items() if c in self.df.columns}
            if valid:
                prepared = self.df[list(valid)].copy()
                for c in prepared.columns:
                    num = pd.to_numeric(prepared[c], errors="coerce")
                    if num.notna().any():
                        prepared[c] = num

                grouped = prepared.assign(_segment=seg).groupby("_segment").agg(valid)
                grouped.columns = [
                    "_".join(str(x) for x in c if x) if isinstance(c, tuple) else str(c)
                    for c in grouped.columns
                ]
                grouped = grouped.reset_index().rename(columns={"_segment": "segment"})
                result = result.merge(grouped, on="segment", how="left")

        result = result.sort_values("count", ascending=False).set_index("segment")

        if top_n is not None:
            mask = result.index == other_name
            if mask.any():
                result = pd.concat([result[~mask], result[mask]])

        print(f"\nСегменты по '{column}': {len(result)} групп")
        return result

    def phik_matrix(
        self,
        columns: list[str] | None = None,
        interval_cols: list[str] | None = None,
    ) -> pd.DataFrame:
        """Строит матрицу корреляций Phik (Phik correlation matrix).

        Phik корректно работает со смешанными типами: числовые ↔ категориальные,
        категориальные ↔ категориальные. Для числовых колонок нужно указать
        interval_cols — иначе Phik обработает их как категориальные (медленно и
        с потерей смысла).

        Args:
            columns: Колонки для матрицы. None — все колонки self.df.
            interval_cols: Числовые (непрерывные) колонки среди columns.

        Returns:
            Квадратный DataFrame — матрица корреляций Phik.
        """

        cols = list(columns) if columns is not None else list(self.df.columns)

        missing = [c for c in cols if c not in self.df.columns]
        if missing:
            raise ValueError(f"Колонки не найдены: {missing}")

        if len(cols) < 2:
            raise ValueError("Нужно минимум 2 колонки для матрицы корреляций.")

        interval = list(interval_cols) if interval_cols is not None else []
        bad_interval = [c for c in interval if c not in cols]
        if bad_interval:
            raise ValueError(
                f"interval_cols должны быть среди columns. Лишние: {bad_interval}"
            )

        data = self.df[cols]
        matrix = data.phik_matrix(interval_cols=interval)

        print(
            f"\nPhik-матрица: {matrix.shape[0]}×{matrix.shape[1]} колонок, "
            f"interval_cols={interval or '—'}"
        )
        return matrix
