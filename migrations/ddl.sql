-- Таблица для пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) CHECK (role IN ('buyer', 'seller', 'admin')) DEFAULT 'buyer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pending_sellers (
    user_id INT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица магазинов
CREATE TABLE IF NOT EXISTS shops (
    shop_id SERIAL PRIMARY KEY,
    seller_id INTEGER REFERENCES users(id) ON DELETE CASCADE, -- Каскадное удаление магазина при удалении продавца
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица платформ
CREATE TABLE IF NOT EXISTS platforms (
    platform_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- Таблица игр
CREATE TABLE IF NOT EXISTS games (
    game_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    publisher VARCHAR(255),
    genre VARCHAR(255),
    platform_id INT REFERENCES platforms(platform_id) ON DELETE CASCADE,
    release_date DATE,
    shop_id INTEGER REFERENCES shops(shop_id) ON DELETE SET NULL
);

-- Таблица связей магазинов и игр (shop_games)
CREATE TABLE IF NOT EXISTS shop_games (
    shop_id INT REFERENCES shops(shop_id) ON DELETE CASCADE,
    game_id INT REFERENCES games(game_id) ON DELETE CASCADE,
    PRIMARY KEY (shop_id, game_id)
);

-- Таблица ключей
CREATE TABLE IF NOT EXISTS keys (
    key_id SERIAL PRIMARY KEY,
    game_id INT REFERENCES games(game_id) ON DELETE CASCADE,
    key_value VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'available',
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shop_id INTEGER REFERENCES shops(shop_id) ON DELETE CASCADE -- Каскадное удаление ключей при удалении магазина
);

-- Таблица продаж
CREATE TABLE IF NOT EXISTS sales (
    sale_id SERIAL PRIMARY KEY,
    buyer_id INT REFERENCES users(id) ON DELETE SET NULL, -- Сохраняем покупателя, но удаляем продажу
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица деталей продаж
CREATE TABLE IF NOT EXISTS sales_details (
    sale_id INT REFERENCES sales(sale_id) ON DELETE CASCADE, -- Каскадное удаление деталей продаж
    key_id INT REFERENCES keys(key_id) ON DELETE CASCADE, -- Каскадное удаление при удалении ключа
    PRIMARY KEY (sale_id, key_id)
);

-- Таблица для связей магазинов и ключей
CREATE TABLE IF NOT EXISTS shop_keys (
    shop_id INT REFERENCES shops(shop_id) ON DELETE CASCADE,
    key_id INT REFERENCES keys(key_id) ON DELETE CASCADE,
    PRIMARY KEY (shop_id, key_id)
);

-- Таблица цен, связанная с таблицей ключей
CREATE TABLE IF NOT EXISTS prices (
    key_id INT PRIMARY KEY REFERENCES keys(key_id) ON DELETE CASCADE, -- Связь с таблицей keys
    start_date DATE NOT NULL,
    end_date DATE,
    price DECIMAL(10, 2) NOT NULL
);

-- Создание представлений
CREATE VIEW v_available_keys AS
SELECT
    k.key_id,
    k.key_value,
    g.title AS game_title,
    p.name AS platform_name,
    k.status,
    s.name AS shop_name,
    pr.price
FROM
    keys k
    JOIN games g ON k.game_id = g.game_id
    JOIN platforms p ON g.platform_id = p.platform_id
    JOIN shops s ON k.shop_id = s.shop_id
    LEFT JOIN prices pr ON k.key_id = pr.key_id
WHERE
    k.status = 'available' AND pr.price IS NOT NULL;

COMMENT ON VIEW v_available_keys IS 'Список доступных ключей с информацией об игре, платформе, магазине и цене.';

CREATE VIEW v_sales_statistics AS
SELECT
    s.sale_date,
    g.title AS game_title,
    pl.name AS platform_name,
    COUNT(k.key_id) AS sold_keys_count,
    SUM(pr.price) AS total_revenue
FROM
    sales s
    JOIN sales_details sd ON s.sale_id = sd.sale_id
    JOIN keys k ON sd.key_id = k.key_id
    JOIN games g ON k.game_id = g.game_id
    JOIN platforms pl ON g.platform_id = pl.platform_id
    JOIN prices pr ON k.key_id = pr.key_id
WHERE
    s.sale_date BETWEEN pr.start_date AND COALESCE(pr.end_date, '5999-12-31'::date)
GROUP BY
    s.sale_date, g.title, pl.name;

COMMENT ON VIEW v_sales_statistics IS 'Статистика продаж по дням с подсчетом проданных ключей и выручки.';

-- Функция для удаления пользователя (только для администраторов)
CREATE OR REPLACE FUNCTION delete_user(admin_id INT, target_user_id INT)
RETURNS VOID AS $$
DECLARE
    admin_role VARCHAR(20);
BEGIN
    SELECT role INTO admin_role FROM users WHERE id = admin_id;

    IF admin_role <> 'admin' THEN
        RAISE EXCEPTION 'Only an admin can delete users.';
    END IF;

    DELETE FROM shops WHERE seller_id = target_user_id;

    DELETE FROM keys WHERE shop_id IN (SELECT shop_id FROM shops WHERE seller_id = target_user_id);

    DELETE FROM pending_sellers WHERE user_id = target_user_id;

    DELETE FROM users WHERE id = target_user_id;
END;
$$ LANGUAGE plpgsql;
