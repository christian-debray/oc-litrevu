from django.test import TestCase
from app.models import User, UserFollows, Ticket, Review
from app.posts import own_or_followed_reviews, own_or_followed_tickets
from app.subscriptions import followed_users, followers
from django.db import models
from itertools import chain


class UserFollowsTestCase(TestCase):
    fixtures = ["tests.yaml"]

    def test_followed_users(self):
        """Finds who follows who"""
        expectations = [
            {"user.pk": 2, "follows": [3, 4]},
            {"user.pk": 3, "follows": [2, 4, 6]},
            {"user.pk": 4, "follows": []},
            {"user.pk": 5, "follows": [2, 3, 4, 6]},
            {"user.pk": 6, "follows": [3, 4]},
        ]
        for test_data in expectations:
            user = User.objects.get(pk=test_data["user.pk"])
            follows = sorted([x.pk for x in followed_users(user)])
            self.assertListEqual(
                follows,
                test_data["follows"],
                f"Results don't match for user #{user.pk} {user}, expected {test_data['follows']}, found {follows}",
            )

    def test_followed_by(self):
        """Finds who is followed by whom"""
        expectations = [
            {"user.pk": 2, "followed_by": [3, 5]},
            {"user.pk": 3, "followed_by": [2, 5, 6]},
            {"user.pk": 4, "followed_by": [2, 3, 5, 6]},
            {"user.pk": 5, "followed_by": []},
            {"user.pk": 6, "followed_by": [3, 5]},
        ]
        for test_data in expectations:
            user = User.objects.get(pk=test_data["user.pk"])
            followed_by = sorted([x.pk for x in followers(user)])
            self.assertListEqual(
                followed_by,
                test_data["followed_by"],
                f"Results don't match for user #{user.pk} {user}, expected {test_data['followed_by']}, found {followed_by}",
            )


class TicketUserManagerTestCase(TestCase):
    fixtures = ["tests.yaml"]

    def test_find_tickets_by_author(self):
        """Finds all tickets for each user"""
        expectations = [
            {"user.pk": 2, "tickets": [1, 2]},
            {"user.pk": 3, "tickets": [3]},
            {"user.pk": 4, "tickets": [4]},
            {"user.pk": 5, "tickets": []},
            {"user.pk": 6, "tickets": []},
        ]
        for test_data in expectations:
            user = User.objects.get(pk=test_data["user.pk"])
            tickets = Ticket.objects.filter(user=user)
            self.assertIsInstance(tickets, models.QuerySet)
            ticket_ids = sorted([x.pk for x in tickets])
            self.assertListEqual(
                ticket_ids,
                test_data["tickets"],
                f"Tickets don't match for user #{user.pk} {user}, expected {test_data['tickets']}, found {ticket_ids}",
            )

    def test_find_tickets_followed_by_user(self):
        """Finds all tickets posted by users followed by user."""
        expectations = [
            {"user.pk": 2, "expected": [1, 2, 3, 4]},
            {"user.pk": 3, "expected": [1, 2, 3, 4]},
            {"user.pk": 4, "expected": [4]},
            {"user.pk": 5, "expected": [1, 2, 3, 4]},
            {"user.pk": 6, "expected": [3, 4]},
        ]
        for test_data in expectations:
            user = User.objects.get(pk=test_data["user.pk"])
            tickets = own_or_followed_tickets(user)
            self.assertIsInstance(tickets, models.QuerySet)
            ticket_ids = sorted([x.pk for x in tickets])
            self.assertListEqual(
                ticket_ids,
                test_data["expected"],
                f"""Results don't match for user #{user.pk} {user},
                    expected {test_data["expected"]}, found {ticket_ids}""",
            )


