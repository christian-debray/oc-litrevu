from django.core.management.base import BaseCommand, CommandError
from app.models import User, Ticket, Review, UserFollows
from django.db import connection
from django.db.models import Model


class Command(BaseCommand):
    help = (
        "Clear the data from all models in the database, but keeps the data structure. Use this before a loaddata."
    )

    def handle(self, *args, **kwargs):
        model_list: list[Model] = reversed([User, Ticket,  Review, UserFollows])
        try:
            connection.cursor()
            with connection.cursor() as cursor:
                for m in model_list:
                    table_name = m._meta.db_table
                    sql = "DELETE FROM `%s`" % table_name
                    cursor.execute(sql)
                    self.stdout.write("Cleared all data from table %s " % self.style.SQL_TABLE(table_name))
        except Exception as e:
            raise CommandError("Failed to clear the database: %s" % str(e))
        self.stdout.write(
            self.style.SUCCESS(
                "Succesfully cleared the data from all models. Migration state remains unchanged."
            )
        )
