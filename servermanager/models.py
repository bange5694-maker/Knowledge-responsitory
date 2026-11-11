# LZH: 模块功能：定义 servermanager 应用的两个数据模型——
# LZH: commands（微信命令配置表）与 EmailSendLog（邮件发送日志表）。

from django.db import models


# Create your models here.

# LZH: 命令模型：保存微信机器人可执行的命令标题、命令内容与描述，供管理后台维护。
class commands(models.Model):
    # LZH: 字段说明：命令标题，作为命令的展示名，最大长度 300。
    title = models.CharField('命令标题', max_length=300)
    # LZH: 字段说明：实际执行的命令内容（如 shell 命令），最大长度 2000。
    command = models.CharField('命令', max_length=2000)
    # LZH: 字段说明：命令用途说明，在 helpme 帮助信息中展示。
    describe = models.CharField('命令描述', max_length=300)
    # LZH: 字段说明：记录创建时间，首次保存时自动写入，之后不再修改。
    creation_time = models.DateTimeField('创建时间', auto_now_add=True)
    # LZH: 字段说明：记录最后修改时间，每次 save() 时自动刷新。
    last_modify_time = models.DateTimeField('修改时间', auto_now=True)

    # LZH: 方法说明：对象的字符串表示，后台与日志中直接显示命令标题。
    # LZH: 参数：无；返回：str，命令标题；异常：无。
    def __str__(self):
        return self.title

    # LZH: 元数据说明：设置后台与表单中显示的中文名称。
    class Meta:
        verbose_name = '命令'
        verbose_name_plural = verbose_name


# LZH: 邮件发送日志模型：记录每次通过系统发出的邮件（收件人、标题、正文、结果），用于排错与审计。
class EmailSendLog(models.Model):
    # LZH: 字段说明：收件人邮箱地址，最大长度 300。
    emailto = models.CharField('收件人', max_length=300)
    # LZH: 字段说明：邮件标题，最大长度 2000。
    title = models.CharField('邮件标题', max_length=2000)
    # LZH: 字段说明：邮件正文，使用 TextField 以支持长文本。
    content = models.TextField('邮件内容')
    # LZH: 字段说明：发送结果标记，True 表示发送成功，默认 False 表示失败或未发送。
    send_result = models.BooleanField('结果', default=False)
    # LZH: 字段说明：日志创建时间，首次保存时自动写入。
    creation_time = models.DateTimeField('创建时间', auto_now_add=True)

    # LZH: 方法说明：对象字符串表示，返回邮件标题，便于后台列表识别。
    # LZH: 参数：无；返回：str，邮件标题；异常：无。
    def __str__(self):
        return self.title

    # LZH: 元数据说明：设置中文名称，并按创建时间倒序排列（最新的日志在最前）。
    class Meta:
        verbose_name = '邮件发送log'
        verbose_name_plural = verbose_name
        ordering = ['-creation_time']
