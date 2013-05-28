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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.·····
#
##############################################################################

import time
import base64

from osv import osv, fields


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
            output += "RecordId\tDate\tVendor Invoice #\tAccount #\tAmout\tDescription\
                        \tTax Code\tTax Amount TVQ\tTax Amount TPS/TVH\tCurrency Code\tExchange Rate\r\n"

            for l in this.line_ids:
                output  += u"%s\t%s\t%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\t%s\t%s\r\n" % (
                        this.employee_id.supplier_id_accountedge,
                        l.date_value,
                        l.expense_id.id,
                        l.account_id.code,
                        (l.total_amount or '0.00'),
                        l.name,
                        (l.tax_id.tax_code_accountedge or '000'),
                        self._compute_TVQ(cr,uid,l,context),
                        self._compute_TPS_TVH(cr,uid,l,context),
                        (l.expense_id.currency_id.name or 'CAD'),
                        (l.expense_id.currency_id.rate or '1.0'))
                byte_string  = output.encode('utf-8-sig')

            res[id] = base64.encodestring(byte_string)

            self.write(cr, uid, ids, {'csv_file':res[id]}, context=context)
            self._add_attachment(cr,uid,id,byte_string,context)

        return True


    def _compute_TPS_TVH(self,cr,uid,expense_line,context={}):
        tax = expense_line.tax_id
        tax_percent = None

        if not tax.amount:
            return 0

        if tax.tax_code_accountedge != '140':
            # cas simple, une seule taxe
            tax_percent = float(tax.amount)
        else:
            # cas TPS-TVQ, prendre la TPS
            for child_tax in tax.child_ids:
                if child_tax.tax_code_accountedge == '500': # TPS
                    tax_percent = float(child_tax.amount)
                    break;

        if tax_percent:
            amount_HT  = expense_line.total_amount / (1 + tax_percent)
            return amount_HT * tax_percent
        return 0


    def _compute_TVQ(self,cr,uid,expense_line,context={}):
        tax = expense_line.tax_id

        if tax.tax_code_accountedge == '140':
            # On a la TVQ seulement dans le cas TPS+TVQ
            for child_tax in tax.child_ids:
                if child_tax.tax_code_accountedge != '500':
                    # On estime que la taxe fille qui n'a pas un id de 500
                    # est la TVQ
                    tax_percent = float(child_tax.amount)
                    amount_HT  = expense_line.total_amount / (1 + tax_percent)
                    return amount_HT * tax_percent
        return 0


    def _add_attachment(self,cr,uid,ids,content,context={}):

        file_name   = 'rapport_'+time.strftime('%Y%m%d_%H%M%S')
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

        # L'utilisateur doit avoir un recordID correspondant à
        # son compte fournisseur dans AccountEdge pour pouvoir
        # générer la note de frais
        for id in ids:
            this    = self.browse(cr, uid, id)

            if not this.employee_id.supplier_id_accountedge:
                raise osv.except_osv('ID du fournisseur dans AccountEdge manquant',
                        'Veuillez ajouter ID de fournisseur AccountEdge pour dans la fiche cet employé au préalable.')

            self._create_csv_report(cr,uid,ids,{})
            self.write(cr,uid,ids,{'state': 'exported'})

        return True



    _columns = {
        'state': fields.selection([
            ('draft', 'New'),
            ('confirm', 'Waiting Approval'),
            ('accepted', 'Approved'),
            ('exported', 'Exporté'),
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

