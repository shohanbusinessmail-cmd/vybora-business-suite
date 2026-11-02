-- Vybora Business Suite — initial schema (version 1)
-- Money: INTEGER poisha (1 BDT = 100). Quantity: INTEGER milli-units (x1000).
-- Timestamps: TEXT ISO-8601 UTC. All financial balances derive from transactions.

-- ============ CORE ============
CREATE TABLE businesses (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT NOT NULL DEFAULT '',
    owner_name TEXT NOT NULL DEFAULT '',
    address TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    logo_path TEXT,
    business_type TEXT NOT NULL DEFAULT 'retail',
    invoice_footer TEXT NOT NULL DEFAULT 'ধন্যবাদ! আবার আসবেন।',
    currency TEXT NOT NULL DEFAULT 'BDT',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
INSERT INTO businesses (id) VALUES (1);

CREATE TABLE business_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
INSERT INTO business_settings (key, value) VALUES
    ('digit_mode', 'bengali'),
    ('date_format', 'dd/mm/yyyy'),
    ('decimal_places', '2'),
    ('thousand_separator', '1'),
    ('currency_prefix', '1'),
    ('tax_mode', 'none'),
    ('tax_rate_bp', '0'),
    ('tax_recoverable', '1'),
    ('allow_negative_stock', '0'),
    ('backup_frequency', 'daily'),
    ('backup_retention', '14'),
    ('backup_dir', ''),
    ('idle_lock_minutes', '15'),
    ('support_contact', '');

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT ''
);
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE
);
CREATE TABLE role_permissions (
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);
CREATE TABLE user_roles (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    details_json TEXT
);
CREATE INDEX idx_audit_ts ON audit_logs(ts);
CREATE INDEX idx_audit_user ON audit_logs(user_id);

-- ============ PRODUCTS & INVENTORY ============
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1))
);
CREATE TABLE brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1))
);
CREATE TABLE units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    symbol TEXT NOT NULL DEFAULT '',
    allows_fraction INTEGER NOT NULL DEFAULT 0 CHECK (allows_fraction IN (0,1))
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sku TEXT NOT NULL UNIQUE,
    category_id INTEGER REFERENCES categories(id),
    brand_id INTEGER REFERENCES brands(id),
    unit_id INTEGER NOT NULL REFERENCES units(id),
    purchase_price INTEGER NOT NULL DEFAULT 0 CHECK (purchase_price >= 0),
    selling_price INTEGER NOT NULL DEFAULT 0 CHECK (selling_price >= 0),
    wholesale_price INTEGER NOT NULL DEFAULT 0 CHECK (wholesale_price >= 0),
    min_stock_qty INTEGER NOT NULL DEFAULT 0 CHECK (min_stock_qty >= 0),
    stock_qty INTEGER NOT NULL DEFAULT 0,
    stock_value INTEGER NOT NULL DEFAULT 0,
    last_avg_cost INTEGER NOT NULL DEFAULT 0 CHECK (last_avg_cost >= 0),
    description TEXT NOT NULL DEFAULT '',
    image_path TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_active ON products(is_active);

CREATE TABLE barcodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    barcode TEXT NOT NULL UNIQUE
);
CREATE INDEX idx_barcodes_product ON barcodes(product_id);

CREATE TABLE product_price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    field TEXT NOT NULL,
    old_value INTEGER NOT NULL,
    new_value INTEGER NOT NULL,
    changed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    user_id INTEGER REFERENCES users(id)
);

CREATE TABLE batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    batch_no TEXT NOT NULL,
    manufactured_on TEXT,
    expires_on TEXT,
    qty INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    UNIQUE (product_id, batch_no)
);
CREATE INDEX idx_batches_expiry ON batches(expires_on);

CREATE TABLE stock_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    batch_id INTEGER REFERENCES batches(id),
    qty_delta INTEGER NOT NULL,
    value_delta INTEGER NOT NULL,
    reason TEXT NOT NULL CHECK (reason IN ('opening','purchase','sale','sale_return','purchase_return','adjustment','write_off','reversal')),
    source_type TEXT NOT NULL,
    source_id INTEGER,
    user_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    note TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_movements_product ON stock_movements(product_id, created_at);
