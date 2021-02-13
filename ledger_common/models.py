from __future__ import unicode_literals
import os

from django.contrib.gis.db.models import MultiPolygonField
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_delete
from django.utils.encoding import python_2_unicode_compatible
from django.core.exceptions import ValidationError
from ledger.accounts.models import EmailUser, Document, RevisionedMixin
from django.contrib.postgres.fields.jsonb import JSONField


@python_2_unicode_compatible
class AbstractRegion(models.Model):
    name = models.CharField(max_length=200, unique=True)
    forest_region = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']
        abstract = True
        #app_label = 'disturbance'

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class AbstractDistrict(models.Model):
    region = models.ForeignKey(Region, related_name='districts')
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=3)
    archive_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['name']
        abstract = True
        #app_label = 'disturbance'

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class AbstractApplicationType(models.Model):

    APPLICATION_TYPES = ()

    DOMAIN_USED_CHOICES = ()

    # name = models.CharField(max_length=64, unique=True)
    name = models.CharField(
        verbose_name='Application Type name',
        max_length=64,
        choices=APPLICATION_TYPES,
    )
    order = models.PositiveSmallIntegerField(default=0)
    visible = models.BooleanField(default=True)
    application_fee = models.DecimalField(max_digits=6, decimal_places=2)
    oracle_code_application = models.CharField(max_length=50)
    is_gst_exempt = models.BooleanField(default=True)
    domain_used = models.CharField(max_length=40, choices=DOMAIN_USED_CHOICES, default=DOMAIN_USED_CHOICES[0][0])

    class Meta:
        ordering = ['order', 'name']
        abstract = True
        #app_label = 'disturbance'

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class UserAction(models.Model):
    who = models.ForeignKey(EmailUser, null=False, blank=False)
    when = models.DateTimeField(null=False, blank=False, auto_now_add=True)
    what = models.TextField(blank=False)

    def __str__(self):
        return "{what} ({who} at {when})".format(
            what=self.what,
            who=self.who,
            when=self.when
        )

    class Meta:
        abstract = True
        #app_label = 'disturbance'


class CommunicationsLogEntry(models.Model):
    TYPE_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone Call'),
        ('mail', 'Mail'),
        ('person', 'In Person'),
        ('referral_complete', 'Referral Completed'),
    ]
    DEFAULT_TYPE = TYPE_CHOICES[0][0]

    # to = models.CharField(max_length=200, blank=True, verbose_name="To")
    to = models.TextField(blank=True, verbose_name="To")
    fromm = models.CharField(max_length=200, blank=True, verbose_name="From")
    # cc = models.CharField(max_length=200, blank=True, verbose_name="cc")
    cc = models.TextField(blank=True, verbose_name="cc")

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=DEFAULT_TYPE)
    reference = models.CharField(max_length=100, blank=True)
    subject = models.CharField(max_length=200, blank=True, verbose_name="Subject / Description")
    text = models.TextField(blank=True)

    customer = models.ForeignKey(EmailUser, null=True, related_name='+')
    staff = models.ForeignKey(EmailUser, null=True, related_name='+')

    created = models.DateTimeField(auto_now_add=True, null=False, blank=False)

    class Meta:
        abstract = True
        #app_label = 'disturbance'


@python_2_unicode_compatible
class Document(models.Model):
    name = models.CharField(max_length=255, blank=True,
                            verbose_name='name', help_text='')
    description = models.TextField(blank=True,
                                   verbose_name='description', help_text='')
    uploaded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        #app_label = 'disturbance'
        abstract = True

    @property
    def path(self):
        # return self.file.path
        return self._file.path

    @property
    def filename(self):
        return os.path.basename(self.path)

    def __str__(self):
        return self.name or self.filename


