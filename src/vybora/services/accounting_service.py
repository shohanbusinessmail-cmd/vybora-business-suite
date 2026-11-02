"""Accounting service: persist balanced journal entries, ledger and trial balance.

post() must be called inside the caller's write transaction so the journal and its
source business document commit (or roll back) together.
"""

from __future__ import annotations

import sqlite3

from vybora.data.db import Database
from vybora.data.sequences import next_document_number
from vybora.domain.accounting import JournalEntry, JournalLine


class AccountingService:
    def __init__(self, db: Database):
        self.db = db

    def post(self, conn: sqlite3.Connection, entry: JournalEntry, *, user_id: int | None) -> int:
        entry.validate()  # raises if unbalanced / invalid
        entry_no = next_document_number(conn, "journal")
        cur = conn.execute(
            "INSERT INTO journal_entries (entry_no, date, source_type, source_id, memo, user_id) "
            "VALUES (?,?,?,?,?,?)",
            (entry_no, entry.date, entry.source_type, entry.source_id, entry.memo, user_id),
        )
        entry_id = cur.lastrowid
        for ln in entry.lines:
            conn.execute(
                "INSERT INTO journal_lines (entry_id, account_code, debit, credit, party_type, party_id) "
                "VALUES (?,?,?,?,?,?)",
                (entry_id, ln.account_code, ln.debit, ln.credit, ln.party_type, ln.party_id),
            )
        return entry_id

    def post_lines(
        self,
        conn: sqlite3.Connection,
        *,
        date: str,
        source_type: str,
        source_id: int | None,
        memo: str,
        lines: list[JournalLine],
        user_id: int | None,
    ) -> int:
        return self.post(
            conn, JournalEntry(date, source_type, source_id, memo, lines), user_id=user_id
        )

    def account_balance(self, code: str, *, upto: str | None = None) -> int:
        """Net balance (debit - credit) for an account."""
        if upto:
            row = self.db.query_one(
                """SELECT COALESCE(SUM(jl.debit),0)-COALESCE(SUM(jl.credit),0) AS bal
                   FROM journal_lines jl JOIN journal_entries je ON je.id=jl.entry_id
                   WHERE jl.account_code=? AND je.date<=?""",
                (code, upto),
            )
        else:
            row = self.db.query_one(
                "SELECT COALESCE(SUM(debit),0)-COALESCE(SUM(credit),0) AS bal "
                "FROM journal_lines WHERE account_code=?",
                (code,),
            )
        return int(row["bal"]) if row else 0

    def trial_balance(self, *, upto: str | None = None) -> list[dict]:
        sql = """SELECT a.code, a.name_bn, a.type,
                        COALESCE(SUM(jl.debit),0) AS debit, COALESCE(SUM(jl.credit),0) AS credit
                 FROM accounts a LEFT JOIN journal_lines jl ON jl.account_code=a.code
                 LEFT JOIN journal_entries je ON je.id=jl.entry_id """
        params: tuple = ()
        if upto:
            sql += "WHERE je.date<=? OR je.date IS NULL "
            params = (upto,)
        sql += "GROUP BY a.code ORDER BY a.code"
        rows = self.db.query(sql, params)
        out = []
        for r in rows:
            net = int(r["debit"]) - int(r["credit"])
            out.append(
                {
                    "code": r["code"],
                    "name_bn": r["name_bn"],
                    "type": r["type"],
                    "debit": max(net, 0),
                    "credit": max(-net, 0),
                }
            )
        return out

    def trial_balance_totals(self, *, upto: str | None = None) -> tuple[int, int]:
        tb = self.trial_balance(upto=upto)
        return sum(r["debit"] for r in tb), sum(r["credit"] for r in tb)

    def general_ledger(
        self, code: str, *, date_from: str | None = None, date_to: str | None = None
    ) -> list[dict]:
        sql = """SELECT je.date, je.entry_no, je.memo, je.source_type, je.source_id,
                        jl.debit, jl.credit
                 FROM journal_lines jl JOIN journal_entries je ON je.id=jl.entry_id
                 WHERE jl.account_code=?"""
        params: list = [code]
        if date_from:
            sql += " AND je.date>=?"
            params.append(date_from)
        if date_to:
            sql += " AND je.date<=?"
            params.append(date_to)
        sql += " ORDER BY je.date, je.id"
        rows = self.db.query(sql, tuple(params))
        running = 0
        out = []
        for r in rows:
            running += int(r["debit"]) - int(r["credit"])
            out.append({**dict(r), "balance": running})
        return out

    def party_balance(self, party_type: str, party_id: int, account_code: str) -> int:
        row = self.db.query_one(
            """SELECT COALESCE(SUM(debit),0)-COALESCE(SUM(credit),0) AS bal
               FROM journal_lines WHERE party_type=? AND party_id=? AND account_code=?""",
            (party_type, party_id, account_code),
        )
        return int(row["bal"]) if row else 0
