import logging

from user_agents import parse

logger = logging.getLogger(__name__)


class UAmiddleware(object):
    """mobile判定をrequestに追加する。
    https://studylog.hateblo.jp/entry/2014/02/10/061003
    https://docs.djangoproject.com/ja/4.0/topics/http/middleware/#activating-middleware
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 前処理
        # self.process_request(request)
        # ビューの処理
        response = self.get_response(request)
        # 後処理
        # self.process_response(request, response)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """mobile判定"""
        request.user_agent_flag = UAmiddleware.user_agent_check(request)
        return None

    def user_agent_check(request):
        try:
            ua_string = request.META["HTTP_USER_AGENT"]
            user_agent = parse(ua_string)
            if user_agent.is_mobile:
                return "mobile"
            else:
                return ""
        except KeyError:
            logger.warning("HTTP_USER_AGENTが設定されていないアクセス")
            return ""
