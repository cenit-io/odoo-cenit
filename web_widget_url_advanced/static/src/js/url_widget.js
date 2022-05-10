/* Copyright 2018 Simone Orsi - Camptocamp SA
License LGPLv3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html). */

odoo.define("web_widget_url_advanced", function(require) {
    "use strict";

    var basic_fields = require("web.basic_fields");

    basic_fields.UrlWidget.include({
        /**
         * @override
         */
        init: function() {
            this._super.apply(this, arguments);
            // Retrieve customized `<a />` text from a field
            // via `text_anchor` attribute or `options.text_anchor`
            var text_anchor = this.attrs.text_anchor || this.attrs.options.text_anchor;
            if (text_anchor) {
                // var field_value = this.recordData[text_field];
                // if (_.isObject(field_value) && _.has(field_value.data)) {
                //     field_value = field_value.data.display_name;
                // }
                this.attrs.text = text_anchor;
            }
        },
        /**
         *
         * @override
         * @private
         */
        _renderReadonly: function() {
            this._super.apply(this, arguments);
            var prefix = this.attrs.prefix_name || this.attrs.options.prefix_name;
            if (prefix) {
                this.$el.attr("href", prefix + ":" + this.value);
            }
        },
    });
});
