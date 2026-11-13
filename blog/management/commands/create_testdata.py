# HJJ: Django管理命令 - 创建测试数据
# 通过 python manage.py create_testdata 执行
# 生成测试用户、分类、标签和文章，用于开发和测试环境

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from blog.models import Article, Tag, Category


class Command(BaseCommand):
    # HJJ: 命令帮助信息
    help = 'create test datas'

    def handle(self, *args, **options):
        """
        HJJ: 命令入口方法
        
        执行流程：
        1. 创建测试用户（邮箱/用户名/密码）
        2. 创建父级分类和子级分类
        3. 创建基础标签
        4. 循环创建19篇测试文章，每篇附带唯一标签
        5. 清空缓存使新数据生效
        
        参数:
            *args: 位置参数（暂未使用）
            **options: 关键字参数（暂未使用）
        返回:
            无
        """
        # HJJ: 创建或获取测试用户
        user = get_user_model().objects.get_or_create(
            email='test@test.com', 
            username='测试用户', 
            password=make_password('test!q@w#eTYU')
        )[0]

        # HJJ: 创建父级分类
        pcategory = Category.objects.get_or_create(
            name='我是父类目', 
            parent_category=None
        )[0]

        # HJJ: 创建子级分类（挂载到父分类下）
        category = Category.objects.get_or_create(
            name='子类目', 
            parent_category=pcategory
        )[0]

        category.save()
        
        # HJJ: 创建基础标签（所有文章共享）
        basetag = Tag()
        basetag.name = "标签"
        basetag.save()
        
        # HJJ: 循环创建19篇测试文章
        for i in range(1, 20):
            article = Article.objects.get_or_create(
                category=category,
                title='nice title ' + str(i),
                body='nice content ' + str(i),
                author=user
            )[0]
            
            # HJJ: 为每篇文章创建唯一标签
            tag = Tag()
            tag.name = "标签" + str(i)
            tag.save()
            
            # HJJ: 添加两个标签（唯一标签+基础标签）
            article.tags.add(tag)
            article.tags.add(basetag)
            article.save()

        # HJJ: 清空缓存，确保新创建的测试数据能立即被前端访问
        from djangoblog.utils import cache
        cache.clear()
        
        # HJJ: 输出绿色成功提示
        self.stdout.write(self.style.SUCCESS('created test datas \n'))