from __future__ import annotations


class Report:
    """Формирует текстовое резюме по результатам анализа лояльности."""

    SEPARATOR = "=" * 60

    def __init__(
        self,
        total_users: int,
        repeat_users: int,
        one_time_users: int,
        concert_rate: float,
        sport_rate: float,
        region_rho: float,
        region_p: float,
        mobile_share: float,
        mobile_repeat: float,
        desktop_repeat: float,
        top_region: str,
        top_region_share: float,
        one_time_median: float,
        repeat_median: float,
        phik_top_links: list[tuple[str, str, float]],
    ) -> None:
        self.total_users = total_users
        self.repeat_users = repeat_users
        self.one_time_users = one_time_users
        self.concert_rate = concert_rate
        self.sport_rate = sport_rate
        self.region_rho = region_rho
        self.region_p = region_p
        self.mobile_share = mobile_share
        self.mobile_repeat = mobile_repeat
        self.desktop_repeat = desktop_repeat
        self.top_region = top_region
        self.top_region_share = top_region_share
        self.one_time_median = one_time_median
        self.repeat_median = repeat_median
        self.phik_top_links = phik_top_links

    @property
    def repeat_rate(self) -> float:
        return self.repeat_users / self.total_users

    @property
    def one_time_share(self) -> float:
        return self.one_time_users / self.total_users

    def generate(self) -> str:
        lines: list[str] = []
        lines.append(self.SEPARATOR)
        lines.append("РЕЗЮМЕ АНАЛИЗА ЛОЯЛЬНОСТИ")
        lines.append(self.SEPARATOR)

        lines.append("")
        lines.append(f"📊 Масштаб: {self.total_users:,} пользователей, "
                      f"{self.repeat_rate:.1%} — повторные покупки")

        lines.append("")
        lines.append("1. Удержание (churn risk)")
        lines.append(f"   • {self.one_time_users:,} ({self.one_time_share:.1%}) — разовые покупатели")
        lines.append(f"   • {self.repeat_users:,} ({self.repeat_rate:.1%}) — повторные покупки")
        lines.append(f"   → Зона риска: {self.one_time_share:.0%} пользователей уходят после первой покупки")

        lines.append("")
        lines.append("2. Гипотеза 1: спорт vs концерты (первый заказ → повторная покупка)")
        lines.append(f"   • Концерты: {self.concert_rate:.1%}, Спорт: {self.sport_rate:.1%}")
        diff = self.sport_rate - self.concert_rate
        lines.append(f"   • Разница: {diff:+.1%}")
        if diff > 0:
            lines.append("   → ГИПОТЕЗА НЕ ПОДТВЕРЖДЕНА: первый заказ на концерты ассоциирован с более высокой долей повторных покупок")
        else:
            lines.append("   → ГИПОТЕЗА НЕ ПОДТВЕРЖДЕНА: первый заказ на спорт не даёт преимущества в повторных покупках")

        lines.append("")
        lines.append("3. Гипотеза 2: активность региона ↔ доля повторных покупок")
        lines.append(f"   • Спирмен: rho = {self.region_rho:.3f}, p-value = {self.region_p:.4f}")
        lines.append("   → ГИПОТЕЗА НЕ ПОДТВЕРЖДЕНА: связи между числом пользователей в регионе и долей повторных покупок нет")

        lines.append("")
        lines.append("4. Удержание по устройству первого заказа")
        lines.append(f"   • Мобильные: {self.mobile_share:.1%} пользователей, повторные — {self.mobile_repeat:.1%}")
        lines.append(f"   • Десктоп:   {(1 - self.mobile_share):.1%} пользователей, повторные — {self.desktop_repeat:.1%}")
        lines.append("   → Разница в поведении между устройствами минимальна")

        lines.append("")
        lines.append("5. Выручка: повторные vs разовые")
        lines.append(f"   • Медиана повторных: {self.repeat_median:.0f} ₽ vs разовых: {self.one_time_median:.0f} ₽")
        lines.append("   → Повторные покупатели имеют более высокую медианную выручку, но разброс очень большой")

        lines.append("")
        lines.append("6. Сильнейшие связи (Phik)")
        for a, b, val in self.phik_top_links:
            lines.append(f"   • {a} ↔ {b}: {val:.2f}")

        lines.append("")
        lines.append("💡 Рекомендации")
        lines.append("   1. Запуск программы удержания разовых покупателей (скидки, push-напоминания)")
        lines.append(f"   2. Приоритет мобильному UX — {self.mobile_share:.0%} пользователей начинают с мобильных")
        lines.append(f"   3. Регионально-адаптивный маркетинг: топ-регионы ({self.top_region}, {self.top_region_share:.0%} базы) — удержание, остальные — рост")
        lines.append("   4. Концерты как драйвер лояльности — усиливать предложение и персонализацию")
        lines.append(self.SEPARATOR)

        return "\n".join(lines)
