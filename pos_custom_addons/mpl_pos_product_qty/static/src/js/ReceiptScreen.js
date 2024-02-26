odoo.define('mpl_pos_product_qty.ReceiptScreen', function (require) {
    'use strict';

    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const Registries = require('point_of_sale.Registries');

    const ModReceiptScreen = (ReceiptScreen) =>
        class extends ReceiptScreen {
            // Update product qty when place an order
            orderDone() {
                let self = this;
                const AllProductIds = self.currentOrder.orderlines.models.map(l => l.product.id);
                let ProductIds = [...new Set(AllProductIds)];
                self.currentOrder.finalize();
                self.rpc({
                    model: 'product.product',
                    method: 'search_read',
                    domain: [['id', 'in', ProductIds]],
                    fields: ['qty_available', 'barcode'],
                    context: Object.assign(self.env.session.user_context, { location: self.env.pos.config.location_id[0] }),
                }).then(function(result){
                    result.forEach((data => {
                        self.env.pos.db.product_by_id[data.id].qty_available = data.qty_available;
                        if (data.barcode) {
                            self.env.pos.db.product_by_barcode[data.barcode].qty_available = data.qty_available;
                        }
                    }));
                    const { name, props } = self.nextScreen;
                    self.showScreen(name, props);
                }, function (err) {
                    console.warn('>> Error when update the product qty : ' + self.props.product.display_name)
                    const { name, props } = self.nextScreen;
                    self.showScreen(name, props);
                })
            }
        }

    Registries.Component.extend(ReceiptScreen, ModReceiptScreen);

    return ModReceiptScreen;
});
