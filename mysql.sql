/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `factoids` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `factoid_key` longtext COLLATE utf8_unicode_ci NOT NULL,
  `factoid_value` longtext COLLATE utf8_unicode_ci DEFAULT NULL,
  `factoid_author` text COLLATE utf8_unicode_ci NOT NULL,
  `factoid_channel` text COLLATE utf8_unicode_ci NOT NULL,
  `factoid_timestamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `factoid_locked` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
