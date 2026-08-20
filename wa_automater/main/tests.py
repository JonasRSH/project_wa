from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.db.models import Sum
from .models import Shipment, Colli, TransitDocument, Customs, Abfahrt


# ---------------------------------------------------------------------------
# Modelle
# ---------------------------------------------------------------------------

class ShipmentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', password='pass')

    def test_valid_shipment_number(self):
        s = Shipment(shipment_number='04964788310', user=self.user)
        s.full_clean()  # darf keinen ValidationError werfen

    def test_invalid_shipment_number_letters(self):
        from django.core.exceptions import ValidationError
        s = Shipment(shipment_number='0496478831X', user=self.user)
        with self.assertRaises(ValidationError):
            s.full_clean()

    def test_invalid_shipment_number_too_short(self):
        from django.core.exceptions import ValidationError
        s = Shipment(shipment_number='0496478831', user=self.user)
        with self.assertRaises(ValidationError):
            s.full_clean()

    def test_shipment_str(self):
        s = Shipment.objects.create(shipment_number='04964788310', user=self.user)
        self.assertEqual(str(s), '04964788310')


# ---------------------------------------------------------------------------
# T1-Abgleich
# ---------------------------------------------------------------------------

class ReconciliationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', password='pass')
        self.transit = TransitDocument.objects.create(
            t_number='26CH05WTL3TJWMS5J1',
            t_colli_quantity=32,
            t_weight=10121.996,
            t_customs_office='Rheinfelden-Autobahn',
            user=self.user,
        )
        self.shipment = Shipment.objects.create(
            shipment_number='04964788310',
            user=self.user,
            transit=self.transit,
        )

    def _get_t1_errors(self):
        """Führt denselben Abgleich wie views.py aus und gibt Fehlerliste zurück."""
        errors = []
        transit = self.shipment.transit
        if transit is None:
            return ['kein T1']
        colli_sum = self.shipment.collis.aggregate(total=Sum('quantity'))['total'] or 0
        if colli_sum != transit.t_colli_quantity:
            errors.append(f'Packstücke: {colli_sum} != {transit.t_colli_quantity}')
        weight_sum = self.shipment.collis.aggregate(total=Sum('weight'))['total'] or 0
        if round(weight_sum, 3) != round(transit.t_weight or 0, 3):
            errors.append(f'Gewicht: {weight_sum} != {transit.t_weight}')
        return errors

    def test_no_errors_when_data_matches(self):
        Colli.objects.create(quantity=32, weight=10121.996, shipment=self.shipment)
        self.assertEqual(self._get_t1_errors(), [])

    def test_colli_mismatch_detected(self):
        Colli.objects.create(quantity=10, weight=10121.996, shipment=self.shipment)
        errors = self._get_t1_errors()
        self.assertTrue(any('Packstücke' in e for e in errors))

    def test_weight_mismatch_detected(self):
        Colli.objects.create(quantity=32, weight=9000.0, shipment=self.shipment)
        errors = self._get_t1_errors()
        self.assertTrue(any('Gewicht' in e for e in errors))

    def test_multiple_collis_summed(self):
        Colli.objects.create(quantity=20, weight=6000.0, shipment=self.shipment)
        Colli.objects.create(quantity=12, weight=4121.996, shipment=self.shipment)
        self.assertEqual(self._get_t1_errors(), [])

    def test_no_transit_linked(self):
        self.shipment.transit = None
        self.shipment.save()
        self.assertEqual(self._get_t1_errors(), ['kein T1'])


# ---------------------------------------------------------------------------
# Login-Schutz
# ---------------------------------------------------------------------------

class AuthTest(TestCase):
    def test_main_view_requires_login(self):
        response = Client().get('/main/')
        self.assertRedirects(response, '/login/?next=%2Fmain%2F', fetch_redirect_response=False)