CREATE INDEX idx_movements_source ON stock_movements(source_type, source_id);

CREATE TABLE stock_adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    qty_delta INTEGER NOT NULL,
    value_delta INTEGER NOT NULL,
    reason TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    user_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    journal_id INTEGER
);

-- ============ PARTIES ============
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    mobile TEXT,
    address TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    opening_balance INTEGER NOT NULL DEFAULT 0 CHECK (opening_balance >= 0),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX idx_customers_name ON customers(name);
CREATE INDEX idx_customers_mobile ON customers(mobile);

CREATE TABLE suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    mobile TEXT,
    address TEXT NOT NULL DEFAULT '',
    business_info TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    opening_balance INTEGER NOT NULL DEFAULT 0 CHECK (opening_balance >= 0),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX idx_suppliers_name ON suppliers(name);
CREATE INDEX idx_suppliers_mobile ON suppliers(mobile);

CREATE TABLE customer_advances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    amount INTEGER NOT NULL CHECK (amount > 0),
    remaining INTEGER NOT NULL CHECK (remaining >= 0),
    source_payment_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE supplier_advances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    amount INTEGER NOT NULL CHECK (amount > 0),
    remaining INTEGER NOT NULL CHECK (remaining >= 0),
    source_payment_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- ============ SALES ============
CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    invoice_no TEXT NOT NULL UNIQUE,
    customer_id INTEGER REFERENCES customers(id),
    date TEXT NOT NULL,
    subtotal INTEGER NOT NULL CHECK (subtotal >= 0),
    discount INTEGER NOT NULL DEFAULT 0 CHECK (discount >= 0),
    tax INTEGER NOT NULL DEFAULT 0 CHECK (tax >= 0),
    total INTEGER NOT NULL CHECK (total >= 0),
    paid INTEGER NOT NULL DEFAULT 0 CHECK (paid >= 0),
    due INTEGER NOT NULL DEFAULT 0 CHECK (due >= 0),
    payment_method TEXT NOT NULL DEFAULT 'cash',
    status TEXT NOT NULL DEFAULT 'posted' CHECK (status IN ('posted','reversed')),
    user_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    note TEXT NOT NULL DEFAULT '',
    CHECK (paid + due = total)
);
CREATE INDEX idx_sales_date ON sales(date);
CREATE INDEX idx_sales_customer ON sales(customer_id);
CREATE INDEX idx_sales_status ON sales(status);

CREATE TABLE sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL REFERENCES sales(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    batch_id INTEGER REFERENCES batches(id),
    qty INTEGER NOT NULL CHECK (qty > 0),
    unit_price INTEGER NOT NULL CHECK (unit_price >= 0),
    discount INTEGER NOT NULL DEFAULT 0 CHECK (discount >= 0),
    line_total INTEGER NOT NULL CHECK (line_total >= 0),
    tax INTEGER NOT NULL DEFAULT 0 CHECK (tax >= 0),
    cogs INTEGER NOT NULL DEFAULT 0 CHECK (cogs >= 0),
    returned_qty INTEGER NOT NULL DEFAULT 0 CHECK (returned_qty >= 0)
);
CREATE INDEX idx_sale_items_sale ON sale_items(sale_id);
CREATE INDEX idx_sale_items_product ON sale_items(product_id);

CREATE TABLE sale_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL REFERENCES sales(id),
    amount INTEGER NOT NULL CHECK (amount > 0),
    method TEXT NOT NULL,
    account_code TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE sale_returns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    return_no TEXT NOT NULL UNIQUE,
    sale_id INTEGER NOT NULL REFERENCES sales(id),
    date TEXT NOT NULL,
    reason TEXT NOT NULL,
    refund_amount INTEGER NOT NULL DEFAULT 0 CHECK (refund_amount >= 0),
    credit_amount INTEGER NOT NULL DEFAULT 0 CHECK (credit_amount >= 0),
    status TEXT NOT NULL DEFAULT 'posted' CHECK (status IN ('posted','reversed')),
    user_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE sale_return_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    return_id INTEGER NOT NULL REFERENCES sale_returns(id),
    sale_item_id INTEGER NOT NULL REFERENCES sale_items(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    qty INTEGER NOT NULL CHECK (qty > 0),
    refund_value INTEGER NOT NULL DEFAULT 0 CHECK (refund_value >= 0),
    restock_value INTEGER NOT NULL DEFAULT 0 CHECK (restock_value >= 0),
    is_damaged INTEGER NOT NULL DEFAULT 0 CHECK (is_damaged IN (0,1))
);

