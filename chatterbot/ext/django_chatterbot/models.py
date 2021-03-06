from django.db import models


class Statement(models.Model):
    """
    A short (<255) character message that is part of a dialog.
    """

    text = models.CharField(
        unique=True,
        blank=False,
        null=False,
        max_length=255
    )

    extra_data = models.CharField(max_length=500)

    def __str__(self):
        if len(self.text.strip()) > 60:
            return '{}...'.format(self.text[:57])
        elif len(self.text.strip()) > 0:
            return self.text
        return '<empty>'

    def add_extra_data(self, key, value):
        """
        Add extra data to the extra_data field.
        """
        import json

        if not self.extra_data:
            self.extra_data = '{}'

        extra_data = json.loads(self.extra_data)
        extra_data[key] = value

        self.extra_data = json.dumps(extra_data)

    def add_response(self, statement):
        """
        Add a response to this statement.
        """
        response, created = self.in_response_to.get_or_create(
            statement=self,
            response=statement
        )

        if created:
            response.occurrence += 1
            response.save()

    def remove_response(self, response_text):
        """
        Removes a response from the statement's response list based
        on the value of the response text.

        :param response_text: The text of the response to be removed.
        :type response_text: str
        """
        is_deleted = False
        response = self.in_response_to.filter(response__text=response_text)

        if response.exists():
            is_deleted = True

        return is_deleted

    def get_response_count(self, statement):
        """
        Find the number of times that the statement has been used
        as a response to the current statement.

        :param statement: The statement object to get the count for.
        :type statement: chatterbot.conversation.statement.Statement

        :returns: Return the number of times the statement has been used as a response.
        :rtype: int
        """
        try:
            response = self.in_response_to.get(response__text=statement.text)
            return response.occurrence
        except Response.DoesNotExist:
            return 0

    def serialize(self):
        """
        :returns: A dictionary representation of the statement object.
        :rtype: dict
        """
        import json
        data = {}

        if not self.extra_data:
            self.extra_data = '{}'

        data['text'] = self.text
        data['in_response_to'] = []
        data['extra_data'] = json.loads(self.extra_data)

        for response in self.in_response_to.all():
            data['in_response_to'].append(response.serialize())

        return data


class Response(models.Model):
    """
    Connection between a response and the statement that triggered it.

    Comparble to a ManyToMany "through" table, but without the M2M indexing/relations.

    Only the text and number of times it has occurred are currently stored.
    Might be useful to store additional features like language, location(s)/region(s),
    first created datetime(s), username, user full name, user gender, etc.
    A the very least occurrences should be an FK to a meta-data table with this info.
    """

    statement = models.ForeignKey(
        'Statement',
        related_name='in_response_to'
    )

    response = models.ForeignKey(
        'Statement',
        related_name='+'
    )

    unique_together = (('statement', 'response'),)

    occurrence = models.PositiveIntegerField(default=1)

    def __str__(self):
        return '{} => {}'.format(
            self.statement.text if len(self.statement.text) <= 20 else self.statement.text[:17] + '...',
            self.response.text if len(self.response.text) <= 40 else self.response.text[:37] + '...'
        )
