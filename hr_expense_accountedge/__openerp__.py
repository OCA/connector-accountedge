# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.·····
#
##############################################################################

{
    "name": "Harmonization of expenses with AccountEdge",
    "version": "1.0",
    "author": "Savoir-faire Linux",
    "website": "http://www.savoirfairelinux.com",
    "category": "Human Resources",
    "description": """
        This module generates the csv reports for the exportation
        of expenses in AccountEdge.
        It also modifies the workflow of the expenses.
    """,
    "depends": [
        'l10n_ca',
        'hr_employee_accountedge',
        'hr_expense_line_supplier_tax',
        'hr_expense_line_account',
        'hr_expense_line_sequence',
        'account_account_halftax',
        'account_tax_accountedge'
        ],
    "data": [
        'hr_expense_accountedge.xml',
        'security/ir_rule.xml',
    ],
    "installable": True,
}
