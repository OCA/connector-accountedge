# -*- encoding: utf-8 -*-
###############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2010 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm


class hr_expense_line(orm.Model):
    _inherit = 'hr.expense.line'

    def get_tax_id(self, cr, uid, product_id, partner_id, context=None):
        """Get the automatic value of the tax id field."""
        product = self.pool.get('product.product').browse(cr, uid, product_id)
        purch_tax = product.product_tmpl_id.supplier_taxes_id

        if purch_tax:
            # Use the default purchase tax set on the product
            defaut_tax = purch_tax[0]

            # Get the fiscal position of the supplier
            supplier = self.pool.get('res.partner').browse(
                cr, uid, partner_id, context=context
            )
            acc_pos = supplier.property_account_position

            # Apply the fiscal position mapping rules
            if acc_pos.tax_ids:
                for tax in acc_pos.tax_ids:
                    if tax.tax_src_id == defaut_tax:
                        defaut_tax = tax.tax_dest_id
                        break
            return defaut_tax.id

        return None

    def create(self, cr, user, vals, context=None):
        """Overwrite the create() function to automatically set the default
        supplier tax since regular employees cannot access this field.
        """
        vals['tax_id'] = self.get_tax_id(
            cr, user, vals['product_id'], vals['partner_id'], context=context,
        )
        return super(hr_expense_line, self).create(cr, user, vals, context)

    def onchange_product_id(self, cr, uid, ids, product_id, uom_id,
                            employee_id, context=None):
        if product_id:
            parent_h_e_l = super(hr_expense_line, self)
            values = parent_h_e_l.onchange_product_id(
                cr, uid, ids, product_id, uom_id, employee_id, context=context
            )
        else:
            values = {}

        for line in self.browse(cr, uid, ids, context=context):
            if line.name:
                tax_id = self.get_tax_id(
                    cr, uid, product_id, line.partner_id.id, context=context
                )
                values['value'].update({
                    'tax_id': tax_id,
                })
        return values

    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        values = {'value': {}}
        for line in self.browse(cr, uid, ids, context=context):
            tax_id = self.get_tax_id(
                cr, uid, line.product_id.id, partner_id, context=context
            )
            values['value'].update({
                'tax_id': tax_id,
            })
        return values

    _columns = {
        'tax_id': fields.many2one(
            'account.tax', 'Tax', domain=[('type_tax_use', '=', 'purchase')],
        ),
        'partner_id': fields.many2one(
            'res.partner', 'Supplier', required=True,
        ),
    }
