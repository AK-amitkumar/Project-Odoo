# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
from datetime import datetime
from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import re

class ExternalCreateCustomer(models.AbstractModel):
    _description = 'Create Customer API'
    _name = 'external.create.customer'

    def _convert_str(self, value):
        if type(value) is str:
            return (unicode(value, "utf-8")).strip()
        else:
            return value

    @api.multi
    def _validate_email(self, email):
        match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email)
        if match == None:
            return False
        return True

    @api.model
    def create_customer(self, code, name, company_type, street, state_code, country_code, email, date_of_birth, date_of_founding, mobile, gender, website, vat,
                        indentify_number, function, phone, fax, sub_email_1, sub_email_2, main_account, promotion_account, representative, source, password_idpage, company_id):
        res = {'"code"': 0, '"msg"': '""'}
        if not code:
            ref = self.env['ir.sequence'].next_by_code('res.partner') or '/'
        else:
            ref = code
            if self.env['res.partner'].search([('ref', '=', code)]):
                return {'"msg"': '"Customer already exists."'}
        ResCountyState = self.env['res.country.state']
        ResPartner = self.env['res.partner']
        ResCountry = self.env['res.country']
        ResCompany = self.env['res.company']
        customer_vals = {}
        # Check type of data
        name = self._convert_str(name)
        if not name:
            return {'"msg"': '"Customer name could not be empty"'}
        customer_vals.update({'name': name})
        if not company_type:
            res['"msg"'] = '"Company Type could not be empty and must belong `person`, `company` or `agency`"'
            return res
        customer_vals.update({'company_type': company_type})
        if not email:
            res['"msg"'] = '"Email could not be empty"'
            return res
        if company_id:
            if not ResCompany.browse(company_id):
                res['"msg"'] = '"Company not exists"'
                return res
            customer_vals.update({'company_id': company_id})
        if not self._validate_email(email) or (sub_email_1 and not self._validate_email(sub_email_1)) or (sub_email_2 and not self._validate_email(sub_email_2)):
            # print email, sub_email_1, sub_email_2
            return {'"msg"': '"Invalid email."'}
        customer_vals.update({
            'email': email,
            'sub_email_1': sub_email_1 or False,
            'sub_email_2': sub_email_2 or False,
        })
        msg = '""'
        customer_vals.update({
            'ref': ref,
            'customer': True,
            'street': street,
            'mobile': mobile,
            'website': website,
            'vat': vat,
            'indentify_number': indentify_number,
            'function': function,
            'phone': phone,
            'fax': fax,
            'main_account': main_account,
            'promotion_account': promotion_account,
            'state_code': state_code,
            'country_code': country_code,
            'representative': representative,
            'password_idpage': password_idpage
        })
        # Get state id
        if state_code:
            state_id = ResCountyState.search([('code', '=', state_code)], limit=1)
            if state_id:
                customer_vals.update({'state_id': state_id.id})
            else:
                return {'"msg"': '"State Code {} is not found"'.
                        format(customer_vals['state_code'])}

        try:
            if date_of_birth:
                date_of_birth_fix = datetime.strptime(str(date_of_birth), DF)
                customer_vals.update({'date_of_birth': date_of_birth_fix})
            if date_of_founding:
                date_of_founding_fix = datetime.strptime(str(date_of_founding), DF)
                customer_vals.update({'date_of_founding': date_of_founding_fix})
        except ValueError:
            return {
                '"code"': 0, '"msg"': '"Invalid date_of_birth or date_of_founding yyyy-mm-dd"',
                '"data"': {}}

        # Get Country id
        country_code = self._convert_str(country_code)
        if country_code:
            country_id = ResCountry.search(
                [('code', '=', country_code)], limit=1)
            if country_id:
                customer_vals.update({'country_id': country_id.id})
            else:
                return {'"msg"': '"Country Code {} is not found"'.
                        format(country_code)}

        # Check gender value
        if gender:
            if gender not in ['male', 'female']:
                return {
                    '"msg"': '"Gender must be in (`male`, `female`)"'
                }
            customer_vals.update({'gender': gender})

        # Check source
        if source:
            source_id = self.env['res.partner.source'].search(
                [('code', '=', source)], limit=1)
            if not source_id:
                return {
                    '"msg"': ('"Customer source `%s` is not found.  "' % source)
                        }
            customer_vals.update({'source_id': source_id.id})
        customer = ResPartner.create(customer_vals)
        return {'"customer"': '\"' + customer.name + '\"', '"msg"': msg, '"code"': 1}

    @api.model
    def update_contact(self, cus_code, type, date_of_birth, gender, street, state_code, country_code, contact_name, indentify_number, function, email, phone, mobile, fax, company_id):
        res = {'"code"': 0, '"msg"': '""'}
        ResCountyState = self.env['res.country.state']
        ResPartner = self.env['res.partner']
        ResCountry = self.env['res.country']
        ResCompany = self.env['res.company']
        customer_vals = {}
        # Check type of data
        if not cus_code:
            return {'"msg"': '"Customer Code could not be empty"'}
        customer_id = ResPartner.search([('ref', '=', cus_code)])
        if not customer_id:
            return {'"msg"': '"Customer not exists"'}
        if not type or type not in ('payment_manager', 'technical_manager', 'domain_manager', 'helpdesk_manager', 'contact'):
            res['"msg"'] = '"Customer Type could not be empty and must belong `payment_manager`, `technical_manager`, `domain_manager`, `helpdesk_manager` or `contact`"'
            return res
        contact_id = customer_id.child_ids.filtered(lambda c: c.type == type)
        if not contact_name:
            res['"msg"'] = '"Contact name could not be empty"'
            return res
        customer_vals.update({
            'company_type': 'person',
            'name': contact_name
        })
        if company_id:
            if not ResCompany.browse(company_id):
                res['"msg"'] = '"Company not exists"'
                return res
            customer_vals.update({'company_id': company_id})
        # if not email:
        #     res['"msg"'] = '"Email could not be empty"'
        #     return res
        if email and not self._validate_email(email):
            return {'"msg"': '"Invalid email."'}
        customer_vals.update({'email': email})
        msg = '""'
        customer_vals.update({
            'street': street,
            'mobile': mobile,
            'indentify_number': indentify_number,
            'function': function,
            'phone': phone,
            'fax': fax,
            'state_code': state_code,
            'country_code': country_code,
        })
        # Get state id
        if state_code:
            state_id = ResCountyState.search([('code', '=', state_code)], limit=1)
            if state_id:
                customer_vals.update({'state_id': state_id.id})
            else:
                return {'"msg"': '"State Code {} is not found"'.
                        format(customer_vals['state_code'])}

        try:
            if date_of_birth:
                date_of_birth_fix = datetime.strptime(str(date_of_birth), DF)
                customer_vals.update({'date_of_birth': date_of_birth_fix})
        except ValueError:
            return {
                '"code"': 0, '"msg"': '"Invalid date_of_birth or date_of_founding yyyy-mm-dd"',
                '"data"': {}}

        # Get Country id
        country_code = self._convert_str(country_code)
        if country_code:
            country_id = ResCountry.search(
                [('code', '=', country_code)], limit=1)
            if country_id:
                customer_vals.update({'country_id': country_id.id})
            else:
                return {'"msg"': '"Country Code {} is not found"'.
                        format(country_code)}

        # Check gender value
        if gender:
            if gender not in ['male', 'female']:
                return {
                    '"msg"': '"Gender must be in (`male`, `female`)"'
                }
            customer_vals.update({'gender': gender})
        # print customer_vals
        if not contact_id:
            customer_vals.update({
                'parent_id': customer_id.id,
                'customer': False,
                'supplier': False
            })
            contact_id = ResPartner.create(customer_vals)
        else:
            contact_id.sudo().write(customer_vals)
        return {'"Update successful contact of customer"': '\"' + customer_id.name + '\"', '"msg"': msg, '"code"': 1}

    @api.model
    def create_list_customer(self, lines=[]):
        res = {'"code"': 0, '"msg"': '""'}
        ResCountyState = self.env['res.country.state']
        ResPartner = self.env['res.partner']
        ResCountry = self.env['res.country']
        ResCompany = self.env['res.company']

        # Check type of data
        if not lines:
            return {'"msg"': '"Lines could not be empty"'}
        if type(lines) is not list:
            return {'"msg"': '"Invalid OrderLineEntity"'}
        for line in lines:
            customer_vals = {'customer': True}
            if not line.get('code'):
                ref = self.env['ir.sequence'].next_by_code('res.partner') or '/'
            else:
                ref = line.get('code')
                if self.env['res.partner'].search([('ref', '=', line.get('code'))]):
                    res['"msg"'] = '"Customer already exists."'
                    break
            name = self._convert_str(line.get('name'))
            if not name:
                res['"msg"'] = '"Customer name could not be empty"'
                break
            customer_vals.update({'name': name, 'ref': ref})
            if not line.get('company_type') or line.get('company_type') not in ('person', 'company', 'agency'):
                res['"msg"'] = '"Company Type could not be empty and must belong `person`, `company` or `agency`"'
                break
            customer_vals.update({'company_type': line.get('company_type')})
            if not line.get('email'):
                res['"msg"'] = '"Email could not be empty"'
                break
            if not self._validate_email(line.get('email')) or (line.get('sub_email_1') and not self._validate_email(line.get('sub_email_1'))) \
                    or (line.get('sub_email_2') and not self._validate_email(line.get('sub_email_2'))):
                res['"msg"'] = '"Invalid email."'
                break
            customer_vals.update({
                'email': line.get('email'),
                'sub_email_1': line.get('sub_email_1') or '',
                'sub_email_2': line.get('sub_email_2') or '',
            })
            msg = '""'
            list_fields = ['street', 'state_code', 'country_code', 'date_of_birth', 'date_of_founding', 'mobile',
                           'gender', 'website', 'vat', 'indentify_number', 'function', 'phone', 'fax',
                           'main_account', 'promotion_account', 'representative', 'source', 'password_idpage', 'company_id']
            for field in list_fields:
                if not line.get(field):
                    continue
                if field in ['email', 'sub_email_1', 'sub_email_2']:
                    if not self._validate_email([line[field]]):
                        res['msg'] = 'Invalid email {} : {} .' . format(field, line[field])
                        break
                customer_vals.update({field: line[field]})

            if line.get('company_id'):
                if not ResCompany.browse(line.get('company_id')):
                    res['"msg"'] = '"Company not exists"'
                    break
                customer_vals.update({'company_id': line.get('company_id')})

            # Get state id
            if line.get('state_code', ''):
                state_id = ResCountyState.search([('code', '=', line.get('state_code', ''))], limit=1)
                if state_id:
                    customer_vals.update({'state_id': state_id.id})
                else:
                    res['"msg"'] = '"State Code {} is not found"'. format(customer_vals['state_code'])
                    break

            try:
                if line.get('date_of_birth'):
                    date_of_birth_fix = datetime.strptime(str(line.get('date_of_birth')), DF)
                    customer_vals.update({'date_of_birth': date_of_birth_fix})
                if line.get('date_of_founding'):
                    date_of_founding_fix = datetime.strptime(str(line.get('date_of_founding')), DF)
                    customer_vals.update({'date_of_founding': date_of_founding_fix})
            except ValueError:
                res = {'"code"': 0, '"msg"': '"Invalid date_of_birth or date_of_founding yyyy-mm-dd"',
                    '"data"': {}}
                break

            # Get Country id
            country_code = self._convert_str(line.get('country_code'))
            if country_code:
                country_id = ResCountry.search(
                    [('code', '=', line.get('country_code'))], limit=1)
                if country_id:
                    customer_vals.update({'country_id': country_id.id})
                else:
                    res = {'"msg"': '"Country Code {} is not found"'.
                            format(line.get('country_code'))}
                    break

            # Check gender value
            if line.get('gender'):
                if line.get('gender') not in ['male', 'female']:
                    res['"msg"'] = '"Gender must be in (`male`, `female`)"'
                    break
                customer_vals.update({'gender': line.get('gender')})

            # Check source
            if line.get('source'):
                source_id = self.env['res.partner.source'].search(
                    [('code', '=', line.get('source'))], limit=1)
                if not source_id:
                    res['"msg"'] = ('"Customer source `%s` is not found.  "' % line.get('source'))
                    break
                customer_vals.update({'source_id': source_id.id})
            customer = ResPartner.create(customer_vals)
            res['"customer"'] = customer.name
        res['"code"'] = 1
        return res

    @api.model
    def get_partner(self, code):
        res = {'"code"': 0, '"msg"': '', '"data"': {}}
        ResPartner = self.env['res.partner']
        data = {}

        # Check partner
        if not code:
            res.update({'"msg"': '"Ref could be not empty"'})
            return res
        partner_id = ResPartner.search([('ref', '=', code)], limit=1)
        if not partner_id:
            res.update({'"msg"': '"Partner not found."'})
            return res

        # If arguments are ok
        try:
            # Parse data
            data.update({
                '"id"': partner_id.id,
                '"name"': '\"' + partner_id.name + '\"',
                '"ref"': '\"' + (partner_id.ref or '') + '\"',
                '"company_type"': '\"' + partner_id.company_type + '\"',
                '"street"': '\"' + (partner_id.street or '') + '\"',
                '"state_id"': '\"' + (partner_id.state_id and partner_id.state_id.name or '') + '\"',
                '"country_id"': '\"' + (partner_id.country_id and partner_id.country_id.name or '') + '\"',
                '"website"': '\"' + (partner_id.website or '') + '\"',
                '"date_of_birth"': '\"' + (partner_id.date_of_birth or '') + '\"',
                '"date_of_founding"': '\"' + (partner_id.date_of_founding or '') + '\"',
                '"vat"': '\"' + (partner_id.vat or '') + '\"',
                '"indentify_number"': '\"' + (partner_id.indentify_number or '') + '\"',
                '"accounting_ref"': '\"' + (partner_id.accounting_ref or '') + '\"',
                '"phone"': '\"' + (partner_id.phone or '') + '\"',
                '"mobile"': '\"' + (partner_id.mobile or '') + '\"',
                '"fax"': '\"' + (partner_id.fax or '') + '\"',
                '"email"': '\"' + (partner_id.email or '') + '\"',
                '"sub_email_1"': '\"' + (partner_id.sub_email_1 or '') + '\"',
                '"sub_email_2"': '\"' + (partner_id.sub_email_2 or '') + '\"',
                '"title"': '\"' + (partner_id.title and partner_id.title.name or '') + '\"',
                '"main_account"': '\"' + str(partner_id.main_account or 0) + '\"',
                '"promotion_account"': '\"' + str(partner_id.promotion_account or 0) + '\"',
                '"password_idpage"': '\"' + (partner_id.password_idpage or '') + '\"',
                '"company_id"': partner_id.company_id and partner_id.company_id.id or 0,
            })

            res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        except:
            res['msg'] = '"Can not get partner"'
            return res
        return res

    @api.model
    def get_contact(self, code, type=False):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        ResPartner = self.env['res.partner']
        data = []
        # Check partner
        if not code:
            res.update({'"msg"': '"Ref could be not empty"'})
            return res
        partner_id = ResPartner.search([('ref', '=', code)], limit=1)
        if not partner_id:
            res.update({'"msg"': '"Partner not found."'})
            return res
        if type and type not in ('payment_manager', 'technical_manager', 'domain_manager', 'helpdesk_manager', 'contact'):
            res.update({'"msg"': '"Type must be in (`payment_manager`, `technical_manager`, `domain_manager`, `helpdesk_manager`, `contact`)"'})
            return res
        if not partner_id.child_ids:
            res.update({'"msg"': '"No contact."'})
            return res
        dict = {}
        for contact in partner_id.child_ids:
            contact_dict = {}
            if type:
                if contact.type == type:
                    contact_dict.update({
                        '"ref"': '\"' + (contact.ref or '') + '\"',
                        '"name"': '\"' + (contact.name or '') + '\"',
                        '"email"': '\"' + (contact.email or '') + '\"',
                        '"indentify_number"': '\"' + (contact.indentify_number or '') + '\"',
                        '"company_type"': '\"' + (contact.company_type or '') + '\"',
                        '"street"': '\"' + (contact.street or '') + '\"',
                        '"state_id"': '\"' + (contact.state_id and str(contact.state_id.id) or '') + '\"',
                        '"mobile"': '\"' + (contact.mobile or '') + '\"',
                        '"phone"': '\"' + (contact.phone or '') + '\"',
                        '"fax"': '\"' + (contact.fax or '') + '\"',
                        '"function"': '\"' + (contact.function or '') + '\"',
                        '"date_of_birth"': '\"' + (contact.date_of_birth or '') + '\"',
                        '"gender"': '\"' + (contact.gender or '') + '\"',
                        '"city"': '\"' + (contact.state_id and contact.state_id.code or '') + '\"',
                        '"country"': '\"' + (contact.country_id and contact.country_id.code or '') + '\"',
                        '"id"': '\"' + str(partner_id.id) + '\"'
                    })
                    dict.update({
                        '\"' + contact.type + '\"': [contact_dict]
                    })
                    break
            else:
                contact_dict.update({
                    '"ref"': '\"' + (contact.ref or '') + '\"',
                    '"name"': '\"' + (contact.name or '') + '\"',
                    '"email"': '\"' + (contact.email or '') + '\"',
                    '"indentify_number"': '\"' + (contact.indentify_number or '') + '\"',
                    '"company_type"': '\"' + (contact.company_type or '') + '\"',
                    '"street"': '\"' + (contact.street or '') + '\"',
                    '"state_id"': '\"' + (contact.state_id and str(contact.state_id.id) or '') + '\"',
                    '"mobile"': '\"' + (contact.mobile or '') + '\"',
                    '"phone"': '\"' + (contact.phone or '') + '\"',
                    '"fax"': '\"' + (contact.fax or '') + '\"',
                    '"function"': '\"' + (contact.function or '') + '\"',
                    '"date_of_birth"': '\"' + (contact.date_of_birth or '') + '\"',
                    '"gender"': '\"' + (contact.gender or '') + '\"',
                    '"city"': '\"' + (contact.state_id and contact.state_id.code or '') + '\"',
                    '"country"': '\"' + (contact.country_id and contact.country_id.code or '') + '\"',
                    '"id"': '\"' + str(partner_id.id) + '\"'
                })
                dict.update({
                    '\"' + contact.type + '\"': [contact_dict]
                })
        data.append(dict)
        res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        return res


