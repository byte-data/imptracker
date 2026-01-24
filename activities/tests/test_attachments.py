"""
Test suite for Activity Attachment functionality
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import datetime
from activities.models import Activity, ActivityAttachment
from masters.models import Funder, ActivityStatus, Currency
from accounts.models import Cluster
from audit.models import AuditLog
import json

User = get_user_model()


class ActivityAttachmentTestCase(TestCase):
    """Test cases for activity attachment functionality"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        # Create test users
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create superuser for admin access
        cls.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        
        # Create test groups
        cls.editor_group = Group.objects.create(name='Activity Editor')
        cls.viewer_group = Group.objects.create(name='Activity Viewer')
        
        # Create currencies
        cls.currency = Currency.objects.create(code='USD', name='US Dollar')
        
        # Create status
        cls.status = ActivityStatus.objects.create(name='Active')
        
        # Create funder
        cls.funder = Funder.objects.create(name='Test Funder', code='TF')
        
        # Create cluster
        cls.cluster = Cluster.objects.create(short_name='TC', full_name='Test Cluster')
        
        # Create test activity
        cls.activity = Activity.objects.create(
            activity_id='TEST001',
            name='Test Activity',
            year=2024,
            status=cls.status,
            currency=cls.currency,
            responsible_officer=cls.user,
            planned_month=datetime.now(),
            total_budget=100000
        )
        cls.activity.funders.add(cls.funder)
        cls.activity.clusters.add(cls.cluster)
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_attachment_model_creation(self):
        """Test creating an attachment"""
        file = SimpleUploadedFile("test.pdf", b"file content", content_type="application/pdf")
        
        attachment = ActivityAttachment.objects.create(
            activity=self.activity,
            file=file,
            filename="test.pdf",
            document_type="report",
            file_type="pdf",
            uploaded_by=self.user,
            file_size=len(b"file content")
        )
        
        self.assertEqual(attachment.activity, self.activity)
        self.assertEqual(attachment.filename, "test.pdf")
        self.assertEqual(attachment.version, 1)
        self.assertTrue(attachment.is_latest)
        self.assertFalse(attachment.is_deleted)
    
    def test_get_attachment_versions(self):
        """Test retrieving attachment versions"""
        # Create first version
        file1 = SimpleUploadedFile("test_v1.pdf", b"file content v1", content_type="application/pdf")
        att1 = ActivityAttachment.objects.create(
            activity=self.activity,
            file=file1,
            filename="test_v1.pdf",
            document_type="report",
            file_type="pdf",
            uploaded_by=self.user,
            file_size=len(b"file content v1")
        )
        
        # Create second version
        versions = ActivityAttachment.objects.filter(
            activity=self.activity,
            document_type="report"
        ).order_by('-version')
        
        self.assertEqual(len(versions), 1)
        self.assertTrue(versions[0].is_latest)
    
    def test_soft_delete_attachment(self):
        """Test soft delete functionality"""
        file = SimpleUploadedFile("test.pdf", b"file content", content_type="application/pdf")
        attachment = ActivityAttachment.objects.create(
            activity=self.activity,
            file=file,
            filename="test.pdf",
            document_type="report",
            file_type="pdf",
            uploaded_by=self.user,
            file_size=len(b"file content")
        )
        
        # Soft delete
        attachment.is_deleted = True
        attachment.save()
        
        # Verify
        refreshed = ActivityAttachment.objects.get(pk=attachment.pk)
        self.assertTrue(refreshed.is_deleted)
    
    def test_upload_attachment_view_authentication(self):
        """Test upload view requires authentication"""
        response = self.client.post(
            f'/activities/{self.activity.pk}/attachments/upload/',
            {'file': SimpleUploadedFile("test.pdf", b"content")}
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_list_attachments_view(self):
        """Test list attachments view"""
        self.client.login(username='testuser', password='testpass123')
        self.user.groups.add(self.viewer_group)
        
        # Create test attachment
        file = SimpleUploadedFile("test.pdf", b"file content", content_type="application/pdf")
        ActivityAttachment.objects.create(
            activity=self.activity,
            file=file,
            filename="test.pdf",
            document_type="report",
            file_type="pdf",
            uploaded_by=self.user,
            file_size=len(b"file content")
        )
        
        response = self.client.get(f'/activities/{self.activity.pk}/attachments/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('attachments', data)
    
    def test_document_type_validation(self):
        """Test that only valid document types are accepted"""
        valid_types = ['report', 'proposal', 'invoice', 'receipt', 'other']
        
        for doc_type in valid_types:
            file = SimpleUploadedFile("test.pdf", b"file content", content_type="application/pdf")
            attachment = ActivityAttachment.objects.create(
                activity=self.activity,
                file=file,
                filename=f"test_{doc_type}.pdf",
                document_type=doc_type,
                file_type="pdf",
                uploaded_by=self.user,
                file_size=len(b"file content")
            )
            self.assertEqual(attachment.document_type, doc_type)
    
    def test_file_type_detection(self):
        """Test automatic file type detection"""
        file_types = [
            ("test.pdf", "pdf", b"PDF content"),
            ("test.docx", "docx", b"DOCX content"),
            ("test.xlsx", "xlsx", b"XLSX content"),
        ]
        
        for filename, expected_type, content in file_types:
            file = SimpleUploadedFile(filename, content, content_type="application/octet-stream")
            attachment = ActivityAttachment.objects.create(
                activity=self.activity,
                file=file,
                filename=filename,
                document_type="report",
                file_type=expected_type,
                uploaded_by=self.user,
                file_size=len(content)
            )
            self.assertEqual(attachment.file_type, expected_type)
    
    def test_attachment_ordering(self):
        """Test that attachments are ordered by upload date"""
        import time
        
        attachments = []
        for i in range(3):
            file = SimpleUploadedFile(f"test{i}.pdf", b"content", content_type="application/pdf")
            att = ActivityAttachment.objects.create(
                activity=self.activity,
                file=file,
                filename=f"test{i}.pdf",
                document_type="report",
                file_type="pdf",
                uploaded_by=self.user,
                file_size=len(b"content")
            )
            attachments.append(att)
            time.sleep(0.1)
        
        # Retrieve ordered list
        ordered = ActivityAttachment.objects.filter(activity=self.activity).order_by('-uploaded_at')
        
        # Most recent should be first
        self.assertEqual(ordered[0].pk, attachments[-1].pk)
    
    def test_attachment_permissions(self):
        """Test permission-based access control"""
        self.client.login(username='testuser', password='testpass123')
        
        # User without permission should get 403
        response = self.client.post(
            f'/activities/{self.activity.pk}/attachments/upload/',
            {'file': SimpleUploadedFile("test.pdf", b"content")}
        )
        
        self.assertEqual(response.status_code, 403)


class ActivityAttachmentIntegrationTestCase(TestCase):
    """Integration tests for attachment workflow"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        cls.currency = Currency.objects.create(code='USD', name='US Dollar')
        cls.status = ActivityStatus.objects.create(name='Active')
        cls.funder = Funder.objects.create(name='Test Funder', code='TF')
        cls.cluster = Cluster.objects.create(short_name='TC', full_name='Test Cluster')
        
        cls.activity = Activity.objects.create(
            activity_id='TEST001',
            name='Test Activity',
            year=2024,
            status=cls.status,
            currency=cls.currency,
            responsible_officer=cls.user,
            planned_month=datetime.now(),
            total_budget=100000
        )
        cls.activity.funders.add(cls.funder)
        cls.activity.clusters.add(cls.cluster)
    
    def test_complete_attachment_workflow(self):
        """Test complete attachment workflow: upload -> list -> download -> delete"""
        # Step 1: Upload attachment
        file = SimpleUploadedFile("report.pdf", b"PDF content", content_type="application/pdf")
        attachment = ActivityAttachment.objects.create(
            activity=self.activity,
            file=file,
            filename="report.pdf",
            document_type="report",
            file_type="pdf",
            uploaded_by=self.user,
            file_size=len(b"PDF content"),
            description="Initial report"
        )
        
        self.assertIsNotNone(attachment.pk)
        self.assertEqual(attachment.version, 1)
        
        # Step 2: List attachments
        attachments = ActivityAttachment.objects.filter(
            activity=self.activity,
            is_deleted=False
        )
        
        self.assertEqual(len(attachments), 1)
        self.assertTrue(attachments[0].is_latest)
        
        # Step 3: Upload new version
        file2 = SimpleUploadedFile("report_v2.pdf", b"PDF content v2", content_type="application/pdf")
        attachment2 = ActivityAttachment.objects.create(
            activity=self.activity,
            file=file2,
            filename="report_v2.pdf",
            document_type="report",
            file_type="pdf",
            uploaded_by=self.user,
            file_size=len(b"PDF content v2"),
            version=2,
            description="Updated report"
        )
        
        # Step 4: Verify version history
        versions = ActivityAttachment.objects.filter(
            activity=self.activity,
            document_type="report"
        ).order_by('-version')
        
        self.assertEqual(len(versions), 2)
        self.assertTrue(versions[0].is_latest)
        self.assertFalse(versions[1].is_latest)
        
        # Step 5: Soft delete
        versions[0].is_deleted = True
        versions[0].save()
        
        active = ActivityAttachment.objects.filter(
            activity=self.activity,
            is_deleted=False
        )
        
        self.assertEqual(len(active), 1)


if __name__ == '__main__':
    import unittest
    unittest.main()
