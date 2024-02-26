odoo.define('mpl_pos_product_qty.pos_show_product_qty', function(require){
'use strict';
const models = require('point_of_sale.models');
const rpc = require('web.rpc');
const session = require('web.session');
const concurrency = require('web.concurrency');
const { Gui } = require('point_of_sale.Gui');

var _super_posmodel = models.PosModel.prototype;
models.PosModel = models.PosModel.extend({
    initialize: function () {
        var self = this;
        var res = _super_posmodel.initialize.apply(this, arguments);
        return res;
    },
    load_server_data: function(){
        var self = this;
        var loaded = _super_posmodel.load_server_data.apply(this, arguments);
            self.models.forEach(function(elem){
                if (elem.model == 'product.product'){
                    elem.fields.push('qty_available');
                    elem.context = function(self){ return { location: self.config.location_id && self.config.location_id[0] }; }
                }
            });
        return loaded;
    },
});
return models;
});