@python_2_unicode_compatible
class SystemMaintenance(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def duration(self):
        """ Duration of system maintenance (in mins) """
        return int((self.end_date - self.start_date).total_seconds() / 60.) if self.end_date and self.start_date else ''
        # return (datetime.now(tz=tz) - self.start_date).total_seconds()/60.

    duration.short_description = 'Duration (mins)'

    class Meta:
        abstract = True
        #app_label = 'disturbance'
        verbose_name_plural = "System maintenance"

    def __str__(self):
        return 'System Maintenance: {} ({}) - starting {}, ending {}'.format(self.name, self.description,
                                                                             self.start_date, self.end_date)


class TemporaryDocumentCollection(models.Model):
    # input_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True
        #app_label = 'disturbance'


# temp document obj for generic file upload component
class TemporaryDocument(Document):
    temp_document_collection = models.ForeignKey(
        TemporaryDocumentCollection,
        related_name='documents')
    _file = models.FileField(max_length=255)

    # input_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True
        #app_label = 'disturbance'


class AbstractProposal(RevisionedMixin):
    CUSTOMER_STATUS_TEMP = 'temp'
    CUSTOMER_STATUS_DRAFT = 'draft'
    CUSTOMER_STATUS_WITH_ASSESSOR = 'with_assessor'
    CUSTOMER_STATUS_AMENDMENT_REQUEST = 'amendment_required'
    CUSTOMER_STATUS_APPROVED = 'approved'
    CUSTOMER_STATUS_DECLINED = 'declined'
    CUSTOMER_STATUS_DISCARDED = 'discarded'
    CUSTOMER_STATUS_CHOICES = ((CUSTOMER_STATUS_TEMP, 'Temporary'),
                               (CUSTOMER_STATUS_DRAFT, 'Draft'),
                               (CUSTOMER_STATUS_WITH_ASSESSOR, 'Under Review'),
                               (CUSTOMER_STATUS_AMENDMENT_REQUEST, 'Amendment Required'),
                               (CUSTOMER_STATUS_APPROVED, 'Approved'),
                               (CUSTOMER_STATUS_DECLINED, 'Declined'),
                               (CUSTOMER_STATUS_DISCARDED, 'Discarded'),
                               )
    # List of statuses from above that allow a customer to edit an application.
    CUSTOMER_EDITABLE_STATE = [CUSTOMER_STATUS_TEMP, CUSTOMER_STATUS_DRAFT, CUSTOMER_STATUS_AMENDMENT_REQUEST, ]

    APPLICANT_TYPE_ORGANISATION = 'organisation'
    APPLICANT_TYPE_PROXY = 'proxy' # proxy also represents an individual making an Apiary application
    APPLICANT_TYPE_SUBMITTER = 'submitter'

    # List of statuses from above that allow a customer to view an application (read-only)
    CUSTOMER_VIEWABLE_STATE = ['with_assessor', 'under_review', 'id_required', 'returns_required', 'approved', 'declined']

    PROCESSING_STATUS_TEMP = 'temp'
    PROCESSING_STATUS_DRAFT = 'draft'
    PROCESSING_STATUS_WITH_ASSESSOR = 'with_assessor'
    PROCESSING_STATUS_WITH_REFERRAL = 'with_referral'
    PROCESSING_STATUS_WITH_ASSESSOR_REQUIREMENTS = 'with_assessor_requirements'
    PROCESSING_STATUS_WITH_APPROVER = 'with_approver'
    PROCESSING_STATUS_RENEWAL = 'renewal'
    PROCESSING_STATUS_LICENCE_AMENDMENT = 'licence_amendment'
    PROCESSING_STATUS_AWAITING_APPLICANT_RESPONSE = 'awaiting_applicant_response'
    PROCESSING_STATUS_AWAITING_ASSESSOR_RESPONSE = 'awaiting_assessor_response'
    PROCESSING_STATUS_AWAITING_RESPONSES = 'awaiting_responses'
    PROCESSING_STATUS_READY_FOR_CONDITIONS = 'ready_for_conditions'
    PROCESSING_STATUS_READY_TO_ISSUE = 'ready_to_issue'
    PROCESSING_STATUS_APPROVED = 'approved'
    PROCESSING_STATUS_DECLINED = 'declined'
    PROCESSING_STATUS_DISCARDED = 'discarded'
    PROCESSING_STATUS_CHOICES = ((PROCESSING_STATUS_TEMP, 'Temporary'),
                                 (PROCESSING_STATUS_DRAFT, 'Draft'),
                                 (PROCESSING_STATUS_WITH_ASSESSOR, 'With Assessor'),
                                 (PROCESSING_STATUS_WITH_REFERRAL, 'With Referral'),
                                 (PROCESSING_STATUS_WITH_ASSESSOR_REQUIREMENTS, 'With Assessor (Requirements)'),
                                 (PROCESSING_STATUS_WITH_APPROVER, 'With Approver'),
                                 (PROCESSING_STATUS_RENEWAL, 'Renewal'),
                                 (PROCESSING_STATUS_LICENCE_AMENDMENT, 'Licence Amendment'),
                                 (PROCESSING_STATUS_AWAITING_APPLICANT_RESPONSE, 'Awaiting Applicant Response'),
                                 (PROCESSING_STATUS_AWAITING_ASSESSOR_RESPONSE, 'Awaiting Assessor Response'),
                                 (PROCESSING_STATUS_AWAITING_RESPONSES, 'Awaiting Responses'),
                                 (PROCESSING_STATUS_READY_FOR_CONDITIONS, 'Ready for Conditions'),
                                 (PROCESSING_STATUS_READY_TO_ISSUE, 'Ready to Issue'),
                                 (PROCESSING_STATUS_APPROVED, 'Approved'),
                                 (PROCESSING_STATUS_DECLINED, 'Declined'),
                                 (PROCESSING_STATUS_DISCARDED, 'Discarded'),
                                 )

    ID_CHECK_STATUS_CHOICES = (('not_checked', 'Not Checked'), ('awaiting_update', 'Awaiting Update'),
                               ('updated', 'Updated'), ('accepted', 'Accepted'))

    COMPLIANCE_CHECK_STATUS_CHOICES = (
        ('not_checked', 'Not Checked'), ('awaiting_returns', 'Awaiting Returns'), ('completed', 'Completed'),
        ('accepted', 'Accepted'))

    CHARACTER_CHECK_STATUS_CHOICES = (
        ('not_checked', 'Not Checked'), ('accepted', 'Accepted'))

    REVIEW_STATUS_CHOICES = (
        ('not_reviewed', 'Not Reviewed'), ('awaiting_amendments', 'Awaiting Amendments'), ('amended', 'Amended'),
        ('accepted', 'Accepted'))

    APPLICATION_TYPE_CHOICES = (
        ('new_proposal', 'New Proposal'),
        ('amendment', 'Amendment'),
        ('renewal', 'Renewal'),
    )

    data = JSONField(blank=True, null=True)
    assessor_data = JSONField(blank=True, null=True)
    comment_data = JSONField(blank=True, null=True)
    schema = JSONField(blank=False, null=False)
    proposed_issuance_approval = JSONField(blank=True, null=True)

    customer_status = models.CharField('Customer Status', max_length=40, choices=CUSTOMER_STATUS_CHOICES,
                                       default=CUSTOMER_STATUS_CHOICES[1][0])
    #applicant = models.ForeignKey(Organisation, blank=True, null=True, related_name='proposals')

    lodgement_number = models.CharField(max_length=9, blank=True, default='')
    lodgement_sequence = models.IntegerField(blank=True, default=0)
    lodgement_date = models.DateTimeField(blank=True, null=True)
    proxy_applicant = models.ForeignKey(EmailUser, blank=True, null=True, related_name='disturbance_proxy')
    submitter = models.ForeignKey(EmailUser, blank=True, null=True, related_name='disturbance_proposals')

    assigned_officer = models.ForeignKey(EmailUser, blank=True, null=True, related_name='disturbance_proposals_assigned', on_delete=models.SET_NULL)
    assigned_approver = models.ForeignKey(EmailUser, blank=True, null=True, related_name='disturbance_proposals_approvals', on_delete=models.SET_NULL)
    processing_status = models.CharField('Processing Status', max_length=30, choices=PROCESSING_STATUS_CHOICES,
                                         default=PROCESSING_STATUS_CHOICES[1][0])
    id_check_status = models.CharField('Identification Check Status', max_length=30, choices=ID_CHECK_STATUS_CHOICES,
                                       default=ID_CHECK_STATUS_CHOICES[0][0])
    compliance_check_status = models.CharField('Return Check Status', max_length=30, choices=COMPLIANCE_CHECK_STATUS_CHOICES,
                                            default=COMPLIANCE_CHECK_STATUS_CHOICES[0][0])
    character_check_status = models.CharField('Character Check Status', max_length=30,
                                              choices=CHARACTER_CHECK_STATUS_CHOICES,
                                              default=CHARACTER_CHECK_STATUS_CHOICES[0][0])
    review_status = models.CharField('Review Status', max_length=30, choices=REVIEW_STATUS_CHOICES,
                                     default=REVIEW_STATUS_CHOICES[0][0])

    approval = models.ForeignKey('disturbance.Approval',null=True,blank=True)

    previous_application = models.ForeignKey('self', on_delete=models.PROTECT, blank=True, null=True)
    proposed_decline_status = models.BooleanField(default=False)
    title = models.CharField(max_length=255,null=True,blank=True)

    #activity = models.CharField(max_length=255,null=True,blank=True)
    #tenure = models.CharField(max_length=255,null=True,blank=True)
    #region = models.ForeignKey(Region, null=True, blank=True)
    #district = models.ForeignKey(District, null=True, blank=True)
    #application_type = models.ForeignKey(ApplicationType)
    #approval_level = models.CharField('Activity matrix approval level', max_length=255,null=True,blank=True)
    #approval_level_document = models.ForeignKey(ProposalDocument, blank=True, null=True, related_name='approval_level_document')
    #approval_level_comment = models.TextField(blank=True)
    #approval_comment = models.TextField(blank=True)
    #assessment_reminder_sent = models.BooleanField(default=False)
    #weekly_reminder_sent_date = models.DateField(blank=True, null=True)
    #sub_activity_level1 = models.CharField(max_length=255,null=True,blank=True)
    #sub_activity_level2 = models.CharField(max_length=255,null=True,blank=True)
    #management_area = models.CharField(max_length=255,null=True,blank=True)

    #fee_invoice_references = ArrayField(models.CharField(max_length=50, null=True, blank=True, default=''), null=True, default=fee_invoice_references_default)
    migrated = models.BooleanField(default=False)

    class Meta:
        abstract = True
        #app_label = 'disturbance'
        #ordering = ['-id']

    def __str__(self):
        return str(self.id)

    #Append 'P' to Proposal id to generate Lodgement number. Lodgement number and lodgement sequence are used to generate Reference.
    #def save(self, *args, **kwargs):
    #    super(Proposal, self).save(*args,**kwargs)
    #    if self.lodgement_number == '':
    #        new_lodgment_id = 'P{0:06d}'.format(self.pk)
    #        self.lodgement_number = new_lodgment_id
    #        self.save()


class AbstractApproval(RevisionedMixin):
    STATUS_CURRENT = 'current'
    STATUS_EXPIRED = 'expired'
    STATUS_CANCELLED = 'cancelled'
    STATUS_SURRENDERED = 'surrendered'
    STATUS_SUSPENDED = 'suspended'
    STATUS_CHOICES = (
        (STATUS_CURRENT, 'Current'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_SURRENDERED, 'Surrendered'),
        (STATUS_SUSPENDED, 'Suspended')
    )
    lodgement_number = models.CharField(max_length=9, blank=True, default='')
    status = models.CharField(max_length=40, choices=STATUS_CHOICES,
                                       default=STATUS_CHOICES[0][0])
    #licence_document = models.ForeignKey(ApprovalDocument, blank=True, null=True, related_name='licence_document')
    #cover_letter_document = models.ForeignKey(ApprovalDocument, blank=True, null=True, related_name='cover_letter_document')
    replaced_by = models.ForeignKey('self', blank=True, null=True)
    #current_proposal = models.ForeignKey(Proposal,related_name='approvals')
    #renewal_document = models.ForeignKey(ApprovalDocument, blank=True, null=True, related_name='renewal_document')
    renewal_sent = models.BooleanField(default=False)
    issue_date = models.DateTimeField()
    original_issue_date = models.DateField(auto_now_add=True)
    start_date = models.DateField()
    expiry_date = models.DateField()
    surrender_details = JSONField(blank=True,null=True)
    suspension_details = JSONField(blank=True,null=True)
    #applicant = models.ForeignKey(Organisation,on_delete=models.PROTECT, blank=True, null=True, related_name='disturbance_approvals')
    proxy_applicant = models.ForeignKey(EmailUser,on_delete=models.PROTECT, blank=True, null=True, related_name='disturbance_proxy_approvals')
    extracted_fields = JSONField(blank=True, null=True)
    cancellation_details = models.TextField(blank=True)
    cancellation_date = models.DateField(blank=True, null=True)
    set_to_cancel = models.BooleanField(default=False)
    set_to_suspend = models.BooleanField(default=False)
    set_to_surrender = models.BooleanField(default=False)
    reissued= models.BooleanField(default=False)
    apiary_approval = models.BooleanField(default=False)
    no_annual_rental_fee_until = models.DateField(blank=True, null=True)
    apiary_sites = models.ManyToManyField('ApiarySite', through=ApiarySiteOnApproval, related_name='approval_set')
    migrated = models.BooleanField(default=False)

    class Meta:
        #app_label = 'disturbance'
        abstract = True
        unique_together = ('lodgement_number', 'issue_date')

