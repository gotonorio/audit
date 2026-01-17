import logging

from common.mixins import PeriodParamMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from budget.forms import Budget_listForm
from budget.services import get_budget_vs_actual

logger = logging.getLogger(__name__)


class BudgetListView(PeriodParamMixin, LoginRequiredMixin, TemplateView):
    """会計支出の予算・実績対比表
    - PeriodParamMixinを継承してget_year_month_params()を呼び出す。
    """

    template_name = "budget/budget_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1. パラメータの取得 (Mixin & GET)
        year, month = self.get_year_month_params()
        ac_class = int(self.request.GET.get("ac_class") or 1)
        kind = int(self.request.GET.get("kind") or 0)

        # 2. Service層での重い計算処理
        report = get_budget_vs_actual(year, month, ac_class, kind)

        logger.debug(report["unbudgeted_list"])

        # 3. フォームの初期化
        form = Budget_listForm(
            initial={
                "year": year,
                "month": month,
                "ac_class": ac_class,
                "kind": kind,
            }
        )

        # 4. コンテキストへの詰め込み
        context.update(
            {
                "title": report["ac_class_name"],
                "form": form,
                "month": report["latest_month"],
                "expense_budget": report["comparison_list"],
                "total_budget": report["total_budget"],
                "total_ruiseki": report["total_actual"],
                "check_budget": report["unbudgeted_list"],
            }
        )
        return context