-- ============ PURCHASES ============
CREATE TABLE purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    purchase_no TEXT NOT NULL UNIQUE,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    date TEXT NOT NULL,
    subtotal INTEGER NOT NULL CHECK (subtotal >= 0),
    discount INTEGER NOT NULL DEFAULT 0 CHECK (discount >= 0),
    additional_cost INTEGER NOT NULL DEFAULT 0 CHECK (additional_cost >= 0),
    tax INTEGER NOT NULL DEFAULT 0 CHECK (tax >= 0),
    total INTEGER NOT NULL CHECK (total >= 0),
    paid INTEGER NOT NULL DEFAULT 0 CHECK (paid >= 0),
    due INTEGER NOT NULL DEFAULT 0 CHECK (due >= 0),
    payment_method TEXT NOT NULL DEFAULT 'cash',
    reference TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'posted' CHECK (status IN ('posted','reversed')),
    user_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    CHECK (paid + due = total)
);
CREATE INDEX idx_purchases_date ON purchases(date);
CREATE INDEX idx_purchases_supplier ON purchases(supplier_id);

CREATE TABLE purchase_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL REFERENCES purchases(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    batch_id INTEGER REFERENCES batches(id),
    qty INTEGER NOT NULL CHECK (qty > 0),
    unit_cost INTEGER NOT NULL CHECK (unit_cost >= 0),
    discount INTEGER NOT NULL DEFAULT 0 CHECK (discount >= 0),
    additional_cost INTEGER NOT NULL DEFAULT 0 CHECK (additional_cost >= 0),
    line_total INTEGER NOT NULL CHECK (line_total >= 0),
    tax INTEGER NOT NULL DEFAULT 0 CHECK (tax >= 0),
    returned_qty INTEGER NOT NULL DEFAULT 0 CHECK (returned_qty >= 0)
);
CREATE INDEX idx_purchase_items_purchase ON purchase_items(purchase_id);
CREATE INDEX idx_purchase_items_product ON purchase_items(product_id);

CREATE TABLE purchase_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL REFERENCES purchases(id),
    amount INTEGER NOT NULL CHECK (amount > 0),
    method TEXT NOT NULL,
    account_code TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE purchase_returns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    return_no TEXT NOT NULL UNIQUE,
    purchase_id INTEGER NOT NULL REFERENCES purchases(id),
    date TEXT NOT NULL,
    reason TEXT NOT NULL,
    credit_amount INTEGER NOT NULL DEFAULT 0 CHECK (credit_amount >= 0),
    refund_amount INTEGER NOT NULL DEFAULT 0 CHECK (refund_amount >= 0),
    status TEXT NOT NULL DEFAULT 'posted' CHECK (status IN ('posted','reversed')),
    user_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE purchase_return_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    return_id INTEGER NOT NULL REFERENCES purchase_returns(id),
    purchase_item_id INTEGER NOT NULL REFERENCES purchase_items(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    qty INTEGER NOT NULL CHECK (qty > 0),
    cost_value INTEGER NOT NULL DEFAULT 0 CHECK (cost_value >= 0),
    tax_value INTEGER NOT NULL DEFAULT 0 CHECK (tax_value >= 0)
);

-- ============ PAYMENTS & ALLOCATIONS ============
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    party_type TEXT NOT NULL CHECK (party_type IN ('customer','supplier')),
    party_id INTEGER NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('in','out')),
    amount INTEGER NOT NULL CHECK (amount > 0),
    method TEXT NOT NULL,
    account_code TEXT NOT NULL,
    date TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    user_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    journal_id INTEGER
);
CREATE INDEX idx_payments_party ON payments(party_type, party_id);

