# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010, 2014 Tiny SPRL (<http://tiny.be>).
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

{
    "name": "Cenit IO Integrations Client",
    # "category": "Hidden",
    "version": "0.15.1",
    "application": True,
    "author": "Cenit IO",
    "website": "https://server.cenit.io",
    # ~ "license": "LGPL-3",
    "category": "Extra Tools",
    "summary": "Odoo, Cenit, Integration, Connector",
    "description": """
        Integrate with third party systems through the Cenit platform
    """,
    "depends": ["base", "base_automation"],
    "external_dependencies": {
        "python": ["inflect", "pyasn1", "OpenSSL", "ndg"]
    },
    "data": [
        "security/ir.model.access.csv",
        "view/config.xml",
        "view/data_definitions.xml",
        "view/setup.xml",
    ],
    "images": [
        "static/screenshots/main.png"
    ],
    "installable": True
}