class ReviewUserManagerTestCase(TestCase):
    fixtures = ["tests.yaml"]

    def test_find_reviews_by_author(self):
        """Finds all tickets for each user"""
        expectations = [
            {"user.pk": 2, "reviews": []},
            {"user.pk": 3, "reviews": [1]},
            {"user.pk": 4, "reviews": [3]},
            {"user.pk": 5, "reviews": [2]},
            {"user.pk": 6, "reviews": []},
        ]
        for test_data in expectations:
            user = User.objects.get(pk=test_data["user.pk"])
            reviews = Review.objects.filter(user=user)
            self.assertIsInstance(reviews, models.QuerySet)
            review_ids = sorted([x.pk for x in reviews])
            self.assertListEqual(
                review_ids,
                test_data["reviews"],
                f"results don't match for user #{user.pk} {user}: expected {test_data['reviews']}, found {review_ids}",
            )

    def test_find_reviews_followed_by_user(self):
        """Finds all reviews followed by a user"""
        expectations = [
            {"user.pk": 2, "reviews": [1, 2, 3]},
            {"user.pk": 3, "reviews": [1, 3]},
            {"user.pk": 4, "reviews": [3]},
            {"user.pk": 5, "reviews": [1, 2, 3]},
            {"user.pk": 6, "reviews": [1, 3]},
        ]
        for test_data in expectations:
            user = User.objects.get(pk=test_data["user.pk"])
            reviews = own_or_followed_reviews(user)
            self.assertIsInstance(reviews, models.QuerySet)
            review_ids = sorted([x.pk for x in reviews])
            self.assertListEqual(
                review_ids,
                test_data["reviews"],
                f"results don't match for user #{user.pk} {user}: expected {test_data['reviews']}, found {review_ids}",
            )


class UserFeedTestCase(TestCase):
    def setUp(self):
        alice = User.objects.create(username="alice", password="Ab1;mlkjhgfdsq")
        bob = User.objects.create(username="bob", password="Ab1;mlkjhgfdsq")
        cecile = User.objects.create(username="cecile", password="Ab1;mlkjhgfdsq")
        UserFollows.objects.create(user=alice, followed_user=bob)
        UserFollows.objects.create(user=bob, followed_user=cecile)
        UserFollows.objects.create(user=cecile, followed_user=bob)

    def _user_feed(self, user):
        review_query_set = own_or_followed_reviews(user)
        ticket_query_set = own_or_followed_tickets(user)
        return sorted(
            chain(review_query_set, ticket_query_set),
            key=lambda x: x.time_created,
        )

    def test_bob_posts_ticket(self):
        """Bob posts a ticket.
        - Alice should see bob's ticket
        """
        bob = User.objects.get(username="bob")
        alice = User.objects.get(username="alice")
        bob_ticket = Ticket.objects.create(
            user=bob, title="Ubik", description="requested by bob"
        )
        alice_feed = own_or_followed_tickets(user=alice)
        self.assertIn(bob_ticket, alice_feed)

    def test_cecile_reviews_ticket_from_bob(self):
        """Bob posts a ticket, cecil posts a review for bob's ticket.
        - Bob should see cecile's review.
        - Cecile should see bob's ticket.
        - Alice should see bob's ticket.
        - Alice should not see cecile's review.
        """
        bob = User.objects.get(username="bob")
        cecile = User.objects.get(username="cecile")
        alice = User.objects.get(username="alice")
        bob_ticket = Ticket.objects.create(
            user=bob, title="Ubik", description="requested by bob"
        )
        cecile_review = Review.objects.create(
            user=cecile,
            ticket=bob_ticket,
            rating=5,
            headline="fantastic",
        )
        bob_feed = own_or_followed_reviews(user=bob)
        cecile_feed = own_or_followed_tickets(user=cecile)
        self.assertIn(bob_ticket, cecile_feed)
        self.assertIn(cecile_review, bob_feed)
        alice_feed = self._user_feed(alice)
        self.assertIn(bob_ticket, alice_feed)
        self.assertNotIn(cecile_review, alice_feed)

    def test_alice_reviews_ticket_from_bob(self):
        """Bob posts a ticket. Alice sees the ticket and posts a review to bob's ticket.
        - Alice should see bob's ticket
        - Cecile should see bob's ticket
        - Bob should see Alice's review
        - Cecile should not see Alice's review.
        """
        bob = User.objects.get(username="bob")
        alice = User.objects.get(username="alice")
        cecile = User.objects.get(username="cecile")
        bob_ticket = Ticket.objects.create(
            user=bob, title="Ubik", description="requested by bob"
        )
        alice_review = Review.objects.create(
            user=alice,
            ticket=bob_ticket,
            rating=3,
            headline="Not bad",
            body="alice reviewd bob's ticket, bob should see this review even though he doesn't follow alice.",
        )
        bob_feed = self._user_feed(bob)
        alice_feed = self._user_feed(alice)
        cecile_feed = self._user_feed(cecile)
        self.assertIn(bob_ticket, alice_feed)
        self.assertIn(alice_review, alice_feed)
        self.assertIn(bob_ticket, cecile_feed)
        self.assertNotIn(alice_review, cecile_feed)
        self.assertIn(bob_ticket, bob_feed)
        self.assertIn(alice_review, bob_feed)
