# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request

class SuggestionBox(http.Controller):

    @http.route('/suggestion/submit', type='http', auth="public", website=True)
    def suggestion_submit_form(self, **post):
        categories = request.env['suggestion.category'].search([('level', '=', 'category')])
        return request.render("suggestion_box.suggestion_submit_form_template", {'categories': categories})

    @http.route('/suggestion/thankyou', type='http', auth="public", website=True)
    def suggestion_thankyou(self, **post):
        return request.render("suggestion_box.suggestion_thank_you_template")

    @http.route('/suggestion/process', type='http', auth="public", website=True, methods=['POST'], csrf=False)
    def suggestion_process_form(self, **post):
        is_anonymous = post.get('anonymous', False)
        owner = request.env.user if not is_anonymous and request.env.user.id != request.env.ref('base.public_user').id else False

        vals = {
            'name': post.get('name'),
            'category_id': int(post.get('category_id')) if post.get('category_id') else False,
            'area_id': int(post.get('area_id')) if post.get('area_id') else False,
            'item_id': int(post.get('item_id')) if post.get('item_id') else False,
            'description': post.get('description'),
            'owner_id': owner.id if owner else False,
        }

        if post.get('image'):
            vals['image'] = post.get('image').read()

        request.env['suggestion.suggestion'].sudo().create(vals)
        return request.redirect('/suggestion/thankyou')

    @http.route('/suggestion/get_areas', type='json', auth="public", website=True)
    def get_areas(self, category_id, **kw):
        areas = request.env['suggestion.category'].sudo().search_read(
            [('level', '=', 'area'), ('parent_id', '=', int(category_id))],
            ['id', 'name']
        )
        return areas

    @http.route('/suggestion/get_items', type='json', auth="public", website=True)
    def get_items(self, area_id, **kw):
        items = request.env['suggestion.category'].sudo().search_read(
            [('level', '=', 'item'), ('parent_id', '=', int(area_id))],
            ['id', 'name']
        )
        return items