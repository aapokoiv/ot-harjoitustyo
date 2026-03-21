import unittest
from kassapaate import Kassapaate
from maksukortti import Maksukortti

class TestKassapaate(unittest.TestCase):
    def setUp(self):
        self.kassa = Kassapaate()
        self.maksukortti = Maksukortti(1000)

    def test_alussa_oikea_maara_rahaa_kassassa(self):
        self.assertEqual(self.kassa.kassassa_rahaa_euroina(), 1000)

    def test_alussa_oikea_maara_myytyja_lounaita(self):
        self.assertEqual(self.kassa.maukkaat + self.kassa.edulliset, 0)

    def test_kateisosto_ei_toimi_jos_liian_vahan_rahaa_edullinen(self):
        self.assertEqual(self.kassa.syo_edullisesti_kateisella(200), 200)
        self.assertEqual(self.kassa.kassassa_rahaa_euroina(), 1000)
        self.assertEqual(self.kassa.edulliset, 0)

    def test_kateisosto_ei_toimi_jos_liian_vahan_rahaa_maukas(self):
        self.assertEqual(self.kassa.syo_maukkaasti_kateisella(300), 300)
        self.assertEqual(self.kassa.kassassa_rahaa_euroina(), 1000)
        self.assertEqual(self.kassa.maukkaat, 0)

    def test_kateisosto_toimii_jos_tarpeaksi_rahaa_edullinen(self):
        self.assertEqual(self.kassa.syo_edullisesti_kateisella(250), 10)
        self.assertEqual(self.kassa.kassassa_rahaa_euroina(), 1002.4)
        self.assertEqual(self.kassa.edulliset, 1)

    def test_kateisosto_toimii_jos_tarpeaksi_rahaa_maukas(self):
        self.assertEqual(self.kassa.syo_maukkaasti_kateisella(450), 50)
        self.assertEqual(self.kassa.kassassa_rahaa_euroina(), 1004)
        self.assertEqual(self.kassa.maukkaat, 1)

    def test_korttiosto_ei_toimi_jos_ei_tarpeaksi_rahaa_edullinen(self):
        maksukortti = Maksukortti(200)
        self.assertEqual(self.kassa.syo_edullisesti_kortilla(maksukortti), False)
        self.assertEqual(maksukortti.saldo_euroina(), 2)
        self.assertEqual(self.kassa.edulliset, 0)

    def test_korttiosto_ei_toimi_jos_ei_tarpeaksi_rahaa_maukas(self):
        maksukortti = Maksukortti(300)
        self.assertEqual(self.kassa.syo_maukkaasti_kortilla(maksukortti), False)
        self.assertEqual(maksukortti.saldo_euroina(), 3)
        self.assertEqual(self.kassa.maukkaat, 0)

    def test_korttiosto_toimii_jos_tarpeaksi_rahaa_edullinen(self):
        self.assertEqual(self.kassa.syo_edullisesti_kortilla(self.maksukortti), True)
        self.assertEqual(self.maksukortti.saldo_euroina(), 7.6)
        self.assertEqual(self.kassa.edulliset, 1)

    def test_korttiosto_toimii_jos_tarpeaksi_rahaa_maukas(self):
        self.assertEqual(self.kassa.syo_maukkaasti_kortilla(self.maksukortti), True)
        self.assertEqual(self.maksukortti.saldo_euroina(), 6)
        self.assertEqual(self.kassa.maukkaat, 1)

    def test_kortille_positiivinen_lataus_kasvattaa_kassan_ja_kortin_saldoa(self):
        self.kassa.lataa_rahaa_kortille(self.maksukortti, 300)

        self.assertEqual(self.kassa.kassassa_rahaa_euroina(), 1003)
        self.assertEqual(self.maksukortti.saldo_euroina(), 13)

    def test_kortille_negatiivinen_lataus_ei_muuta_kassan_tai_kortin_saldoa(self):
        self.kassa.lataa_rahaa_kortille(self.maksukortti, -300)

        self.assertEqual(self.kassa.kassassa_rahaa_euroina(), 1000)
        self.assertEqual(self.maksukortti.saldo_euroina(), 10)

