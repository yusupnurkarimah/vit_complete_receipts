# -*- coding: utf-8 -*-
from odoo import http

# class VitCompleteReceipts(http.Controller):
#     @http.route('/vit_complete_receipts/vit_complete_receipts/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/vit_complete_receipts/vit_complete_receipts/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('vit_complete_receipts.listing', {
#             'root': '/vit_complete_receipts/vit_complete_receipts',
#             'objects': http.request.env['vit_complete_receipts.vit_complete_receipts'].search([]),
#         })

#     @http.route('/vit_complete_receipts/vit_complete_receipts/objects/<model("vit_complete_receipts.vit_complete_receipts"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('vit_complete_receipts.object', {
#             'object': obj
#         })