import unittest
from maksukortti import Maksukortti

class TestMaksukortti(unittest.TestCase):
    def setUp(self):
        self.maksukortti = Maksukortti(1000)

    def test_luotu_kortti_on_olemassa(self):
        self.assertNotEqual(self.maksukortti, None)

    def test_saldo_on_alussa_oikein(self):
        self.assertEqual(str(self.maksukortti), "Kortilla on rahaa 10.00 euroa")

    def test_rahan_lisaaminen_toimii(self):
        self.maksukortti.lataa_rahaa(500)

        self.assertEqual(self.maksukortti.saldo_euroina(), 15.0)
    
    def test_saldo_vahenee_jos_tarpeaksi_rahaa(self):
        self.maksukortti.ota_rahaa(500)

        self.assertEqual(self.maksukortti.saldo_euroina(), 5.0)

    def test_saldo_ei_muutu_jos_ei_tarpeaksi_rahaa(self):
        self.maksukortti.ota_rahaa(1200)

        self.assertEqual(self.maksukortti.saldo_euroina(), 10.0)

    def test_saldon_otto_palauttaa_true_jos_rahaa_riittaa(self):
        self.assertEqual(self.maksukortti.ota_rahaa(500), True)

    def test_saldon_otto_palauttaa_false_jos_rahaa_ei_riita(self):
        self.assertEqual(self.maksukortti.ota_rahaa(1200), False)
