from django.test import TestCase
from app.models import User, Ticket, Review
from app.subscriptions import followed_users
from django.db import models


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
                f"Resulst don't match for user #{user.pk} {user}, expected {test_data['follows']}, found {follows}"
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
            tickets = Ticket.with_user_manager.own(user)
            self.assertIsInstance(tickets, models.QuerySet)
            ticket_ids = sorted([x.pk for x in tickets])
            self.assertListEqual(
                ticket_ids,
                test_data["tickets"],
                f"Tickets don't match for user #{user.pk} {user}, expected {test_data['tickets']}, found {ticket_ids}"
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
            tickets = Ticket.with_user_manager.own_or_followed(user)
            self.assertIsInstance(tickets, models.QuerySet)
            ticket_ids = sorted([x.pk for x in tickets])
            self.assertListEqual(
                ticket_ids,
                test_data["expected"],
                f"""Results don't match for user #{user.pk} {user},
                    expected {test_data["expected"]}, found {ticket_ids}"""
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
            reviews = Review.with_user_manager.own(user)
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
            {"user.pk": 2, "reviews": [1, 3]},
            {"user.pk": 3, "reviews": [1, 3]},
            {"user.pk": 4, "reviews": [3]},
            {"user.pk": 5, "reviews": [1, 2, 3]},
            {"user.pk": 6, "reviews": [1, 3]},
        ]
        for test_data in expectations:
            user = User.objects.get(pk=test_data["user.pk"])
            reviews = Review.with_user_manager.own_or_followed(user)
            self.assertIsInstance(reviews, models.QuerySet)
            review_ids = sorted([x.pk for x in reviews])
            self.assertListEqual(
                review_ids,
                test_data["reviews"],
                f"results don't match for user #{user.pk} {user}: expected {test_data['reviews']}, found {review_ids}",
            )
