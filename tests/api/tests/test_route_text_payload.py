from unittest import main

from .helpers import api, test_base


text = """
    Nocturne

    Ruislinnun laulu korvissani,
    tähkäpäiden päällä täysi kuu;
    kesä-yön on onni omanani,
    kaskisavuun laaksot verhouu.
    En ma iloitse, en sure, huokaa;
    mutta metsän tummuus mulle tuokaa,
    puunto pilven, johon päivä hukkuu,
    siinto vaaran tuulisen, mi nukkuu,
    tuoksut vanamon ja varjot veen;
    niistä sydämeni laulun teen.

    Sulle laulan neiti, kesäheinä,
    sydämeni suuri hiljaisuus,
    uskontoni, soipa säveleinä,
    tammenlehvä-seppel vehryt, uus.
    En ma enää aja virvatulta,
    onpa kädessäni onnen kulta;
    pienentyy mun ympär’ elon piiri;
    aika seisoo, nukkuu tuuliviiri;
    edessäni hämäräinen tie
    tuntemattomahan tupaan vie.

    Eino Leino
"""


class RouteTextPayloadCases:
    class RouteTextPayloadBase(test_base.TestBase):
        def test_text_in_json(self):
            json = self.res.json()
            arg = 'text'
            self.assertIn(arg, json)
            self.assertEqual(json[arg], text)


class TestRouteTextPayloadPost(RouteTextPayloadCases.RouteTextPayloadBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.post(
            cls.v['AGW'] + '/test_route_text_payload_post',
            text=text
        )


class TestRouteTextPayloadPut(RouteTextPayloadCases.RouteTextPayloadBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.put(
            cls.v['AGW'] + '/test_route_text_payload_put',
            text=text
        )


class TestRouteTextPayloadPatch(RouteTextPayloadCases.RouteTextPayloadBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.patch(
            cls.v['AGW'] + '/test_route_text_payload_patch',
            text=text
        )


if __name__ == '__main__':
    main()
