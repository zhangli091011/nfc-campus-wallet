-- Migration 013: Random Discount System
-- 随机立减系统表

CREATE TABLE IF NOT EXISTS `random_discount_settings` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `event_id` INT NOT NULL,
    `enabled` BOOLEAN NOT NULL DEFAULT FALSE,
    `min_discount_amount` DECIMAL(12, 2) NOT NULL DEFAULT 0.01,
    `max_discount_amount` DECIMAL(12, 2) NOT NULL DEFAULT 5.00,
    `probability` INT NOT NULL DEFAULT 100 COMMENT '触发概率 1-100',
    `total_pool` DECIMAL(12, 2) NOT NULL DEFAULT 1000.00,
    `remaining_pool` DECIMAL(12, 2) NOT NULL DEFAULT 1000.00,
    `max_discount_per_transaction` DECIMAL(12, 2) DEFAULT NULL,
    `min_payment_amount` DECIMAL(12, 2) NOT NULL DEFAULT 1.00,
    `daily_limit_per_user` INT DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY `uq_random_discount_event` (`event_id`),
    CONSTRAINT `fk_random_discount_event` FOREIGN KEY (`event_id`) REFERENCES `events` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `random_discount_records` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `event_id` INT NOT NULL,
    `participant_id` INT NOT NULL,
    `transaction_id` INT NOT NULL,
    `booth_id` INT DEFAULT NULL,
    `original_amount` DECIMAL(12, 2) NOT NULL,
    `discount_amount` DECIMAL(12, 2) NOT NULL,
    `actual_amount` DECIMAL(12, 2) NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_discount_record_event` FOREIGN KEY (`event_id`) REFERENCES `events` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_discount_record_participant` FOREIGN KEY (`participant_id`) REFERENCES `participants` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_discount_record_transaction` FOREIGN KEY (`transaction_id`) REFERENCES `transactions` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_discount_record_booth` FOREIGN KEY (`booth_id`) REFERENCES `booths` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
