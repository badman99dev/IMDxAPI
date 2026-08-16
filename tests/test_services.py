"""Smoke tests for IMDxAPI services (require live internet + IMDb endpoint)."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

from app.services.imdb_client import ImdbClient
from app.services import title_service, name_service, title_sub_service, name_sub_service


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


class TestTitleSubEndpoints(unittest.TestCase):
    """Phase-2: Tiffara title sub-endpoints."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.client = ImdbClient(cache_ttl=120)

    def tearDown(self):
        self.loop.run_until_complete(self.client.close())
        self.loop.close()

    def test_seasons(self):
        r = self.loop.run_until_complete(
            title_sub_service.list_title_seasons(self.client, "tt0944947")
        )
        self.assertGreater(len(r.seasons), 0)
        self.assertTrue(all(s.episodeCount for s in r.seasons))

    def test_episodes(self):
        r = self.loop.run_until_complete(
            title_sub_service.list_title_episodes(self.client, "tt0944947", season="1", limit=3)
        )
        self.assertGreater(r.totalCount, 0)
        self.assertEqual(len(r.episodes), 3)
        self.assertTrue(all(e.season == "1" for e in r.episodes))
        self.assertIsNotNone(r.episodes[1].title)

    def test_credits(self):
        r = self.loop.run_until_complete(
            title_sub_service.list_title_credits(self.client, "tt1375666", categories=["actor"], limit=3)
        )
        self.assertGreater(r.totalCount, 0)
        self.assertTrue(all(c.name.id for c in r.credits))
        self.assertIsNotNone(r.credits[0].characters)

    def test_release_dates(self):
        r = self.loop.run_until_complete(
            title_sub_service.list_title_release_dates(self.client, "tt1375666", limit=2)
        )
        self.assertGreater(len(r.releaseDates), 0)
        self.assertTrue(r.nextPageToken)

    def test_akas(self):
        r = self.loop.run_until_complete(title_sub_service.list_title_akas(self.client, "tt1375666"))
        self.assertGreater(len(r.akas), 0)

    def test_images(self):
        r = self.loop.run_until_complete(
            title_sub_service.list_title_images(self.client, "tt1375666", types=["poster"], limit=3)
        )
        self.assertGreater(r.totalCount, 0)
        self.assertTrue(all(i.type == "poster" for i in r.images))

    def test_videos(self):
        r = self.loop.run_until_complete(title_sub_service.list_title_videos(self.client, "tt1375666", limit=3))
        self.assertGreater(len(r.videos), 0)
        self.assertEqual(r.videos[0].type, "trailer")

    def test_awards(self):
        r = self.loop.run_until_complete(
            title_sub_service.list_title_award_nominations(self.client, "tt1375666", limit=3)
        )
        self.assertGreater(len(r.awardNominations), 0)
        self.assertIsNotNone(r.awardNominations[0].event.name)

    def test_parents_guide(self):
        r = self.loop.run_until_complete(
            title_sub_service.list_title_parents_guide(self.client, "tt1375666")
        )
        self.assertGreater(len(r.parentsGuide), 0)
        cats = {p.category for p in r.parentsGuide}
        self.assertIn("SEXUAL_CONTENT", cats)

    def test_certificates(self):
        r = self.loop.run_until_complete(
            title_sub_service.list_title_certificates(self.client, "tt1375666")
        )
        self.assertGreater(len(r.certificates), 0)
        self.assertTrue(all(c.country.code for c in r.certificates))

    def test_company_credits(self):
        r = self.loop.run_until_complete(
            title_sub_service.list_title_company_credits(self.client, "tt1375666", limit=3)
        )
        self.assertGreater(len(r.companyCredits), 0)
        self.assertTrue(all(c.company.name for c in r.companyCredits))

    def test_box_office(self):
        r = self.loop.run_until_complete(
            title_sub_service.get_title_box_office(self.client, "tt1375666")
        )
        self.assertIsNotNone(r)
        self.assertEqual(r.domesticGross.currency, "USD")
        self.assertIsNotNone(r.productionBudget)

    def test_box_office_not_found(self):
        r = self.loop.run_until_complete(
            title_sub_service.get_title_box_office(self.client, "tt9999999")
        )
        self.assertIsNone(r)


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


class TestNameSubEndpoints(unittest.TestCase):
    """Phase-3: Tiffara name sub-endpoints + charts + interests."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.client = ImdbClient(cache_ttl=120)

    def tearDown(self):
        self.loop.run_until_complete(self.client.close())
        self.loop.close()

    def test_filmography(self):
        r = self.loop.run_until_complete(
            name_sub_service.list_name_filmography(
                self.client, "nm0634240", categories=["director"], limit=3
            )
        )
        self.assertGreater(r.totalCount, 0)
        self.assertTrue(all(c.category == "director" for c in r.credits))
        self.assertIsNotNone(r.credits[0].title.primaryTitle)

    def test_name_images(self):
        r = self.loop.run_until_complete(
            name_sub_service.list_name_images(
                self.client, "nm0634240", types=["poster"], limit=2
            )
        )
        self.assertGreater(r.totalCount, 0)
        self.assertTrue(all(i.type == "poster" for i in r.images))

    def test_relationships(self):
        r = self.loop.run_until_complete(
            name_sub_service.get_name_relationships(self.client, "nm0634240")
        )
        self.assertGreater(len(r.relationships), 0)
        self.assertTrue(all(rel.relationType for rel in r.relationships))

    def test_trivia(self):
        r = self.loop.run_until_complete(
            name_sub_service.list_name_trivia(self.client, "nm0634240", limit=2)
        )
        self.assertGreater(r.totalCount, 0)
        self.assertTrue(all(t.text for t in r.triviaEntries))
        self.assertIsNotNone(r.triviaEntries[0].voteCount)

    def test_starmeter(self):
        r = self.loop.run_until_complete(
            name_sub_service.get_starmeter_chart(self.client, limit=3)
        )
        self.assertEqual(len(r.names), 3)
        self.assertTrue(all(n.meterRanking.currentRank for n in r.names))
        self.assertTrue(r.nextPageToken)

    def test_batch_names(self):
        names = self.loop.run_until_complete(
            name_sub_service.batch_get_names(self.client, ["nm0634240", "nm0000138"])
        )
        self.assertEqual(len(names), 2)
        self.assertEqual(names[0].displayName, "Christopher Nolan")

    def test_interest_categories(self):
        r = self.loop.run_until_complete(
            name_sub_service.list_interest_categories(self.client)
        )
        self.assertGreater(len(r.categories), 0)
        self.assertTrue(all(cat.interests for cat in r.categories))

    def test_interest_by_id(self):
        r = self.loop.run_until_complete(name_sub_service.get_interest(self.client, "in0000001"))
        self.assertIsNotNone(r)
        self.assertEqual(r.name, "Action")
        self.assertFalse(r.isSubgenre)


if __name__ == "__main__":
    unittest.main(verbosity=2)