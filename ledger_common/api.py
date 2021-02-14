import re
import traceback
import os

import json

import pytz
from ledger.settings_base import TIME_ZONE, DATABASES
from django.db.models import Q
from django.db import transaction, connection
from django.core.exceptions import ValidationError
from rest_framework import viewsets, serializers, status, views
from rest_framework.decorators import detail_route, list_route, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from ledger.accounts.models import EmailUser
from datetime import datetime

from django.http import HttpResponse#, JsonResponse, Http404

from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework.pagination import PageNumberPagination
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework_datatables.renderers import DatatablesRenderer

from ledger_common.models import AbstractProposal
from ledger_common.serializers import AbstractProposalSerializer

import logging
logger = logging.getLogger(__name__)


class AbstractProposalViewSet(viewsets.ModelViewSet):
    #import ipdb; ipdb.set_trace()
    #queryset = Proposal.objects.all()
    queryset = AbstractProposal.objects.none()
    serializer_class = AbstractProposalSerializer

    def internal_serializer_class(self):
        try:
            return InternalProposalSerializer
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            handle_validation_error(e)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET',])
    def assign_request_user(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.assign_officer(request,request.user)
            #serializer = InternalProposalSerializer(instance,context={'request':request})
            serializer_class = self.internal_serializer_class()
            serializer = serializer_class(instance,context={'request':request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST',])
    def assign_to(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            user_id = request.data.get('assessor_id',None)
            user = None
            if not user_id:
                raise serializers.ValidationError('An assessor id is required')
            try:
                user = EmailUser.objects.get(id=user_id)
            except EmailUser.DoesNotExist:
                raise serializers.ValidationError('A user with the id passed in does not exist')
            instance.assign_officer(request,user)
            #serializer = InternalProposalSerializer(instance,context={'request':request})
            serializer_class = self.internal_serializer_class()
            serializer = serializer_class(instance,context={'request':request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET',])
    def unassign(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.unassign(request)
            #serializer = InternalProposalSerializer(instance,context={'request':request})
            serializer_class = self.internal_serializer_class()
            serializer = serializer_class(instance,context={'request':request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

