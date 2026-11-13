# 第 3 章素材 · accounts（朱宇豪）

> 用途：报告第 3 章「人工分析代码的质量情况」中 accounts 部分的素材，交给何君杰汇总。
> 范围：accounts 10 个业务文件、546 行（不含测试与迁移）。
> 依据：`feat/app-accounts` 注释版（提交 `16d0c0e`，PR #5），文中行号以该版本为准。
> 写法：按模板 3.1～3.4 组织；3.4 的 Q1～Q11 可直接在第 6 章改进计划里引用。

---

## 3.1 代码风格

**总体结论**：accounts 整体符合 PEP 8 的基本约定——4 个空格缩进，函数/变量用 snake_case，类名用 PascalCase，模块与函数大多有说明性注释；本次为 10 个业务文件补充了 113 行 `# ZYH:` 注释，模块级、函数级和关键行都有覆盖。主要偏差有三处：一是中英文标签混用（`forms.py` 里既有 `gettext_lazy` 的英文 label，也有直接写死的中文“确认密码”“邮箱”）；二是 `views.py` 的 `account_result` 用 `type`、`id` 作局部变量，遮蔽了内置函数；三是 `utils.py` 的模块级常量 `_code_ttl` 用了小写，按 PEP 8 常量应写成 `_CODE_TTL`。

**正面片段**（`accounts/models.py:14-22`）：

```python
14  class BlogUser(AbstractUser):
15      # ZYH: 昵称，用于前台作者信息展示；blank=True 表示允许为空。
16      nickname = models.CharField(_('nick name'), max_length=100, blank=True)
17      # ZYH: 用户创建时间，默认取当前时间，便于后台按注册时间排序与统计。
18      creation_time = models.DateTimeField(_('creation time'), default=now)
19      # ZYH: 用户信息最后修改时间，默认取当前时间，后续可在保存时手动更新。
20      last_modify_time = models.DateTimeField(_('last modify time'), default=now)
21      # ZYH: 用户来源，例如 Register、adminsite，用于区分注册渠道。
22      source = models.CharField(_('create source'), max_length=100, blank=True)
```

说明：字段命名统一 snake_case，每个字段前有中文注释，`verbose_name` 用 `gettext_lazy` 包裹，符合项目现有的国际化写法。

**偏差片段**（`accounts/forms.py:66-80`）：

```python
66      # ZYH: 确认密码字段，用于防止用户输错新密码。
67      new_password2 = forms.CharField(
68          label="确认密码",
69          widget=forms.PasswordInput(
70              attrs={
71                  "class": "form-control",
72                  'placeholder': _("Confirm password")
73              }
74          ),
75      )
76
77      # ZYH: 邮箱字段，用于定位要重置密码的账户。
78      email = forms.EmailField(
79          label='邮箱',
```

说明：同一文件里 `new_password1` 用 `_("New password")`，`new_password2` 却直接写中文；`email` 的 label 也是中文。项目以英文 gettext 为主，建议统一走 `_()`，中文放 `locale/zh_Hans` 翻译文件，避免以后做多语言时漏翻。

---

## 3.2 代码设计

**总体结论**：accounts 的分层比较清楚：`models.py` 只放用户模型，`forms.py` 负责字段与校验，`utils.py` 收口验证码的发送/缓存/校验，`views.py` 负责流程编排，`admin.py` 放后台表单。视图优先继承 `SecureFormView`、`LoginFormView`、`LogoutRedirectView`，复用了 CSRF、敏感参数保护和禁用缓存；`EmailOrUsernameModelBackend` 把“用户名或邮箱登录”单独做成认证后端，符合 Django 的认证扩展点。

**正面片段 1**（`accounts/user_login_backend.py:15-25`）：

```python
15      def authenticate(self, request, username=None, password=None, **kwargs):
16          # ZYH: 含 @ 时按邮箱查询，否则按用户名查询。
17          if '@' in username:
18              kwargs = {'email': username}
19          else:
20              kwargs = {'username': username}
21          try:
22              user = get_user_model().objects.get(**kwargs)
23              # ZYH: 使用 Django 的 check_password 校验哈希密码，禁止明文比较。
24              if user.check_password(password):
25                  return user
```

说明：把“用户名/邮箱二选一”的查询逻辑集中在认证后端，视图层不用关心登录标识；`check_password` 保证密码以哈希形式校验。

**正面片段 2**（`accounts/views.py:34,93,112` 的类声明）：

