"""Composition root: wires services with their dependencies (dependency injection)."""

from __future__ import annotations

from vybora.data.db import Database
from vybora.services.accounting_service import AccountingService
from vybora.services.audit_service import AuditService
from vybora.services.auth_service import AuthService
from vybora.services.customer_service import CustomerService
from vybora.services.inventory_service import InventoryService
from vybora.services.product_service import ProductService
from vybora.services.settings_service import SettingsService
from vybora.services.supplier_service import SupplierService
from vybora.services.user_service import UserService


class Services:
    def __init__(self, db: Database):
        self.db = db
        self.audit = AuditService(db)
        self.accounting = AccountingService(db)
        self.settings = SettingsService(db, self.audit)
        self.auth = AuthService(db, self.audit)
        self.users = UserService(db, self.audit)
        self.products = ProductService(db, self.audit)
        self.inventory = InventoryService(db, self.audit, self.accounting)
        self.customers = CustomerService(db, self.audit, self.accounting)
        self.suppliers = SupplierService(db, self.audit, self.accounting)


def build_services(db: Database) -> Services:
    return Services(db)
