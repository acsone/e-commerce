# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tests.common import TransactionCase


class TestProductTemplateLinker(TransactionCase):
    """
    Tests for product.template.linker
    """

    def setUp(self):
        super(TestProductTemplateLinker, self).setUp()
        self.env = self.env(
            context=dict(self.env.context, tracking_disable=True))
        self.wizard_obj = self.env['product.template.linker']
        self.product_link_obj = self.env['product.template.link']
        self.product1 = self.env.ref(
            "product.product_product_25").product_tmpl_id
        self.product2 = self.env.ref(
            "product.product_product_5").product_tmpl_id
        self.product3 = self.env.ref(
            "product.product_product_27").product_tmpl_id
        self.products = self.product1 | self.product2 | self.product3
        self.products.mapped("product_template_link_ids").unlink()

    def _launch_wizard(self, products, operation_type, link_type=False):
        """

        :param products: product.template recordset
        :return: product.template.linker recordset
        """
        values = {
            "operation_type": operation_type,
            "link_type": link_type,
            "product_ids": [(6, False, products.ids)],
        }
        return self.wizard_obj.create(values)

    def test_wizard_link_cross_sell(self):
        link_type = "cross_sell"
        wizard = self._launch_wizard(
            self.products, operation_type="link", link_type=link_type)
        links = wizard.action_apply_link()
        for link in links:
            source_product = link.product_template_id
            linked_products = source_product.product_template_link_ids
            expected_products_linked = self.products - source_product
            self.assertEquals(
                set(expected_products_linked.ids),
                set(linked_products.mapped("linked_product_template_id").ids)
            )
            self.assertEquals(link_type, link.link_type)

    def test_wizard_link_up_sell(self):
        link_type = "up_sell"
        wizard = self._launch_wizard(
            self.products, operation_type="link", link_type=link_type)
        links = wizard.action_apply_link()
        for link in links:
            source_product = link.product_template_id
            linked_products = source_product.product_template_link_ids
            expected_products_linked = self.products - source_product
            self.assertEquals(
                set(expected_products_linked.ids),
                set(linked_products.mapped("linked_product_template_id").ids)
            )
            self.assertEquals(link_type, link.link_type)

    def test_wizard_link_duplicate1(self):
        link_type = "up_sell"
        wizard = self._launch_wizard(
            self.products, operation_type="link", link_type=link_type)
        self.product_link_obj.create({
            "product_template_id": self.product1.id,
            "linked_product_template_id": self.product2.id,
            "link_type": link_type,
        })
        links = wizard.action_apply_link()
        for link in links:
            source_product = link.product_template_id
            linked_products = source_product.product_template_link_ids
            expected_products_linked = self.products - source_product
            self.assertEquals(
                set(expected_products_linked.ids),
                set(linked_products.mapped("linked_product_template_id").ids))
            self.assertEquals(link_type, link.link_type)
        # Ensure no duplicates
        link = self.product1.product_template_link_ids.filtered(
            lambda l: l.linked_product_template_id == self.product2)
        self.assertEquals(1, len(link))

    def test_wizard_link_duplicate2(self):
        link_type = "cross_sell"
        wizard = self._launch_wizard(
            self.products, operation_type="link", link_type=link_type)
        self.product_link_obj.create({
            "product_template_id": self.product1.id,
            "linked_product_template_id": self.product2.id,
            "link_type": "up_sell",
        })
        links = wizard.action_apply_link()
        for link in links:
            source_product = link.product_template_id
            linked_products = source_product.product_template_link_ids
            expected_products_linked = self.products - source_product
            self.assertEquals(
                set(expected_products_linked.ids),
                set(linked_products.mapped("linked_product_template_id").ids))
            self.assertEquals(link_type, link.link_type)
        # Ensure no duplicates
        link = self.product1.product_template_link_ids.filtered(
            lambda l: l.linked_product_template_id == self.product2)
        # 2 because we have up_sell and cross_sell
        self.assertEquals(2, len(link))

    def test_wizard_unlink(self):
        wizard = self._launch_wizard(self.products, operation_type="unlink")
        self.product_link_obj.create({
            "product_template_id": self.product1.id,
            "linked_product_template_id": self.product2.id,
            "link_type": "up_sell",
        })
        self.product_link_obj.create({
            "product_template_id": self.product1.id,
            "linked_product_template_id": self.product3.id,
            "link_type": "cross_sell",
        })
        wizard.action_apply_unlink()
        self.assertFalse(self.product1.product_template_link_ids)
