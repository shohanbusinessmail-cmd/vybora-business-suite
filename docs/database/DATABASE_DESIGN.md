# Database Design — Vybora Business Suite

Engine: SQLite ≥ 3.40 (stdlib). File: `%LOCALAPPDATA%/Vybora/data/vybora.db` (Windows).
Pragmas per connection: `journal_mode=WAL`, `foreign_keys=ON`, `synchronous=FULL`,
`busy_timeout=5000`, `temp_store=MEMORY`. Money = INTEGER poisha; qty = INTEGER
milli-units; timestamps = TEXT ISO-8601 UTC; ids = INTEGER PK AUTOINCREMENT unless noted.

## Table groups

### Core
- `businesses` (id=1 singleton, name, owner_name, address, phone, email, logo_path,
  business_type, invoice_footer, currency='BDT')
- `business_settings` (key TEXT PK, value TEXT) — digit mode, date format, tax mode/
  rate, negative-stock policy, backup schedule/dir/retention, support contact
- `users` (id, username UNIQUE, full_name, password_hash, is_active, created_at,
  failed_attempts, locked_until)
- `roles` (id, name UNIQUE, description); `permissions` (id, code UNIQUE);
  `role_permissions` (role_id, permission_id); `user_roles` (user_id, role_id)
- `audit_logs` (id, ts, user_id, action, entity_type, entity_id, details_json)
- `schema_migrations` (version INTEGER PK, name, applied_at)

### Products & inventory
- `categories` (id, name UNIQUE, is_active)
- `brands` (id, name UNIQUE, is_active)
- `units` (id, name UNIQUE, symbol, allows_fraction INTEGER 0/1)
- `products` (id, name, sku UNIQUE, category_id FK, brand_id FK, unit_id FK,
  purchase_price, selling_price, wholesale_price, min_stock_qty, stock_qty,
  stock_value, last_avg_cost, description, image_path, is_active,
  allow_negative_stock_override?, created_at, updated_at)
  CHECKs: prices ≥ 0, stock_value ≥ 0 unless negative policy, timestamps.
- `barcodes` (id, product_id FK, barcode UNIQUE)
- `product_price_history` (id, product_id, field, old_value, new_value, changed_at, user_id)
- `batches` (id, product_id FK, batch_no, manufactured_on, expires_on, qty, created_at,
  UNIQUE(product_id, batch_no))
- `stock_movements` (id, product_id FK, batch_id FK NULL, qty_delta, value_delta,
  reason TEXT CHECK in (opening,purchase,sale,sale_return,purchase_return,adjustment,
  write_off,reversal), source_type, source_id, user_id, created_at, note)
- `stock_adjustments` (id, request_id UNIQUE, product_id, qty_delta, reason, note,
  user_id, created_at, journal_id FK)

### Parties
- `customers` (id, code UNIQUE, name, mobile, address, notes, opening_balance,
  is_active, created_at, updated_at)
- `suppliers` (id, code UNIQUE, name, mobile, address, business_info, notes,
  opening_balance, is_active, created_at, updated_at)
- `customer_advances` (id, customer_id FK, amount, remaining, source_payment_id,
  created_at) — remaining derived-check via allocations
- `supplier_advances` (id, supplier_id FK, amount, remaining, source_payment_id, created_at)

### Sales & purchases
- `sales` (id, request_id UNIQUE, invoice_no UNIQUE, customer_id FK NULL, date,
  subtotal, discount, tax, total, paid, due, payment_method, status CHECK
  (posted,reversed), user_id, created_at, note)
- `sale_items` (id, sale_id FK, product_id FK, batch_id FK NULL, qty, unit_price,
  discount, line_total, tax, cogs, returned_qty DEFAULT 0)
- `sale_payments` (id, sale_id FK, amount, method, account_code, created_at)
- `sale_returns` (id, request_id UNIQUE, return_no UNIQUE, sale_id FK, date, reason,
  refund_amount, credit_amount, status, user_id, created_at)
- `sale_return_items` (id, return_id FK, sale_item_id FK, product_id, qty,
  refund_value, restock_value, is_damaged)
