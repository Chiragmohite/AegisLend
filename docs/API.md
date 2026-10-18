# API reference — current implemented routes

Generated from FastAPI OpenAPI after the approved polish changes. Request/response schemas and validation details are available at `/docs` when the backend runs. Protected routes require a signed bearer token and a valid server-side session; administrator routes additionally load the administrator role from the database.

| Method | Path | Operation |
|---|---|---|
| GET | `/api/v1/activity` | Activity |
| GET | `/api/v1/admin/access` | Admin Access |
| GET | `/api/v1/admin/applications` | Review Applications |
| GET | `/api/v1/admin/appointments` | All Appointments |
| POST | `/api/v1/admin/appointments/{appointment_id}/attendance` | Attendance |
| GET | `/api/v1/admin/audit` | Audit List |
| GET | `/api/v1/admin/documents` | Documents |
| POST | `/api/v1/admin/documents` | Upload |
| DELETE | `/api/v1/admin/documents/{document_id}` | Remove Document |
| POST | `/api/v1/admin/documents/{document_id}/reindex` | Reindex |
| GET | `/api/v1/admin/products` | Admin Products |
| POST | `/api/v1/admin/products` | Create Product |
| PUT | `/api/v1/admin/products/{product_id}` | Edit Product |
| GET | `/api/v1/admin/security/events` | Events |
| POST | `/api/v1/admin/security/events/{event_id}/review` | Review Event |
| GET | `/api/v1/admin/security/incidents` | Incidents |
| GET | `/api/v1/admin/security/incidents/{incident_id}` | Detail |
| POST | `/api/v1/admin/security/incidents/{incident_id}/actions` | Act |
| POST | `/api/v1/admin/security/probe` | Probe |
| GET | `/api/v1/admin/security/risks` | Risks |
| GET | `/api/v1/admin/security/summary` | Security Summary |
| POST | `/api/v1/admin/security/train` | Train Model |
| GET | `/api/v1/admin/users` | Users |
| POST | `/api/v1/applications` | Create Application |
| GET | `/api/v1/applications` | Applications |
| PUT | `/api/v1/applications/{application_id}` | Edit Draft |
| GET | `/api/v1/applications/{application_id}` | Get Application |
| POST | `/api/v1/applications/{application_id}/transition` | Transition |
| POST | `/api/v1/appointments` | Book |
| GET | `/api/v1/appointments` | Appointments |
| GET | `/api/v1/appointments/slots` | Slots |
| GET | `/api/v1/appointments/waitlist` | Waitlist |
| POST | `/api/v1/appointments/waitlist` | Join Waitlist |
| DELETE | `/api/v1/appointments/waitlist/{entry_id}` | Leave Waitlist |
| GET | `/api/v1/appointments/{appointment_id}/attendance` | View Attendance |
| POST | `/api/v1/appointments/{appointment_id}/cancel` | Cancel |
| POST | `/api/v1/appointments/{appointment_id}/reschedule` | Reschedule |
| POST | `/api/v1/assistant` | Assistant |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/logout` | Logout Session |
| GET | `/api/v1/auth/me` | Me |
| GET | `/api/v1/auth/otp` | Otp Status |
| POST | `/api/v1/auth/otp/activate` | Otp Activate |
| POST | `/api/v1/auth/otp/enroll` | Otp Enroll |
| POST | `/api/v1/auth/register` | Register |
| GET | `/api/v1/auth/session` | Session Status |
| POST | `/api/v1/auth/session/confirm` | Confirm Session |
| GET | `/api/v1/dashboard` | Dashboard |
| POST | `/api/v1/eligibility` | Eligibility |
| GET | `/api/v1/eligibility/{assessment_id}` | Get Eligibility |
| GET | `/api/v1/health/application` | Application Ready |
| GET | `/api/v1/health/live` | Live |
| GET | `/api/v1/health/ready` | Ready |
| GET | `/api/v1/products` | Products |
| GET | `/api/v1/profile` | Profile |
| PUT | `/api/v1/profile` | Save Profile |

56 implemented API operations.