```python
34  class RegisterView(SecureFormView):
...
93  class LogoutView(LogoutRedirectView):
...
112 class LoginView(LoginFormView):
```

说明：三个视图分别复用项目基类的 CSRF 保护、退出缓存控制和登录敏感参数保护，避免每个视图重复写 `dispatch` 装饰器。

**偏差片段**（`accounts/views.py:137-145`）：

```python
137     def form_valid(self, form):
138         form = AuthenticationForm(data=self.request.POST, request=self.request)
139
140         if form.is_valid():
141             delete_sidebar_cache()
142             logger.info(self.redirect_field_name)
143
144             # ZYH: 调用 Django 认证体系建立登录会话，后续请求通过 session 识别用户。
145             auth.login(self.request, form.get_user())
```

说明：`LoginView` 已经声明 `form_class = LoginForm`，但 `form_valid` 又把传入的 `form` 丢掉，重新构造 `AuthenticationForm`，等于绕过了 `LoginForm` 的定制；同一份 POST 数据被校验两次，后续加验证码、限流或自定义 clean 时容易被忽略。建议直接使用传入的 `form`（必要时在 `LoginForm` 上扩展）。

**其他设计问题**：

- `RegisterView.form_valid` 在视图里拼激活邮件的 HTML（`views.py:64-82`），表现层和业务逻辑混在一起，建议移到模板或用 `render_to_string`；
- `account_result`（`views.py:187-221`）同时承担“结果页展示”和“邮箱激活”两件事，函数较长，建议拆成 `register_result` / `activate` 两个视图或辅助函数；
- `ForgetPasswordEmailCode`（`views.py:247-263`）直接继承 `View`，只接受 POST，没有频率限制，存在被刷邮件/短信接口的风险；
- `urls.py` 对静态路径也用了 `re_path`，可读性不如 `path`，但不影响功能。

---

## 3.3 编程技能

**总体结论**：accounts 里有几处体现了一定的编程功底：

1. 激活链接用 `SECRET_KEY + user.id` 做双重 `get_sha256` 签名，URL 里只暴露 id 和签名，不暴露用户敏感信息；
2. 登录按“记住我”分别设置 session 和 `logged_user` Cookie 的有效期，退出时同时清 session、侧边栏缓存和 Cookie；
3. 自定义认证后端支持用户名/邮箱登录，扩展点选得对；
4. 验证码用 Django cache 存储，TTL 固定 5 分钟，避免在数据库里堆临时数据；
5. 结果页用 `get_object_or_404` 处理不存在的用户，登录跳转用 `url_has_allowed_host_and_scheme` 防开放重定向；
6. 后台自定义 `BlogUserCreationForm`，保存时用 `set_password` 生成哈希，不落明文。

**片段 1**（`accounts/views.py:53-55`，激活签名）：

```python
53          # ZYH: 使用 SECRET_KEY 与用户 id 做两次 SHA256，生成不可伪造的激活签名。
54          sign = get_sha256(get_sha256(settings.SECRET_KEY + str(user.id)))
```

说明：签名把用户 id 和服务端密钥绑定，攻击者改 URL 里的 id 后签名对不上，`account_result` 会返回 403；这比直接把 `is_active=True` 暴露在 URL 里安全。

**片段 2**（`accounts/views.py:146-155`，登录有效期）：

```python
146         # 设置登录有效期
147         if self.request.POST.get("remember"):
148             # ZYH: 勾选“记住我”时使用配置的长期有效期。
149             self.request.session.set_expiry(settings.REMEMBER_ME_LOGIN_TTL)
150             cookie_max_age = settings.REMEMBER_ME_LOGIN_TTL
151         else:
152             # 使用Django默认的2周
153             # ZYH: 未勾选时使用 Django 默认的会话有效期。
154             self.request.session.set_expiry(settings.SESSION_COOKIE_AGE)
155             cookie_max_age = settings.SESSION_COOKIE_AGE
```

说明：会话和前端 Cookie 用同一个 `cookie_max_age`，不会出现“页面显示已登录、session 已过期”的不一致。

**片段 3**（`accounts/views.py:173-178`，安全跳转）：

```python
173         redirect_to = self.request.POST.get(self.redirect_field_name)
174         if not url_has_allowed_host_and_scheme(
175                 url=redirect_to, allowed_hosts=[
176                     self.request.get_host()]):
177             redirect_to = self.success_url
178         return redirect_to
```

