"""Smoke tests for IMDxAPI services (require live internet + IMDb endpoint)."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

from app.services.imdb_client import ImdbClient
from app.services import title_service, name_service


class TestTitleService(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.client = ImdbClient(cache_ttl=120)

    def tearDown(self):
        self.loop.run_until_complete(self.client.close())
        self.loop.close()

    def test_get_title(self):
        t = self.loop.run_until_complete(title_service.get_title(self.client, "tt1375666"))
        self.assertIsNotNone(t)
        self.assertEqual(t.primaryTitle, "Inception")
        self.assertEqual(t.type, "movie")
        self.assertEqual(t.startYear, 2010)
        self.assertGreaterEqual(t.rating.aggregateRating, 8.0)
        self.assertIn("Sci-Fi", t.genres)
        self.assertIsNotNone(t.directors)
        self.assertEqual(t.directors[0].displayName, "Christopher Nolan")
        self.assertIsNotNone(t.stars)
        self.assertEqual(t.originCountries[0].code, "US")

    def test_get_title_not_found(self):
        t = self.loop.run_until_complete(title_service.get_title(self.client, "tt9999999"))
        self.assertIsNone(t)

    def test_search(self):
        r = self.loop.run_until_complete(
            title_service.search_titles(self.client, "Batman", limit=5)
        )
        self.assertGreater(len(r.titles), 0)
        self.assertTrue(all(x.id for x in r.titles))

    def test_list_titles_filters(self):
        r = self.loop.run_until_complete(
            title_service.list_titles(
                self.client, genres=["Sci-Fi"], min_aggregate_rating=8.0, limit=5
            )
        )
        self.assertGreaterEqual(r.totalCount, 1000)
        self.assertEqual(len(r.titles), 5)

    def test_list_pagination(self):
        p1 = self.loop.run_until_complete(title_service.list_titles(self.client, limit=3))
        self.assertTrue(p1.nextPageToken)
        p2 = self.loop.run_until_complete(
            title_service.list_titles(self.client, limit=3, page_token=p1.nextPageToken)
        )
        ids1 = {t.id for t in p1.titles}
        ids2 = {t.id for t in p2.titles}
        self.assertTrue(ids1.isdisjoint(ids2))


class TestNameService(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.client = ImdbClient(cache_ttl=120)

    def tearDown(self):
        self.loop.run_until_complete(self.client.close())
        self.loop.close()

    def test_get_name(self):
        n = self.loop.run_until_complete(name_service.get_name(self.client, "nm0634240"))
        self.assertIsNotNone(n)
        self.assertEqual(n.displayName, "Christopher Nolan")
        self.assertEqual(n.birthDate.year, 1970)
        self.assertIn("director", n.primaryProfessions)

    def test_get_name_not_found(self):
        n = self.loop.run_until_complete(name_service.get_name(self.client, "nm9999999"))
        self.assertIsNone(n)


if __name__ == "__main__":
    unittest.main(verbosity=2)