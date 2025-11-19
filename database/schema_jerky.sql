-- Jerky Products Table (for the parody "Reserve Collection" section)

CREATE TABLE IF NOT EXISTS jerky_products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL, -- Display title
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    weight VARCHAR(50), -- e.g., "4oz", "6oz"
    image_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'available', -- 'sold_out', 'coming_soon', 'seasonal', 'available'
    badge_text VARCHAR(50), -- Custom badge text (e.g., "SOLD OUT", "COMING SOON", "SEASONAL")
    badge_color VARCHAR(20), -- Color for the badge
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_jerky_products_active ON jerky_products(is_active);
CREATE INDEX IF NOT EXISTS idx_jerky_products_status ON jerky_products(status);

-- Seed initial jerky products (the parody items)
INSERT INTO jerky_products (name, slug, title, description, price, weight, image_url, status, badge_text, display_order)
VALUES 
    ('Premium Bear Jerky', 'premium-bear-jerky', 'Premium Bear Jerky', 
     'The original classic. Tough, chewy, and tastes vaguely of trash bags and pine needles.', 
     45.00, '4oz', 'https://tahoebearjerky.com/bear_with_jerky.png', 'sold_out', 'SOLD OUT', 1),
    
    ('Spicy Lynx Jerky', 'spicy-lynx-jerky', 'Spicy Lynx Jerky',
     'Elusive flavor for the elusive palate. Catches you by surprise.',
     55.00, '3oz', 'https://tahoebearjerky.com/lynx_with_jerky.png', 'coming_soon', 'COMING SOON', 2),
    
    ('Coyote Snack Sticks', 'coyote-snack-sticks', 'Coyote Snack Sticks',
     'Lean, mean, and howlin'' with flavor. Best enjoyed under a full moon.',
     35.00, '6oz', 'https://tahoebearjerky.com/coyote_with_sign.png', 'seasonal', 'SEASONAL', 3)
ON CONFLICT (slug) DO NOTHING;
