-- MySQL dump 10.13  Distrib 9.4.0, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: dailyblog
-- ------------------------------------------------------
-- Server version	9.4.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `accounts_bloguser`
--

DROP TABLE IF EXISTS `accounts_bloguser`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_bloguser` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `first_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `nickname` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `source` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `creation_time` datetime(6) NOT NULL,
  `last_modify_time` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_bloguser`
--

LOCK TABLES `accounts_bloguser` WRITE;
/*!40000 ALTER TABLE `accounts_bloguser` DISABLE KEYS */;
INSERT INTO `accounts_bloguser` VALUES (1,'pbkdf2_sha256$1000000$L2aQdfVmE5ETvlaCwclpjl$LUhMRHemMD4iuIkMiqQbK1QwBP102fjPANunHNQGtNg=',NULL,1,'admin','','','admin@example.com',1,1,'2026-09-13 21:08:17.965397','我','','2026-09-13 21:08:17.965400','2026-09-13 21:08:17.965401');
/*!40000 ALTER TABLE `accounts_bloguser` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_bloguser_groups`
--

DROP TABLE IF EXISTS `accounts_bloguser_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_bloguser_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `bloguser_id` bigint NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_bloguser_groups_bloguser_id_group_id_fc37e89b_uniq` (`bloguser_id`,`group_id`),
  KEY `accounts_bloguser_groups_group_id_98d76804_fk_auth_group_id` (`group_id`),
  CONSTRAINT `accounts_bloguser_gr_bloguser_id_a16ccbb7_fk_accounts_` FOREIGN KEY (`bloguser_id`) REFERENCES `accounts_bloguser` (`id`),
  CONSTRAINT `accounts_bloguser_groups_group_id_98d76804_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_bloguser_groups`
--