- `purchases` (id, request_id UNIQUE, purchase_no UNIQUE, supplier_id FK, date,
  subtotal, discount, additional_cost, tax, total, paid, due, payment_method,
  reference, status, user_id, created_at)
- `purchase_items` (id, purchase_id FK, product_id FK, batch_id FK NULL, qty,
  unit_cost, discount, additional_cost, line_total, tax, returned_qty DEFAULT 0)
- `purchase_payments` (id, purchase_id FK, amount, method, account_code, created_at)
- `purchase_returns` (id, request_id UNIQUE, return_no UNIQUE, purchase_id FK, date,
  reason, credit_amount, refund_amount, status, user_id, created_at)
- `purchase_return_items` (id, return_id FK, purchase_item_id FK, product_id, qty,
  cost_value, tax_value)

### Payments & allocations
- `payments` (id, request_id UNIQUE, party_type CHECK(customer,supplier), party_id,
  direction CHECK(in,out), amount, method, account_code, date, note, user_id,
  created_at, journal_id)
- `payment_allocations` (id, payment_id FK, document_type CHECK(sale,purchase),
  document_id, amount, CHECK amount>0)
- `advance_applications` (id, advance_id, advance_type, document_type, document_id, amount)

### Financial
- `accounts` (code TEXT PK, name_bn, type CHECK(ASSET,LIABILITY,EQUITY,INCOME,COGS,
  EXPENSE), is_system, is_active)
- `journal_entries` (id, entry_no UNIQUE, date, source_type, source_id, memo,
  user_id, created_at, reversed_entry_id FK NULL)
- `journal_lines` (id, entry_id FK, account_code FK, debit INTEGER DEFAULT 0,
  credit INTEGER DEFAULT 0, party_type NULL, party_id NULL,
  CHECK(debit>=0 AND credit>=0 AND (debit>0)<>(credit>0)))
- `expense_categories` (id, name UNIQUE, account_code FK UNIQUE, is_active)
- `expenses` (id, request_id UNIQUE, date, category_id FK, amount, account_code,
  description, reference, receipt_path, status, user_id, created_at, journal_id)
- `other_income` (id, request_id UNIQUE, date, amount, account_code, description,
  reference, kind CHECK(income,loan,capital,transfer), status, user_id, created_at, journal_id)
- `cash_sessions` (id, opened_at, closed_at NULL, opening_cash, expected_cash NULL,
  counted_cash NULL, variance NULL, notes, opened_by, closed_by NULL,
  status CHECK(open,closed))
- `financial_periods` (id, name, start_date, end_date, is_closed) — optional locking

### Operations
- `payment_methods` (id, code UNIQUE, name_bn, account_code FK, is_active)
- `sequences` (name TEXT PK, prefix, next_value INTEGER, padding)
- `backup_history` (id, created_at, path, size_bytes, sha256, kind CHECK(manual,auto,
  pre_restore), status CHECK(ok,failed), verified INTEGER, user_id)
- `license_metadata` (id=1, license_id, business_name, business_id, edition,
  issued_at, machine_fingerprint, activated_at, license_path, status)
- `reprint_history` (id, sale_id FK, user_id, created_at, format)

## Key indexes
products(name), products(sku), barcodes(barcode), customers(name,mobile),
suppliers(name,mobile), sales(date), sales(customer_id), sale_items(product_id),
purchases(date), purchases(supplier_id), stock_movements(product_id,created_at),
journal_lines(account_code), journal_entries(source_type,source_id),
payments(party_type,party_id), audit_logs(ts).

## Derived balances (never independently editable)
- Customer due = opening (journal) + Σ sale due portions − Σ collections allocated −
  Σ return credits + advance movements → computed from journal_lines tagged with
  party + document dues; cached `due` on sales is authoritative per-document and
  reconciled against AR subledger.
- Supplier payable = symmetric.
- Stock pool = products.stock_qty/stock_value, reconciled against Σ stock_movements.
- GL balances = Σ journal_lines by account.

## Migration policy
Ordered SQL files `NNNN_name.sql`, each applied in one transaction, recorded in
`schema_migrations`. App refuses to start on downgrade or checksum mismatch.
Migration failure rolls back fully; DB untouched. Backups recommended pre-migration
(auto pre-migration backup taken by the app).