CREATE TABLE payment_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id INTEGER NOT NULL REFERENCES payments(id),
    document_type TEXT NOT NULL CHECK (document_type IN ('sale','purchase')),
    document_id INTEGER NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0)
);
CREATE INDEX idx_alloc_payment ON payment_allocations(payment_id);
CREATE INDEX idx_alloc_doc ON payment_allocations(document_type, document_id);

CREATE TABLE advance_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    advance_id INTEGER NOT NULL,
    advance_type TEXT NOT NULL CHECK (advance_type IN ('customer','supplier')),
    document_type TEXT NOT NULL,
    document_id INTEGER NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0)
);

-- ============ FINANCIAL ============
CREATE TABLE accounts (
    code TEXT PRIMARY KEY,
    name_bn TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('ASSET','LIABILITY','EQUITY','INCOME','COGS','EXPENSE')),
    is_system INTEGER NOT NULL DEFAULT 1 CHECK (is_system IN (0,1)),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1))
);
CREATE TABLE journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_no TEXT NOT NULL UNIQUE,
    date TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_id INTEGER,
    memo TEXT NOT NULL DEFAULT '',
    user_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    reversed_entry_id INTEGER REFERENCES journal_entries(id)
);
CREATE INDEX idx_journal_source ON journal_entries(source_type, source_id);
CREATE INDEX idx_journal_date ON journal_entries(date);

CREATE TABLE journal_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL REFERENCES journal_entries(id),
    account_code TEXT NOT NULL REFERENCES accounts(code),
    debit INTEGER NOT NULL DEFAULT 0 CHECK (debit >= 0),
    credit INTEGER NOT NULL DEFAULT 0 CHECK (credit >= 0),
    party_type TEXT CHECK (party_type IN ('customer','supplier')),
    party_id INTEGER,
    CHECK ((debit > 0) <> (credit > 0))
);
CREATE INDEX idx_journal_lines_account ON journal_lines(account_code);
CREATE INDEX idx_journal_lines_entry ON journal_lines(entry_id);
CREATE INDEX idx_journal_lines_party ON journal_lines(party_type, party_id);

CREATE TABLE expense_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    account_code TEXT NOT NULL UNIQUE REFERENCES accounts(code),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1))
);
CREATE TABLE expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    date TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES expense_categories(id),
    amount INTEGER NOT NULL CHECK (amount > 0),
    account_code TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    reference TEXT NOT NULL DEFAULT '',
    receipt_path TEXT,
    status TEXT NOT NULL DEFAULT 'posted' CHECK (status IN ('posted','reversed')),
    user_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    journal_id INTEGER
);
CREATE INDEX idx_expenses_date ON expenses(date);

CREATE TABLE other_income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    date TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    account_code TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    reference TEXT NOT NULL DEFAULT '',
    kind TEXT NOT NULL CHECK (kind IN ('income','loan','capital','transfer')),
    status TEXT NOT NULL DEFAULT 'posted' CHECK (status IN ('posted','reversed')),
    user_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    journal_id INTEGER
);

CREATE TABLE cash_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opened_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    closed_at TEXT,
    opening_cash INTEGER NOT NULL DEFAULT 0 CHECK (opening_cash >= 0),
    expected_cash INTEGER,
    counted_cash INTEGER,
    variance INTEGER,
    notes TEXT NOT NULL DEFAULT '',
    opened_by INTEGER REFERENCES users(id),
    closed_by INTEGER REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','closed'))
);

CREATE TABLE financial_periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    is_closed INTEGER NOT NULL DEFAULT 0 CHECK (is_closed IN (0,1))
);