说明：只允许跳回当前 Host，避免 `next=https://evil.example` 的开放重定向。

---

## 3.4 代码质量问题

| 编号 | 位置（文件:行） | 问题 | 严重程度 | 是否修复 | 修复建议（供第 6 章用） |
|---|---|---|---|---|---|
| Q1 | `accounts/views.py:59,83` | 同一文件同时使用 `account:result` 和 `accounts:result`；`djangoblog/urls.py:77` 的 include 用的是 `namespace='account'`，两种写法依赖 Django 的命名空间回退，路由调整时容易失效 | 低 | 否 | 统一用一个命名空间（建议与 include 一致的 `account:result`），并在测试里覆盖注册成功跳转 |
| Q2 | `accounts/models.py:14`、`accounts/forms.py:43` | `BlogUser` 继承 `AbstractUser`，email 没有唯一约束；注册只在表单层 `exists()` 检查，并发/后台导入可产生重复邮箱，而找回密码按 email 取用户 | 高 | 否 | 给 email 加 `unique=True`（或业务上保证唯一），注册用数据库唯一约束兜底；找回密码处理 `MultipleObjectsReturned` |
| Q3 | `accounts/views.py:237` | `BlogUser.objects.filter(email=...).get()` 在邮箱不存在或多条时抛 `DoesNotExist`/`MultipleObjectsReturned`，返回 500 | 中 | 否 | 用 `get_object_or_404` 或 try/except 转成表单错误 |
| Q4 | `accounts/views.py:138` | 丢弃传入的 `form`，重新构造 `AuthenticationForm`，绕过 `LoginForm` 定制并重复校验 | 中 | 否 | 直接用 `form`，把需要的定制放到 `LoginForm` |
| Q5 | `accounts/forms.py:101-106` | `clean_new_password2` 读 `self.data` 而不是 `self.cleaned_data`，拿到的是未清洗的原始输入；`validate_password` 也没有传 user | 中 | 否 | 改用 `self.cleaned_data`，并把 `user` 传给 `validate_password` 以启用相似度校验 |
| Q6 | `accounts/views.py:64-82` | 视图内拼接大段 HTML 邮件正文，表现层与业务逻辑耦合 | 中 | 否 | 移到 `templates/account/email/...`，用 `render_to_string` 渲染 |
| Q7 | `accounts/views.py:188-189` | `type`、`id` 遮蔽内置函数，后续想用 `type()`/`id()` 会出错 | 低 | 否 | 改名 `result_type`、`user_id` |
| Q8 | `accounts/views.py:210` | 激活时 `user.save()` 全字段更新，可能覆盖并发修改的其他字段 | 低 | 否 | `user.save(update_fields=['is_active'])` |
| Q9 | `accounts/utils.py:13` | 模块级常量 `_code_ttl` 使用小写，不符合 UPPER_CASE 约定 | 低 | 否 | 改名 `_CODE_TTL`，同步 `set_code` 引用 |
| Q10 | `accounts/views.py:247-263` | 发送找回密码验证码的接口没有频率限制，可被脚本反复调用刷邮件 | 中 | 否 | 按邮箱/IP 加缓存计数或 Django ratelimit，例如 60 秒 1 次、每天 N 次 |
| Q11 | `accounts/models.py:20` | `last_modify_time` 默认 `now`，但保存时从不更新，字段名与行为不符 | 低 | 否 | 重写 `save()` 或在业务层更新；也可改用 `auto_now=True`（注意会失去手动控制） |

> 说明：以上问题都是本次人工阅读发现的，均未修复（本次作业只加注释，不改业务逻辑）；修复建议可直接用于报告第 6 章“下一步的改进计划”。

---

## 给何君杰的汇总说明

1. 以上可直接作为报告第 3 章 accounts 部分的素材：3.1～3.3 是“结论 + 片段”，3.4 是问题表。
2. 行号以 `feat/app-accounts` 注释版（提交 `16d0c0e`，PR #5）为准；贴进报告时建议只保留 8～15 行关键片段，不要整段贴。
3. Q1～Q11 的编号可在第 6 章改进计划里直接引用（例如“针对 Q2 给 email 加唯一约束”）。
4. accounts 的注释统计见同目录《注释登记表-朱宇豪.xlsx》：10 个业务文件、113 行 `# ZYH:` 注释。
5. 需要更多片段（找回密码验证码链路、admin 自定义表单、登录失败处理）我可以再补。
