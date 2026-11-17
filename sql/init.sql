-- 个人支出记账：幂等初始化脚本
-- 执行前须确认：库名必须与 .env 中的 DB_NAME 一致。
-- 本脚本只包含幂等的建库建表语句。

CREATE DATABASE IF NOT EXISTS `expense_tracker`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `expense_tracker`.`records` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `amount` DECIMAL(10,2) NOT NULL COMMENT '金额（元）',
  `category` VARCHAR(16) NOT NULL COMMENT '分类（六个固定值之一）',
  `record_date` DATE NOT NULL COMMENT '记账日期',
  `note` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '备注',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_records_record_date` (`record_date`),
  KEY `idx_records_category_record_date` (`category`, `record_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='账目记录';
