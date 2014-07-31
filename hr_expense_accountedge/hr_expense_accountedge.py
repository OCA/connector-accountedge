# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import base64

from datetime import datetime
from openerp.osv import orm, fields
from openerp.tools.translate import _


class hr_expense_expense(orm.Model):
    _inherit = 'hr.expense.expense'

    def _create_csv_report(self, cr, uid, ids, context=None):
        res = {}
        for expense in self.browse(cr, uid, ids, context=context):
            output = (
                expense.employee_id.name +
                "\r\n"
                "Employee\tCard ID\tDate\tVendor Invoice #\tAccount Number\t"
                "Amount\tDescription\tTax Code\tCurrency Code\tExchange Rate"
                "\r\n"
            )
            # Comment the previous line and uncomment the next one
            # if you want to import taxes with their amount, instead of their
            # code \tTax Code\tGST Amount\tPST/QST Amount\tCurrency Code\t
            # Exchange Rate\r\n"

            for l in expense.line_ids:
                taxes = self._compute_taxes(cr, uid, l, context)
                output += u"%s\t%s\t%s\t%s\t%s\t%.2f\t%s\t%s\t%s\t%.2f\r\n" % (
                    expense.employee_id.name,
                    expense.employee_id.supplier_id_accountedge,
                    datetime.today().strftime("%d-%m-%Y"),
                    l.expense_id.id,
                    l.account_id.code,
                    taxes['amount_before_tax'],
                    l.name,
                    (l.tax_id.tax_code_accountedge or '000'),
                    # Comment the previous line and uncomment the next two ones
                    # if you want to import taxes with their amount, instead of
                    # their code
                    # taxes['amount_gst'],
                    # taxes['amount_pst'],
                    (l.expense_id.currency_id.name or 'CAD'),
                    (float(l.expense_id.currency_id.rate) or '1.0')
                )

            byte_string = output.encode('utf-8-sig')
            res[id] = base64.encodestring(byte_string)

            self.write(cr, uid, ids, {'csv_file': res[id]}, context=context)
            self._add_attachment(cr, uid, id, byte_string, context)

        return True

    def _compute_taxes(self, cr, uid, expense_line, context={}):

        res = {
            'amount_before_tax': expense_line.total_amount,
            'amount_gst': 0.0,  # Goods and Services Tax, federal
            'amount_pst': 0.0,  # Provincial Sales Tax
        }

        tax = expense_line.tax_id
        if not tax.amount:
            return res

        # Divide tax per two?
        tax_factor = 1.0
        if expense_line.account_id.tax_halftax:
            tax_factor = 0.5

        if tax.child_ids:
            # TODO: the detection of the two taxes should be more reliable
            for child_tax in tax.child_ids:
                if 'TPS' in child_tax.name or 'GST' in child_tax.name:
                    res['amount_gst'] = float(child_tax.amount) * tax_factor
                else:
                    res['amount_pst'] = float(child_tax.amount) * tax_factor
        else:
            res['amount_gst'] = float(tax.amount)
        res['amount_before_tax'] = (
            expense_line.total_amount /
            (1 + res['amount_gst'] + res['amount_pst'])
        )
        res['amount_gst'] = res['amount_before_tax'] * res['amount_gst']
        res['amount_pst'] = res['amount_before_tax'] * res['amount_pst']
        return res

    def _add_attachment(self, cr, uid, ids, content, context={}):

        file_name = 'export_'+time.strftime('%Y%m%d_%H%M%S')+'.tsv'
        self.pool.get('ir.attachment').create(cr, uid, {
            'name': file_name,
            'datas': base64.encodestring(content),
            'datas_fname': file_name,
            'res_model': self._name,
            'res_id': ids,
            },
            context=context
        )
        return True

    def action_exported(self, cr, uid, ids, *args):
        if not len(ids):
            return False

        # Employee must have a recordID matching his supplier account
        # in Accountedge to generate an expense sheet
        for id in ids:
            this = self.browse(cr, uid, id)
            if not this.employee_id.supplier_id_accountedge:
                raise orm.except_orm(
                    _('Accountedge Supplier ID missing'),
                    _('Please add the Accountedge supplier ID on the '
                      'employee before exporting the sheet.')
                )
            self._create_csv_report(cr, uid, ids, {})
            self.write(cr, uid, ids, {'state': 'exported'})
        return True

    def action_imported(self, cr, uid, ids, *args):
        if not len(ids):
            return False
        for id in ids:
            self.write(cr, uid, ids, {'state': 'imported'})
        return True

    def _get_cur_account_manager(self, cr, uid, ids, field_name, arg, context):
        res = {}
        users_pool = self.pool['res.users']
        employee_pool = self.pool['hr.employee']
        for id in ids:
            emails = ''
            grp_ids = self.pool.get('res.groups').search(
                cr, uid, [
                    ('name', '=', u'Manager'),
                    ('category_id.name', '=', u'Accounting & Finance')
                ], context=context
            )
            usr_ids = users_pool.search(
                cr, uid, [('groups_id', '=', grp_ids[0])], context=context
            )
            usrs = users_pool.browse(cr, uid, usr_ids, context=context)

            for user in usrs:
                if user.user_email:
                    emails += user.user_email
                    emails += ','
                else:
                    empl_id = employee_pool.search(
                        cr, uid, [('login', '=', user.login)], context=context
                    )[0]
                    empl = employee_pool.browse(
                        cr, uid, empl_id, context=context
                    )
                    if empl.work_email:
                        emails += empl.work_email
                        emails += ','
            emails = emails[:-1]
            res[id] = emails
        return res

    _columns = {
        'manager': fields.function(
            _get_cur_account_manager, string='Manager', type='char',
            size=128, readonly=True
        ),
        'state': fields.selection(
            [
                ('draft', 'New'),
                ('confirm', 'Waiting Approval'),
                ('accepted', 'Approved'),
                ('exported', 'Exported'),
                ('imported', 'Imported'),
                ('cancelled', 'Refused'),
            ],
            'State',
            readonly=True,
            help="""\
When the expense request is created the state is 'Draft'.
It is confirmed by the user and request is sent to admin, the state is \
'Waiting Confirmation'.
If the admin accepts it, the state is 'Accepted'.
If the admin refuses it, the state is 'Refused'.
If a csv file has been generated for the expense request, the state is \
'Exported'.
If the expense request has been imported in AccountEdge, the state is \
'Imported'."""),
    }


class hr_expense_line(orm.Model):
    _inherit = 'hr.expense.line'

    def _get_parent_state(self, cr, uid, ids, field_name, arg, context):
        res = {}
        line_pool = self.pool['hr.expense.line']
        for expense_line in line_pool.browse(cr, uid, ids, context=context):
            res[expense_line.id] = expense_line.expense_id.state
        return res

    _columns = {
        'state': fields.function(
            _get_parent_state,
            string='Expense State',
            type='char',
            size=128,
            readonly=True,
        ),
    }