-- ============ OPERATIONS ============
CREATE TABLE payment_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name_bn TEXT NOT NULL,
    account_code TEXT NOT NULL REFERENCES accounts(code),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1))
);
CREATE TABLE sequences (
    name TEXT PRIMARY KEY,
    prefix TEXT NOT NULL,
    next_value INTEGER NOT NULL DEFAULT 1,
    padding INTEGER NOT NULL DEFAULT 5
);
CREATE TABLE backup_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL DEFAULT 0,
    sha256 TEXT NOT NULL DEFAULT '',
    kind TEXT NOT NULL CHECK (kind IN ('manual','auto','pre_restore')),
    status TEXT NOT NULL CHECK (status IN ('ok','failed')),
    verified INTEGER NOT NULL DEFAULT 0 CHECK (verified IN (0,1)),
    user_id INTEGER REFERENCES users(id)
);
CREATE TABLE license_metadata (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    license_id TEXT,
    business_name TEXT,
    business_id TEXT,
    edition TEXT,
    issued_at TEXT,
    machine_fingerprint TEXT,
    activated_at TEXT,
    license_path TEXT,
    status TEXT NOT NULL DEFAULT 'unlicensed'
);
INSERT INTO license_metadata (id) VALUES (1);

CREATE TABLE reprint_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL REFERENCES sales(id),
    user_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    format TEXT NOT NULL DEFAULT 'a4'
);

-- ============ SEED DATA ============
INSERT INTO units (name, symbol, allows_fraction) VALUES
    ('পিস', 'pcs', 0), ('কেজি', 'kg', 1), ('গ্রাম', 'g', 1),
    ('লিটার', 'L', 1), ('মিলিলিটার', 'mL', 1), ('প্যাকেট', 'pkt', 0),
    ('বক্স', 'box', 0), ('ডজন', 'dozen', 0), ('কার্টন', 'ctn', 0), ('মিটার', 'm', 1);

INSERT INTO roles (name, description) VALUES
    ('owner', 'মালিক / প্রশাসনিক'), ('manager', 'ম্যানেজার'),
    ('cashier', 'ক্যাশিয়ার'), ('inventory', 'মজুত ব্যবস্থাপক'), ('accountant', 'হিসাবরক্ষক');

INSERT INTO permissions (code) VALUES
    ('sales.view'), ('sales.create'), ('sales.cancel'), ('sales.return'),
    ('costs.view'), ('profits.view'), ('products.manage'), ('stock.manage'), ('stock.adjust'),
    ('customers.manage'), ('suppliers.manage'), ('payments.record'), ('purchases.manage'),
    ('expenses.manage'), ('reports.view'), ('users.manage'), ('backup.manage'),
    ('backup.restore'), ('settings.manage'), ('audit.view'), ('license.manage');

-- owner: all permissions
INSERT INTO role_permissions (role_id, permission_id)
    SELECT (SELECT id FROM roles WHERE name='owner'), id FROM permissions;
-- manager: all except users.manage, license.manage
INSERT INTO role_permissions (role_id, permission_id)
    SELECT (SELECT id FROM roles WHERE name='manager'), id FROM permissions
    WHERE code NOT IN ('users.manage','license.manage');
-- cashier
INSERT INTO role_permissions (role_id, permission_id)
    SELECT (SELECT id FROM roles WHERE name='cashier'), id FROM permissions
    WHERE code IN ('sales.view','sales.create','sales.return','payments.record','customers.manage');
-- inventory
INSERT INTO role_permissions (role_id, permission_id)
    SELECT (SELECT id FROM roles WHERE name='inventory'), id FROM permissions
    WHERE code IN ('products.manage','stock.manage','stock.adjust','purchases.manage','suppliers.manage');
-- accountant
INSERT INTO role_permissions (role_id, permission_id)
    SELECT (SELECT id FROM roles WHERE name='accountant'), id FROM permissions
    WHERE code IN ('payments.record','expenses.manage','reports.view','costs.view','profits.view','sales.view');

INSERT INTO sequences (name, prefix, next_value, padding) VALUES
    ('invoice', 'INV-', 1, 5), ('purchase', 'PUR-', 1, 5),
    ('sale_return', 'SRN-', 1, 5), ('purchase_return', 'PRN-', 1, 5),
    ('journal', 'JRN-', 1, 6), ('customer', 'CUS-', 1, 4), ('supplier', 'SUP-', 1, 4);
