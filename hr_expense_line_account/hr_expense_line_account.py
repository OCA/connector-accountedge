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

from osv import orm, fields


class hr_expense_line(orm.Model):
    _inherit = 'hr.expense.line'
    _columns = {
        'account_id': fields.many2one('account.account', 'Financial Account'),
    }

    def get_account_id(self, cr, uid, product_id, context=None):
        """Get the automatic value of the account_id field."""
        if not product_id:
            return None
        # Retrieve the product
        product_pool = self.pool['product.product']
        product = product_pool.browse(cr, uid, product_id, context=context)
        # Product -> Accounting -> Expense account
        exp_acc = product.product_tmpl_id.property_account_expense

        # If the field is empty
        if not exp_acc:
            # Find the product's 'Parent category'
            parent_category = product.product_tmpl_id.categ_id
            # Try to find the expense account of the parent category
            exp_acc = parent_category.property_account_expense_categ

        if exp_acc:
            return exp_acc.id

        return None

    def create(self, cr, user, vals, context=None):
        """Overwrite the create() function to automatically set the default
        account id since regular employees cannot access this field.
        """
        vals['account_id'] = self.get_account_id(
            cr, user, vals['product_id'], context=context
        )
        return super(hr_expense_line, self).create(cr, user, vals, context)

    def onchange_product_id(
            self, cr, uid, ids, product_id, uom_id, employee_id, context=None):
        res = super(hr_expense_line, self).onchange_product_id(
            cr, uid, ids, product_id, uom_id, employee_id, context=context
        )
        for id in ids:
            account_id = self.get_account_id(cr, uid, product_id, context)
            res['value']['account_id'] = account_id
        return res
