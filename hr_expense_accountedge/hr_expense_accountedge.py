# -*- encoding: utf-8 -*-
##############################################################################
#····
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import base64

from osv import osv, fields
from datetime import datetime


class hr_expense_expense(osv.osv):
    _inherit = 'hr.expense.expense'

    def _create_csv_report(self,cr,uid,ids,context={}):
        res = {}
        for id in ids:
            this    = self.browse(cr, uid, id)
            empl_id = self.pool.get('hr.employee').search(cr, uid, [('user_id','=', this.user_id.id)])
            empl    = self.pool.get('hr.employee').browse(cr, uid, empl_id)[0]

            output  = this.employee_id.name
            output += "\r\n"
            output += "Card ID\tDate\tVendor Invoice #\tAccount Number\tAmount\tDescription\
                        \tTax Code\tGST Amount\tPST/QST Amount\tCurrency Code\tExchange Rate\r\n"


            for l in this.line_ids:
                taxes = self._compute_taxes(cr,uid,l,context)
                output  += u"%s\t%s\t%s\t%s\t%.2f\t%s\t%s\t%.2f\t%.2f\t%s\t%.2f\r\n" % (
                        this.employee_id.supplier_id_accountedge,
                        datetime.strptime(l.date_value,"%Y-%m-%d").strftime("%m/%d/%Y"),
                        l.expense_id.id,
                        l.account_id.code,
                        taxes['amount_before_tax'],
                        l.name,
                        (l.tax_id.tax_code_accountedge or '000'),
                        taxes['amount_gst'],
                        taxes['amount_pst'],
                        (l.expense_id.currency_id.name or 'CAD'),
                        (float(l.expense_id.currency_id.rate) or '1.0'))

            byte_string = output.encode('utf-8-sig')
            res[id]     = base64.encodestring(byte_string)

            self.write(cr, uid, ids, {'csv_file':res[id]}, context=context)
            self._add_attachment(cr,uid,id,byte_string,context)

        return True


    def _compute_taxes(self,cr,uid,expense_line,context={}):

        res = {
                'amount_before_tax' : expense_line.total_amount,
                'amount_gst'        : 0.0,    # Goods and Services Tax, federal
                'amount_pst'        : 0.0     # Provincial Sales Tax
        }

        tax = expense_line.tax_id
        if not tax.amount:
            return res

        # Divide tax per two?
        tax_factor = 1.0
        if expense_line.account_id.tax_halftax:
            tax_factor = 0.5

        if tax.child_ids :
            for child_tax in tax.child_ids: # TODO: the detection of the two taxes should be more reliable
                if  'TPS' in child_tax.name or \
                    'GST' in child_tax.name:
                    res['amount_gst'] = float(child_tax.amount) * tax_factor
                else:
                    res['amount_pst'] = float(child_tax.amount) * tax_factor
        else:
            res['amount_gst'] = float(tax.amount)


        res['amount_before_tax']    = expense_line.total_amount / (1 + res['amount_gst'] + res['amount_pst'])
        res['amount_gst']           = res['amount_before_tax'] * res['amount_gst']
        res['amount_pst']           = res['amount_before_tax'] * res['amount_pst']

        return res



    def _add_attachment(self,cr,uid,ids,content,context={}):

        file_name   = 'export_'+time.strftime('%Y%m%d_%H%M%S')+'.tsv'
        attach_id   = self.pool.get('ir.attachment').create(cr, uid, {
            'name'          : file_name,
            'datas'         : base64.encodestring(content),
            'datas_fname'   : file_name,
            'res_model'     : self._name,
            'res_id'        : ids,
            },
            context=context
        )
        return True

    def action_exported(self,cr,uid,ids,*args):
        if not len(ids):
            return False

        # Employee must have a recordID matching his supplier account
        # in Accountedge to generate an expense sheet
        for id in ids:
            this    = self.browse(cr, uid, id)
            if not this.employee_id.supplier_id_accountedge:
                raise osv.except_osv('Accountedge Supplier ID missing',
                        'Please add the Accountedge supplier ID on the employee before exporting the sheet.')

            self._create_csv_report(cr,uid,ids,{})
            self.write(cr,uid,ids,{'state': 'exported'})

        return True


    def action_imported(self,cr,uid,ids,*args):
        if not len(ids):
            return False
        for id in ids:
            self.write(cr,uid,ids,{'state': 'imported'})
        return True


    def _get_cur_account_manager(self, cr, uid, ids, field_name, arg, context):
        res  = {}
        for id in ids:
            emails = ''
            grp_ids = self.pool.get('res.groups').search(cr, uid, [('name','=',u'Manager'),('category_id.name','=',u'Accounting & Finance')])
            usr_ids = self.pool.get('res.users').search(cr, uid, [('groups_id','=',grp_ids[0])])
            usrs    = self.pool.get('res.users').browse(cr, uid, usr_ids)

            for user in usrs:
                if user.user_email:
                    emails += user.user_email
                    emails += ','
                else:
                    empl_id = self.pool.get('hr.employee').search(cr, uid,[('login','=',user.login)])[0]
                    empl    = self.pool.get('hr.employee').browse(cr, uid, empl_id)
                    if empl.work_email:
                        emails += empl.work_email
                        emails += ','

            emails  = emails[:-1]
            res[id] = emails
        return res

    _columns = {
        'manager' : fields.function(_get_cur_account_manager,string='Manager',type='char',size=128,readonly=True),
        'state' : fields.selection([
            ('draft', 'New'),
            ('confirm', 'Waiting Approval'),
            ('accepted', 'Approved'),
            ('exported', 'Exported'),
            ('imported', 'Imported'),
            ('cancelled', 'Refused'),],
            'State', readonly=True, help='When the expense request is created the state is \'Draft\'.\
                    \n It is confirmed by the user and request is sent to admin, the state is \'Waiting Confirmation\'.\
                    \nIf the admin accepts it, the state is \'Accepted\'.\
                    \nIf the admin refuses it, the state is \'Refused\'.\
                    \n If a csv file has been generated for the expense request, the state is  \'Exported\'.\
                    \n If the expense request has been imported in AccountEdge, the state is \'Imported\'.'
        ),
    }


hr_expense_expense()

class hr_expense_line(osv.osv):
    _inherit = 'hr.expense.line'

    def _get_parent_state(self, cr, uid, ids, field_name, arg, context):
        res  = {}
        for id in ids:
            expense_line = self.pool.get('hr.expense.line').browse(cr, uid, id)
            res[id] = expense_line.expense_id.state
        return res

    _columns = {
        'state': fields.function(_get_parent_state,string='Expense State',type='char',size=128,readonly=True),
    }

hr_expense_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
