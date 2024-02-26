# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class ThemeHome(http.Controller):

    @http.route('/', auth='public', type='http', website=True)
    def home_products(self, **kw):
        new_arrivals_mens = request.env['product.template'].sudo().search(
            [('categ_id', '=', 10)])

        new_arrivals_womens = request.env['product.template'].sudo().search(
            [('categ_id', '=', 12)])

        new_arrivals_kids = request.env['product.template'].sudo().search(
            [('categ_id', '=', 13)])
        # print("####################")
        # print(new_arrivals_mens)
        for i in new_arrivals_mens:
            print(i.name)
        return http.request.render('theme_home.website_homepage',{'new_arrivals_mens': new_arrivals_mens,'new_arrivals_womens': new_arrivals_womens, 'new_arrivals_kids': new_arrivals_kids})

    @http.route('/about-us', auth='public', type="http", website=True)
    def about_us(self, **kw):
        return http.request.render('theme_home.about-us', {})

    @http.route('/testimonials', auth='public', type="http", website=True)
    def about_us(self, **kw):
        return http.request.render('theme_home.testimonials', {})

    @http.route('/mycart', auth='public', type="http", website=True)
    def about_us(self, **kw):
        return http.request.render('theme_home.mycart', {})

    @http.route(['/products', '/products/page/<int:page>'], auth='public', type='http', website=True)
    def all_products(self, page=0, search='', **post):
        domain = []
        if search:
            domain.append(('name', 'ilike', search))
        if search:
            post["search"] = search


        new_arrivals = request.env['product.template'].sudo().search(domain)
        # new_arrivals = request.env['product.template'].sudo().search(['|', '|', ('categ_id', '=', 10), ('categ_id', '=', 12), ('categ_id', '=', 13)])
        total = new_arrivals.sudo().search_count([])
        pager = request.website.pager(
            url='/products',
            total=total,
            page=page,
            step=3,
        )
        offset = pager['offset']
        new_arrivals = new_arrivals[offset: offset + 6]
        # new_arrivals = request.env['product.template'].sudo().search([('website_published', '=', True)],
        #                                                              order='create_date desc', limit=30)
        # values = {
        #     'new_arrivals': new_arrivals
        # }

        #response = http.Response(template='theme_home.products', {'search': search,'new_arrivals': new_arrivals,'pager': pager,})
        return http.request.render('theme_home.products', {'search': search,'new_arrivals': new_arrivals,'pager': pager,})

    @http.route('/product-view/<model("product.template"):pr_id>', auth='public', type='http', website=True)
    def product_view(self, pr_id, **kw):
        product_id = ''

        if pr_id.id:
            product_id = pr_id.id
            pr_details = request.env['product.product'].sudo().search([('product_tmpl_id', '=', product_id)])

        return http.request.render('theme_home.product-view', {'pr_details': pr_details})
