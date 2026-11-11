# HJJ: 博客搜索表单模块，基于Haystack框架扩展搜索功能，
# HJJ: 提供搜索关键词校验和日志记录功能

import logging

from django import forms
from haystack.forms import SearchForm

logger = logging.getLogger(__name__)


class BlogSearchForm(SearchForm):
    # HJJ: 自定义搜索表单，强制要求搜索关键词不能为空
    querydata = forms.CharField(required=True)

    def search(self):
        """
        HJJ: 重写搜索方法，在父类搜索基础上增加关键词日志记录
        参数: 无
        返回: SearchQuerySet | None - 搜索结果集，无效查询时返回空结果
        """
        # HJJ: 调用父类的search方法执行实际搜索逻辑
        datas = super(BlogSearchForm, self).search()
        
        # HJJ: 校验表单有效性，无效则返回空查询结果
        if not self.is_valid():
            return self.no_query_found()

        # HJJ: 记录用户搜索的关键词到日志，便于分析搜索热词
        if self.cleaned_data['querydata']:
            logger.info(self.cleaned_data['querydata'])
            
        return datas