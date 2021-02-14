from ledger.accounts.models import EmailUser
from rest_framework import serializers

from ledger_common.models import AbstractProposal


class EmailUserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = EmailUser
        fields = (
                'id',
                'email',
                'first_name',
                'last_name',
                'title',
                'organisation',
                'name'
                )

    def get_name(self, obj):
        return obj.get_full_name()

class AbstractProposalSerializer(serializers.ModelSerializer):

    class Meta:
        model = AbstractProposal
        fields = (
                'id',
                )
        read_only_fields=(
                'id',
                )

