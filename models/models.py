# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo.tools import formatLang

class vit_complete_receipts(models.Model):
    _name = 'purchase.bill.union'
    _inherit = 'purchase.bill.union'

    picking_id = fields.Many2one(string='Receipts', comodel_name='stock.picking', readonly=True,)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'purchase_bill_union')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW purchase_bill_union AS (
                SELECT
                    id, number as name, reference, partner_id, date, amount_untaxed as amount, currency_id, company_id,
                    id as vendor_bill_id, NULL::integer as purchase_order_id, NULL::integer as picking_id
                FROM account_invoice
                WHERE
                    type='in_invoice' and COALESCE(number, '') != ''
                UNION
                SELECT
                    -id as id, name, partner_ref, partner_id, date_order::date as date, amount_untaxed as amount, currency_id, company_id,
                    NULL::integer as vendor_bill_id, id as purchase_order_id, NULL::integer as picking_id
                FROM purchase_order
                WHERE
                    state in ('purchase', 'done') AND
                    invoice_status in ('to invoice', 'no')
                UNION
                SELECT
                    -id as id, name, '', partner_id, date::date as date, 0, 1, company_id,
                    NULL::integer as vendor_bill_id, NULL::integer as purchase_order_id, id as picking_id
                FROM stock_picking sp
                WHERE
                    state in ('stock_picking', 'done') AND
                    sp.picking_type_id = 1
            )""")

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    picking_id = fields.Many2one(string='Receipts', comodel_name='stock.picking', readonly=True,)

    @api.onchange('vendor_bill_purchase_id')
    def _onchange_bill_purchase_order(self):
        if not self.vendor_bill_purchase_id:
            return {}
        self.picking_id = self.vendor_bill_purchase_id.picking_id
        self.purchase_id = self.vendor_bill_purchase_id.purchase_order_id
        self.vendor_bill_id = self.vendor_bill_purchase_id.vendor_bill_id
        self.vendor_bill_purchase_id = False
        return {}

    def _prepare_invoice_line_from_pick_line(self, line):
        invoice_line = self.env['account.invoice.line']
        date = self.date or self.date_invoice
        data = {
            'move_id': line.id,
            'name': line.picking_id.name + ': ' + line.name,
            'origin': line.picking_id.origin,
            'uom_id': line.product_uom.id,
            'product_id': line.product_id.id,
            'account_id': invoice_line.with_context({'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
            'price_unit': line.product_id.standard_price,
            'quantity': line.quantity_done,
            # 'discount': 0.0,
            # 'account_analytic_id': line.account_analytic_id.id,
            # 'analytic_tag_ids': line.analytic_tag_ids.ids,
            # 'invoice_line_tax_ids': invoice_line_tax_ids.ids
        }
        account = invoice_line.get_invoice_line_account('in_invoice', line.product_id, "" , self.env.user.company_id)
        if account:
            data['account_id'] = account.id
        return data

    # Load all unsold PO lines
    @api.onchange('picking_id')
    def picking_move_change(self):
        if not self.picking_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.picking_id.partner_id.id

        new_lines = self.env['account.invoice.line']
        for line in self.picking_id.move_lines - self.invoice_line_ids.mapped('move_id'):
            data = self._prepare_invoice_line_from_pick_line(line)
            new_line = new_lines.new(data)
            new_line._set_additional_fields(self)
            new_lines += new_line

        self.invoice_line_ids += new_lines
        self.picking_id = False
        return {}

    @api.onchange('invoice_line_ids')
    def _onchange_origin(self):
        purchase_ids = self.invoice_line_ids.mapped('purchase_id')
        if purchase_ids:
            self.origin = ', '.join(purchase_ids.mapped('name'))
        picking_ids = self.invoice_line_ids.mapped('picking_id')
        if picking_ids:
            self.origin = ', '.join(picking_ids.mapped('name'))

class AccountInvoiceLine(models.Model):
    """ Override AccountInvoice_line to add the link to the purchase order line it is related to"""
    _inherit = 'account.invoice.line'

    move_id = fields.Many2one('stock.move', 'Stock Move', ondelete='set null', index=True, readonly=True)
    picking_id = fields.Many2one('stock.picking', related='move_id.picking_id', string='Stock Picking', store=False, readonly=True, related_sudo=False)


class StockMove(models.Model):
    _inherit = "stock.move"

    invoice_lines = fields.One2many('account.invoice.line', 'move_id', string="Bill Lines", readonly=True, copy=False)