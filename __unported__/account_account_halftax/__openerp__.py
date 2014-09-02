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
    "name": "Account tax halftax",
    "version": "1.0",
    "author": "Savoir-faire Linux",
    "website": "http://www.savoirfairelinux.com",
    "category": "Human Resources",
    "description": """
        This module adds a boolean to account.account called 'tax_halftax'.
        If this boolean is set to true, then the amount of the tax has to be
        divided by 2.
    """,
    "depends": ['account'],
    "data": [
        'account_account_halftax.xml',
    ],
    'installable': False,
}
