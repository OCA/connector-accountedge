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
    "name": "Supplier tax id on hr.expense.line",
    "version": "1.0",
    "author": "Savoir-faire Linux",
    "website": "http://www.savoirfairelinux.com",
    "category": "Human Resources",
    "description": """
        This module adds the supplier tax id field to hr.expense.line
    """,
    "depends": ['hr_expense', 'hr_expense_line_supplier'],
    "data": [
        'hr_expense_line_supplier_tax.xml',
    ],
    'installable': False,
}