LOCK TABLES `accounts_bloguser_groups` WRITE;
/*!40000 ALTER TABLE `accounts_bloguser_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_bloguser_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_bloguser_user_permissions`
--

DROP TABLE IF EXISTS `accounts_bloguser_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_bloguser_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `bloguser_id` bigint NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_bloguser_user_p_bloguser_id_permission_i_14808777_uniq` (`bloguser_id`,`permission_id`),
  KEY `accounts_bloguser_us_permission_id_ae5159b9_fk_auth_perm` (`permission_id`),
  CONSTRAINT `accounts_bloguser_us_bloguser_id_7e1b5742_fk_accounts_` FOREIGN KEY (`bloguser_id`) REFERENCES `accounts_bloguser` (`id`),
  CONSTRAINT `accounts_bloguser_us_permission_id_ae5159b9_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_bloguser_user_permissions`
--

LOCK TABLES `accounts_bloguser_user_permissions` WRITE;
/*!40000 ALTER TABLE `accounts_bloguser_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_bloguser_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=77 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add content type',4,'add_contenttype'),(14,'Can change content type',4,'change_contenttype'),(15,'Can delete content type',4,'delete_contenttype'),(16,'Can view content type',4,'view_contenttype'),(17,'Can add session',5,'add_session'),(18,'Can change session',5,'change_session'),(19,'Can delete session',5,'delete_session'),(20,'Can view session',5,'view_session'),(21,'Can add site',6,'add_site'),(22,'Can change site',6,'change_site'),(23,'Can delete site',6,'delete_site'),(24,'Can view site',6,'view_site'),(25,'Can add Website configuration',7,'add_blogsettings'),(26,'Can change Website configuration',7,'change_blogsettings'),(27,'Can delete Website configuration',7,'delete_blogsettings'),(28,'Can view Website configuration',7,'view_blogsettings'),(29,'Can add link',8,'add_links'),(30,'Can change link',8,'change_links'),(31,'Can delete link',8,'delete_links'),(32,'Can view link',8,'view_links'),(33,'Can add sidebar',9,'add_sidebar'),(34,'Can change sidebar',9,'change_sidebar'),(35,'Can delete sidebar',9,'delete_sidebar'),(36,'Can view sidebar',9,'view_sidebar'),(37,'Can add tag',10,'add_tag'),(38,'Can change tag',10,'change_tag'),(39,'Can delete tag',10,'delete_tag'),(40,'Can view tag',10,'view_tag'),(41,'Can add category',11,'add_category'),(42,'Can change category',11,'change_category'),(43,'Can delete category',11,'delete_category'),(44,'Can view category',11,'view_category'),(45,'Can add article',12,'add_article'),(46,'Can change article',12,'change_article'),(47,'Can delete article',12,'delete_article'),(48,'Can view article',12,'view_article'),(49,'Can add user',13,'add_bloguser'),(50,'Can change user',13,'change_bloguser'),(51,'Can delete user',13,'delete_bloguser'),(52,'Can view user',13,'view_bloguser'),(53,'Can add comment',14,'add_comment'),(54,'Can change comment',14,'change_comment'),(55,'Can delete comment',14,'delete_comment'),(56,'Can view comment',14,'view_comment'),(57,'Can add comment reaction',15,'add_commentreaction'),(58,'Can change comment reaction',15,'change_commentreaction'),(59,'Can delete comment reaction',15,'delete_commentreaction'),(60,'Can view comment reaction',15,'view_commentreaction'),(61,'Can add oauth配置',16,'add_oauthconfig'),(62,'Can change oauth配置',16,'change_oauthconfig'),(63,'Can delete oauth配置',16,'delete_oauthconfig'),(64,'Can view oauth配置',16,'view_oauthconfig'),(65,'Can add oauth user',17,'add_oauthuser'),(66,'Can change oauth user',17,'change_oauthuser'),(67,'Can delete oauth user',17,'delete_oauthuser'),(68,'Can view oauth user',17,'view_oauthuser'),(69,'Can add 命令',18,'add_commands'),(70,'Can change 命令',18,'change_commands'),(71,'Can delete 命令',18,'delete_commands'),(72,'Can view 命令',18,'view_commands'),(73,'Can add 邮件发送log',19,'add_emailsendlog'),(74,'Can change 邮件发送log',19,'change_emailsendlog'),(75,'Can delete 邮件发送log',19,'delete_emailsendlog'),(76,'Can view 邮件发送log',19,'view_emailsendlog');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `blog_article`
--

DROP TABLE IF EXISTS `blog_article`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `blog_article` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `body` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `pub_time` datetime(6) NOT NULL,
  `status` varchar(1) COLLATE utf8mb4_unicode_ci NOT NULL,
  `comment_status` varchar(1) COLLATE utf8mb4_unicode_ci NOT NULL,
  `type` varchar(1) COLLATE utf8mb4_unicode_ci NOT NULL,
  `views` int unsigned NOT NULL,
  `article_order` int NOT NULL,
  `show_toc` tinyint(1) NOT NULL,
  `author_id` bigint NOT NULL,
  `category_id` int NOT NULL,
  `creation_time` datetime(6) NOT NULL,
  `last_modify_time` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `title` (`title`),
  KEY `idx_type_status_pub` (`type`,`status`,`pub_time` DESC),
  KEY `idx_status_views` (`status`,`views` DESC),
  KEY `idx_author_status_type` (`author_id`,`status`,`type`),
  KEY `idx_category_status` (`category_id`,`status`),
  CONSTRAINT `blog_article_author_id_905add38_fk_accounts_bloguser_id` FOREIGN KEY (`author_id`) REFERENCES `accounts_bloguser` (`id`),
  CONSTRAINT `blog_article_category_id_7e38f15e_fk_blog_category_id` FOREIGN KEY (`category_id`) REFERENCES `blog_category` (`id`),
  CONSTRAINT `blog_article_chk_1` CHECK ((`views` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `blog_article`
--

LOCK TABLES `blog_article` WRITE;
/*!40000 ALTER TABLE `blog_article` DISABLE KEYS */;
INSERT INTO `blog_article` VALUES (7,'Agent 选型份额报告 · 项目说明','> 一句话：**统计 AI 编程助手都在推荐谁家的产品，把数据卖给厂商。**\n\n---\n\n## 一、背景：发生了什么变化\n\n以前，开发者选工具靠的是：Google 搜索、看博客、问同事。\n\n现在，越来越多开发者直接让 AI 编程助手（Claude Code、Cursor、Codex 等）帮自己做决定：\n\n```\n开发者对 AI 说：\"帮我给这个项目加个数据库\"\nAI 直接回答：\"用 Supabase\"，并且顺手就配好了\n```\n\n**AI 说什么，开发者就用什么。** AI 成了一个新的\"销售渠道\"。\n\n问题在于：**这个渠道是看不见的。**\n\nSupabase 发现新用户变多了，但市场部说不清用户哪来的——不是广告，不是搜索，是 AI 推荐的。看不见就没办法管理，也没办法向老板汇报。\n\n## 二、我们要做什么\n\n做一个\"市场调研公司\"，但调研对象不是人，是 AI。\n\n### 具体做法（三步）\n\n**第 1 步：出题**\n\n准备一批标准化任务，模拟真实开发场景：\n\n- \"给一个 Next.js 电商网站加数据库\"\n- \"给 Flask 应用加用户登录功能\"\n- \"帮我选一个能存向量数据的方案\"\n\n**第 2 步：定期考试**\n\n每周把这些题喂给各家 AI 助手，每个 AI 跑几百遍，记录它们分别推荐了哪些产品。\n\n**第 3 步：出报告、卖订阅**\n\n```\n《2026 年 9 月 Agent 选型报告 · 数据库品类》\n\n- Supabase：被推荐率 58%（比上月 +3%）\n- Neon：22%（比上月 +5%）← 本月黑马\n- PlanetScale：11%（比上月 -8%）⚠️ 正在掉队\n- 附：AI 推荐 Neon 时最常用的理由 top 3\n```\n\n厂商按月付费，持续追踪自己在\"AI 渠道\"里的份额变化——就像今天品牌方买尼尔森的市场份额报告一样。\n\n## 三、为什么这个生意能成立\n\n| 关键点 | 说明 |\n|---|---|\n| **痛点真实** | 厂商明知 AI 在给自己（或对手）拉客，却完全没有数据 |\n| **数据别人抄不走** | 必须持续烧钱跑真实测试才能拿到，不是网上能爬到的 |\n| **越老越值钱** | 历史数据积累越久，趋势分析越有价值 |\n| **天然订阅制** | 厂商需要的是持续监测，不是一次性报告 |\n| **有真实对标** | 通用领域已有公司（如 Profound）做\"AI 搜索可见度监测\"并获得高估值；但专门盯\"AI 编程助手选型\"的还没人做好 |\n\n## 四、技术难不难？——不难\n\n整个系统四个零件，一个人 3-4 周能做出第一版：\n\n1. **题库**：写几十个标准化任务文本（手动活，零代码）\n2. **测试机器人**：AI 助手都有命令行版本，脚本自动批量调用（1-2 天）\n3. **结果统计**：用便宜的小模型自动识别\"这次推荐了谁\"（1-2 天）\n4. **报表网站**：普通的图表 dashboard（1-2 周）\n\n**运行成本**：每次测试只花一点 API 调用费，每月几百元人民币的规模。\n\n> 这个项目的难度 80% 不在技术，在下面第五部分。\n\n## 五、真正的难点（要提前想清楚）\n\n1. **信誉冷启动（最大难点）**\n   报告要先免费公开发布几个月，在行业社区（HN、Twitter、V2EX）攒出口碑，厂商才会认你是\"权威数据源\"。**前半年约等于做内容博主，没有收入。**\n\n2. **厂商可能自己测**\n   厂商花几百块也能自己跑测试。我们的壁垒是：**第三方中立身份 + 全行业最全的历史数据**——自己测的数据没法对外引用，尼尔森的价值就在于此。\n\n3. **题库要保密**\n   题目一旦泄露，厂商会针对性\"刷榜\"（往互联网上灌对自己有利的内容）。题库需要定期更换、不对外公开。\n\n4. **AI 版本更新会造成数据波动**\n   AI 升级后推荐偏好可能突变。这既是风险也是卖点——厂商更需要持续盯数据了。\n\n## 六、落地路径建议\n\n```\n阶段 1（第 1-2 个月）：做 MVP + 免费公开报告\n  → 每周发一份《AI 最爱推荐什么》公开周报，攒行业声望\n\n阶段 2（第 3-6 个月）：验证付费意愿\n  → 主动联系报告里提到的厂商，卖\"详细版数据 + 理由分析\"\n\n阶段 3（第 6 个月后）：订阅制\n  → 按品类收月费，逐品类扩张（数据库 → 鉴权 → 部署 → 监控……）\n```\n\n## 七、和 loopkit 的关系\n\n这个项目和 loopkit 是**同一个市场的两面**：\n\n- **loopkit** = 帮厂商\"被 AI 选中\"的武器（进攻）\n- **本项目** = 帮厂商\"看见自己有没有被选中\"的雷达（测量）\n\n报告积累的行业洞察可以直接指导 loopkit 的内容方向；报告里\"掉队\"的厂商，就是 loopkit 最精准的销售线索。**两个项目共用一套叙事，互相导流。**\n\n---\n\n*文档版本：v1 · 2026-08-19*','2026-09-20 17:35:09.110697','p','o','a',0,0,0,1,3,'2026-09-20 17:35:09.110732','2026-09-20 17:35:09.110735');
/*!40000 ALTER TABLE `blog_article` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `blog_article_tags`
--

DROP TABLE IF EXISTS `blog_article_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `blog_article_tags` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `article_id` int NOT NULL,
  `tag_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `blog_article_tags_article_id_tag_id_b78a22e9_uniq` (`article_id`,`tag_id`),
  KEY `blog_article_tags_tag_id_88eb3ed9_fk_blog_tag_id` (`tag_id`),
  CONSTRAINT `blog_article_tags_article_id_82c02dd6_fk_blog_article_id` FOREIGN KEY (`article_id`) REFERENCES `blog_article` (`id`),
  CONSTRAINT `blog_article_tags_tag_id_88eb3ed9_fk_blog_tag_id` FOREIGN KEY (`tag_id`) REFERENCES `blog_tag` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `blog_article_tags`
--

LOCK TABLES `blog_article_tags` WRITE;
/*!40000 ALTER TABLE `blog_article_tags` DISABLE KEYS */;
INSERT INTO `blog_article_tags` VALUES (15,7,15),(16,7,16),(17,7,17);
/*!40000 ALTER TABLE `blog_article_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `blog_blogsettings`
--

DROP TABLE IF EXISTS `blog_blogsettings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `blog_blogsettings` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `site_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `site_description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `site_seo_description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `site_keywords` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `article_sub_length` int NOT NULL,
  `sidebar_article_count` int NOT NULL,
  `sidebar_comment_count` int NOT NULL,
  `article_comment_count` int NOT NULL,
  `show_google_adsense` tinyint(1) NOT NULL,
  `google_adsense_codes` longtext COLLATE utf8mb4_unicode_ci,
  `open_site_comment` tinyint(1) NOT NULL,
  `beian_code` varchar(2000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `analytics_code` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `show_gongan_code` tinyint(1) NOT NULL,
  `gongan_beiancode` longtext COLLATE utf8mb4_unicode_ci,
  `global_footer` longtext COLLATE utf8mb4_unicode_ci,
  `global_header` longtext COLLATE utf8mb4_unicode_ci,
  `comment_need_review` tinyint(1) NOT NULL,
  `color_scheme` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `blog_blogsettings`
--

LOCK TABLES `blog_blogsettings` WRITE;
/*!40000 ALTER TABLE `blog_blogsettings` DISABLE KEYS */;
INSERT INTO `blog_blogsettings` VALUES (1,'知识分享','分享商业与 AI 产品的学习笔记','分享商业与 AI 产品的学习笔记：购买理由、需求挖掘、MVP 验证，以及能赚钱的 AI 产品去哪里找。','AI产品,商业,需求,创业,产品思维',200,8,5,5,0,'',1,'','',0,'','','<style id=\"custom-beautify\">\n/* ============ 站点自定义美化（轻量） ============ */\n:root {\n  --bw-accent: #0d9488;                 /* 青绿主色，与 teal 配色方案一致 */\n  --bw-accent-soft: rgba(13, 148, 136, .10);\n  --bw-radius: 18px;\n  --bw-shadow: 0 1px 2px rgba(15, 23, 42, .04), 0 8px 24px -12px rgba(15, 23, 42, .18);\n}\n\n/* 1. 字体：优先中文屏显字体，正文更好看 */\nbody {\n  font-family: \"PingFang SC\", \"HarmonyOS Sans SC\", \"Microsoft YaHei\", \"Open Sans\",\n               system-ui, -apple-system, \"Segoe UI\", sans-serif;\n  -webkit-font-smoothing: antialiased;\n  -moz-osx-font-smoothing: grayscale;\n}\narticle p, .article-content p, .prose p {\n  line-height: 1.95;\n  letter-spacing: .01em;\n}\n\n/* 2. 文章卡片：大圆角 + 柔和阴影 + 悬浮微抬 */\narticle.group {\n  border-radius: var(--bw-radius) !important;\n  box-shadow: var(--bw-shadow) !important;\n  transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease;\n}\narticle.group:hover {\n  transform: translateY(-3px);\n  border-color: var(--bw-accent) !important;\n  box-shadow: 0 2px 4px rgba(15, 23, 42, .05), 0 18px 40px -18px rgba(13, 148, 136, .38) !important;\n}\n\n/* 3. 标题：更稳的字重与字距，悬浮变主色 */\narticle.group h2 { font-weight: 700; letter-spacing: -.01em; }\narticle.group h2 a:hover { color: var(--bw-accent) !important; }\n\n/* 4. 标签：胶囊化 + 悬浮填充 */\na[href*=\"/tag/\"] {\n  border-radius: 999px !important;\n  padding-left: .65rem;\n  padding-right: .65rem;\n}\na[href*=\"/tag/\"]:hover {\n  border-color: var(--bw-accent) !important;\n  background: var(--bw-accent-soft) !important;\n  color: var(--bw-accent) !important;\n}\n\n/* 5. 顶栏：加一条细渐变线，更有层次 */\nheader.sticky { box-shadow: 0 1px 0 rgba(15, 23, 42, .05); }\nheader.sticky::after {\n  content: \"\";\n  display: block;\n  height: 2px;\n  background: linear-gradient(90deg, transparent, var(--bw-accent), transparent);\n  opacity: .35;\n}\n\n/* 6. 侧边栏区块：统一圆角 */\naside section, aside > div { border-radius: var(--bw-radius); }\n\n/* 7. 选中文字与滚动条 */\n::selection { background: rgba(13, 148, 136, .22); }\n::-webkit-scrollbar { width: 10px; height: 10px; }\n::-webkit-scrollbar-thumb {\n  background: rgba(100, 116, 139, .35);\n  border-radius: 999px;\n  border: 2px solid transparent;\n  background-clip: content-box;\n}\n::-webkit-scrollbar-thumb:hover { background: rgba(13, 148, 136, .55); background-clip: content-box; }\n\n/* 8. 图片 / 代码块 / 引用：圆角统一 */\n.article-content img, article img, pre, blockquote { border-radius: 14px; }\npre { padding: 1rem 1.1rem; }\n</style>',0,'teal');
/*!40000 ALTER TABLE `blog_blogsettings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `blog_category`
--

DROP TABLE IF EXISTS `blog_category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `blog_category` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `slug` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `index` int NOT NULL,
  `parent_category_id` int DEFAULT NULL,
  `creation_time` datetime(6) NOT NULL,
  `last_modify_time` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `blog_category_parent_category_id_f50c3c0c_fk_blog_category_id` (`parent_category_id`),
  KEY `blog_category_slug_92643dc5` (`slug`),
  CONSTRAINT `blog_category_parent_category_id_f50c3c0c_fk_blog_category_id` FOREIGN KEY (`parent_category_id`) REFERENCES `blog_category` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `blog_category`
--

LOCK TABLES `blog_category` WRITE;
/*!40000 ALTER TABLE `blog_category` DISABLE KEYS */;
INSERT INTO `blog_category` VALUES (3,'商业','shang-ye',0,NULL,'2026-09-20 16:33:55.046180','2026-09-20 16:33:55.046185');
/*!40000 ALTER TABLE `blog_category` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `blog_links`
--

DROP TABLE IF EXISTS `blog_links`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `blog_links` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `link` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sequence` int NOT NULL,
  `is_enable` tinyint(1) NOT NULL,
  `show_type` varchar(1) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_mod_time` datetime(6) NOT NULL,
  `creation_time` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `sequence` (`sequence`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `blog_links`
--

LOCK TABLES `blog_links` WRITE;
/*!40000 ALTER TABLE `blog_links` DISABLE KEYS */;
/*!40000 ALTER TABLE `blog_links` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `blog_sidebar`
--

DROP TABLE IF EXISTS `blog_sidebar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `blog_sidebar` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `sequence` int NOT NULL,
  `is_enable` tinyint(1) NOT NULL,
  `last_mod_time` datetime(6) NOT NULL,
  `creation_time` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `sequence` (`sequence`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `blog_sidebar`
--

LOCK TABLES `blog_sidebar` WRITE;
/*!40000 ALTER TABLE `blog_sidebar` DISABLE KEYS */;
/*!40000 ALTER TABLE `blog_sidebar` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `blog_tag`
--

DROP TABLE IF EXISTS `blog_tag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `blog_tag` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `slug` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `creation_time` datetime(6) NOT NULL,
  `last_modify_time` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `blog_tag_slug_01068d0e` (`slug`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `blog_tag`
--

LOCK TABLES `blog_tag` WRITE;
/*!40000 ALTER TABLE `blog_tag` DISABLE KEYS */;
INSERT INTO `blog_tag` VALUES (15,'Agent','agent','2026-09-20 17:35:09.562353','2026-09-20 17:35:09.562357'),(16,'市场调研','shi-chang-diao-yan','2026-09-20 17:35:09.578181','2026-09-20 17:35:09.578184'),(17,'商业模式','shang-ye-mo-shi','2026-09-20 17:35:09.593903','2026-09-20 17:35:09.593906');
/*!40000 ALTER TABLE `blog_tag` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comments_comment`
--

DROP TABLE IF EXISTS `comments_comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comments_comment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `body` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_enable` tinyint(1) NOT NULL,
  `article_id` int NOT NULL,
  `author_id` bigint NOT NULL,
  `parent_comment_id` bigint DEFAULT NULL,
  `creation_time` datetime(6) NOT NULL,
  `last_modify_time` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `comments_comment_author_id_334ce9e2_fk_accounts_bloguser_id` (`author_id`),
  KEY `comments_comment_parent_comment_id_71289d4a_fk_comments_` (`parent_comment_id`),
  KEY `idx_art_parent_enable` (`article_id`,`parent_comment_id`,`is_enable`),
  KEY `idx_enable_id` (`is_enable`,`id` DESC),
  CONSTRAINT `comments_comment_article_id_94fe60a2_fk_blog_article_id` FOREIGN KEY (`article_id`) REFERENCES `blog_article` (`id`),
  CONSTRAINT `comments_comment_author_id_334ce9e2_fk_accounts_bloguser_id` FOREIGN KEY (`author_id`) REFERENCES `accounts_bloguser` (`id`),
  CONSTRAINT `comments_comment_parent_comment_id_71289d4a_fk_comments_` FOREIGN KEY (`parent_comment_id`) REFERENCES `comments_comment` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comments_comment`
--

LOCK TABLES `comments_comment` WRITE;
/*!40000 ALTER TABLE `comments_comment` DISABLE KEYS */;
/*!40000 ALTER TABLE `comments_comment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comments_commentreaction`
--

DROP TABLE IF EXISTS `comments_commentreaction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comments_commentreaction` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `reaction_type` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `comment_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `comments_commentreaction_comment_id_user_id_react_59e7fb94_uniq` (`comment_id`,`user_id`,`reaction_type`),
  KEY `comments_commentreac_user_id_1be332d5_fk_accounts_` (`user_id`),
  KEY `idx_comment_reaction` (`comment_id`,`reaction_type`),
  CONSTRAINT `comments_commentreac_comment_id_873aaba8_fk_comments_` FOREIGN KEY (`comment_id`) REFERENCES `comments_comment` (`id`),
  CONSTRAINT `comments_commentreac_user_id_1be332d5_fk_accounts_` FOREIGN KEY (`user_id`) REFERENCES `accounts_bloguser` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comments_commentreaction`
--

LOCK TABLES `comments_commentreaction` WRITE;
/*!40000 ALTER TABLE `comments_commentreaction` DISABLE KEYS */;
/*!40000 ALTER TABLE `comments_commentreaction` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext COLLATE utf8mb4_unicode_ci,
  `object_repr` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_accounts_bloguser_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_accounts_bloguser_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_bloguser` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `model` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (13,'accounts','bloguser'),(1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(12,'blog','article'),(7,'blog','blogsettings'),(11,'blog','category'),(8,'blog','links'),(9,'blog','sidebar'),(10,'blog','tag'),(14,'comments','comment'),(15,'comments','commentreaction'),(4,'contenttypes','contenttype'),(16,'oauth','oauthconfig'),(17,'oauth','oauthuser'),(18,'servermanager','commands'),(19,'servermanager','emailsendlog'),(5,'sessions','session'),(6,'sites','site');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=41 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-09-13 21:07:51.392817'),(2,'contenttypes','0002_remove_content_type_name','2026-09-13 21:07:51.560937'),(3,'auth','0001_initial','2026-09-13 21:07:52.010068'),(4,'auth','0002_alter_permission_name_max_length','2026-09-13 21:07:52.099512'),(5,'auth','0003_alter_user_email_max_length','2026-09-13 21:07:52.105566'),(6,'auth','0004_alter_user_username_opts','2026-09-13 21:07:52.113656'),(7,'auth','0005_alter_user_last_login_null','2026-09-13 21:07:52.120795'),(8,'auth','0006_require_contenttypes_0002','2026-09-13 21:07:52.126295'),(9,'auth','0007_alter_validators_add_error_messages','2026-09-13 21:07:52.135215'),(10,'auth','0008_alter_user_username_max_length','2026-09-13 21:07:52.141461'),(11,'auth','0009_alter_user_last_name_max_length','2026-09-13 21:07:52.147770'),(12,'auth','0010_alter_group_name_max_length','2026-09-13 21:07:52.166141'),(13,'auth','0011_update_proxy_permissions','2026-09-13 21:07:52.172590'),(14,'auth','0012_alter_user_first_name_max_length','2026-09-13 21:07:52.178328'),(15,'accounts','0001_initial','2026-09-13 21:07:52.709462'),(16,'accounts','0002_alter_bloguser_options_remove_bloguser_created_time_and_more','2026-09-13 21:07:53.055516'),(17,'admin','0001_initial','2026-09-13 21:07:53.283988'),(18,'admin','0002_logentry_remove_auto_add','2026-09-13 21:07:53.290948'),(19,'admin','0003_logentry_add_action_flag_choices','2026-09-13 21:07:53.298777'),(20,'blog','0001_initial','2026-09-13 21:07:54.072576'),(21,'blog','0002_blogsettings_global_footer_and_more','2026-09-13 21:07:54.201760'),(22,'blog','0003_blogsettings_comment_need_review','2026-09-13 21:07:54.282876'),(23,'blog','0004_rename_analyticscode_blogsettings_analytics_code_and_more','2026-09-13 21:07:54.354022'),(24,'blog','0005_alter_article_options_alter_category_options_and_more','2026-09-13 21:07:55.903965'),(25,'blog','0006_alter_blogsettings_options','2026-09-13 21:07:55.909384'),(26,'blog','0007_article_idx_type_status_pub_article_idx_status_views_and_more','2026-09-13 21:07:56.052520'),(27,'blog','0008_blogsettings_color_scheme','2026-09-13 21:07:56.130936'),(28,'comments','0001_initial','2026-09-13 21:07:56.459928'),(29,'comments','0002_alter_comment_is_enable','2026-09-13 21:07:56.469565'),(30,'comments','0003_alter_comment_options_remove_comment_created_time_and_more','2026-09-13 21:07:56.851419'),(31,'comments','0004_comment_idx_art_parent_enable_comment_idx_enable_id','2026-09-13 21:07:56.909972'),(32,'comments','0005_commentreaction','2026-09-13 21:07:57.181312'),(33,'oauth','0001_initial','2026-09-13 21:07:57.328030'),(34,'oauth','0002_alter_oauthconfig_options_alter_oauthuser_options_and_more','2026-09-13 21:07:57.986473'),(35,'oauth','0003_alter_oauthuser_nickname','2026-09-13 21:07:57.995476'),(36,'servermanager','0001_initial','2026-09-13 21:07:58.049150'),(37,'servermanager','0002_alter_emailsendlog_options_and_more','2026-09-13 21:07:58.124729'),(38,'sessions','0001_initial','2026-09-13 21:07:58.203917'),(39,'sites','0001_initial','2026-09-13 21:07:58.241863'),(40,'sites','0002_alter_domain_unique','2026-09-13 21:07:58.267850');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_data` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_site`
--

DROP TABLE IF EXISTS `django_site`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_site` (
  `id` int NOT NULL AUTO_INCREMENT,
  `domain` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_site_domain_a2e37b91_uniq` (`domain`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_site`
--

LOCK TABLES `django_site` WRITE;
/*!40000 ALTER TABLE `django_site` DISABLE KEYS */;
INSERT INTO `django_site` VALUES (1,'example.com','example.com');
/*!40000 ALTER TABLE `django_site` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `oauth_oauthconfig`
--

DROP TABLE IF EXISTS `oauth_oauthconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `oauth_oauthconfig` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `type` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `appkey` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `appsecret` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `callback_url` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_enable` tinyint(1) NOT NULL,
  `creation_time` datetime(6) NOT NULL,
  `last_modify_time` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `oauth_oauthconfig`
--

LOCK TABLES `oauth_oauthconfig` WRITE;
/*!40000 ALTER TABLE `oauth_oauthconfig` DISABLE KEYS */;
/*!40000 ALTER TABLE `oauth_oauthconfig` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `oauth_oauthuser`
--

DROP TABLE IF EXISTS `oauth_oauthuser`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `oauth_oauthuser` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `openid` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nickname` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `token` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `picture` varchar(350) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `metadata` longtext COLLATE utf8mb4_unicode_ci,
  `author_id` bigint DEFAULT NULL,
  `creation_time` datetime(6) NOT NULL,
  `last_modify_time` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `oauth_oauthuser_author_id_a975bef0_fk_accounts_bloguser_id` (`author_id`),
  CONSTRAINT `oauth_oauthuser_author_id_a975bef0_fk_accounts_bloguser_id` FOREIGN KEY (`author_id`) REFERENCES `accounts_bloguser` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `oauth_oauthuser`
--

LOCK TABLES `oauth_oauthuser` WRITE;
/*!40000 ALTER TABLE `oauth_oauthuser` DISABLE KEYS */;
/*!40000 ALTER TABLE `oauth_oauthuser` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `servermanager_commands`
--

DROP TABLE IF EXISTS `servermanager_commands`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `servermanager_commands` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(300) COLLATE utf8mb4_unicode_ci NOT NULL,
  `command` varchar(2000) COLLATE utf8mb4_unicode_ci NOT NULL,
  `describe` varchar(300) COLLATE utf8mb4_unicode_ci NOT NULL,
  `creation_time` datetime(6) NOT NULL,
  `last_modify_time` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `servermanager_commands`
--

LOCK TABLES `servermanager_commands` WRITE;
/*!40000 ALTER TABLE `servermanager_commands` DISABLE KEYS */;
/*!40000 ALTER TABLE `servermanager_commands` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `servermanager_emailsendlog`
--

DROP TABLE IF EXISTS `servermanager_emailsendlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `servermanager_emailsendlog` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `emailto` varchar(300) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(2000) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `send_result` tinyint(1) NOT NULL,
  `creation_time` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `servermanager_emailsendlog`
--

LOCK TABLES `servermanager_emailsendlog` WRITE;
/*!40000 ALTER TABLE `servermanager_emailsendlog` DISABLE KEYS */;
/*!40000 ALTER TABLE `servermanager_emailsendlog` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-09-20 18:32:04
