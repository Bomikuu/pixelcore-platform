from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from businesses.models import Business, BusinessDevice, BusinessMembership
from businesses.services import issue_device_pairing_code, pair_device
from scheduling.models import StaffProfile
from .services import issue_attendance_action_code


class WorkforceIsolationTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user("workforce-owner", email="workforce-owner@example.com", password="safe-test-password")
        self.staff_user = user_model.objects.create_user("workforce-staff", email="workforce-staff@example.com", password="safe-test-password")
        self.outsider = user_model.objects.create_user("workforce-outsider", email="workforce-outsider@example.com", password="safe-test-password")
        self.business = Business.objects.create(display_name="Workforce Studio", created_by=self.owner)
        BusinessMembership.objects.create(business=self.business, user=self.owner, role="owner")
        membership = BusinessMembership.objects.create(
            business=self.business,
            user=self.staff_user,
            role="staff",
        )
        self.profile = StaffProfile.objects.create(
            business=self.business,
            membership=membership,
            display_name="Casey",
            employment_status="active",
        )

    def authenticate(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")

    def test_outsider_cannot_list_and_staff_cannot_create_workforce_records(self):
        path = f"/api/businesses/{self.business.public_id}/workforce/leave-requests/"
        self.authenticate(self.outsider)
        self.assertEqual(self.client.get(path).status_code, 404)
        self.authenticate(self.staff_user)
        response = self.client.post(path, {"staff_public_id": str(self.profile.public_id), "leave_type": "personal", "start_date": "2030-01-01", "end_date": "2030-01-01", "reason": "Personal"}, format="json")
        self.assertEqual(response.status_code, 404)

    def test_revoked_attendance_terminal_token_is_rejected(self):
        device = BusinessDevice.objects.create(business=self.business, name="Front terminal", device_type="attendance", created_by=self.owner)
        _, token = pair_device(issue_device_pairing_code(device))
        code, _ = issue_attendance_action_code(self.profile, "clock_in")
        device.token_version += 1
        device.save(update_fields=["token_version", "updated_at"])
        response = self.client.post(
            "/api/devices/attendance/",
            {"code": code},
            format="json",
            HTTP_X_DEVICE_TOKEN=token,
        )
        self.assertEqual(response.status_code, 403)

    def test_employee_action_codes_are_single_use_and_determine_the_action(self):
        device = BusinessDevice.objects.create(
            business=self.business,
            name="Front terminal",
            device_type="attendance",
            created_by=self.owner,
        )
        _, token = pair_device(issue_device_pairing_code(device))

        clock_in_code, _ = issue_attendance_action_code(self.profile, "clock_in")
        clock_in = self.client.post(
            "/api/devices/attendance/",
            {"code": clock_in_code},
            format="json",
            HTTP_X_DEVICE_TOKEN=token,
        )
        self.assertEqual(clock_in.status_code, 201)
        self.assertEqual(clock_in.data["action"], "clock_in")
        self.assertEqual(clock_in.data["employee_name"], "Casey")

        reused = self.client.post(
            "/api/devices/attendance/",
            {"code": clock_in_code},
            format="json",
            HTTP_X_DEVICE_TOKEN=token,
        )
        self.assertEqual(reused.status_code, 409)

        clock_out_code, _ = issue_attendance_action_code(self.profile, "clock_out")
        clock_out = self.client.post(
            "/api/devices/attendance/",
            {"code": clock_out_code},
            format="json",
            HTTP_X_DEVICE_TOKEN=token,
        )
        self.assertEqual(clock_out.status_code, 201)
        self.assertEqual(clock_out.data["action"], "clock_out")
