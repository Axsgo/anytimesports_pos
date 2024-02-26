odoo.define('anytime_pos_modifier.models',function(require){
    "use strict"
    var models = require('point_of_sale.models');

    let _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
        get_invoice_number: function() {
            var invoice_number = this.get_name();
            if (invoice_number) {
                var invoice_number = invoice_number.replace('Order ', '');
            }
            return invoice_number;
        },
        get_client_name: function() {
            var client = this.get('client');
            if (client) {
                return client.name;
            }
            return '';
        },
        get_client_mobile: function() {
            var client = this.get('client');
            if (client) {
                return client.phone;
            }
            return '';
        },
        export_for_printing: function () {
            var receipt = _super_Order.export_for_printing.call(this);
            receipt.total_with_tax_and_discount = this.get_total_without_tax() + this.get_total_tax() + this.get_total_discount();
            receipt.invoice_number = this.get_invoice_number();
            receipt.customer_name = this.get_client_name();
            receipt.mobile_number = this.get_client_mobile();
            return receipt;
        },
    })
});
