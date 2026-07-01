import logging
import os

import msal
import requests

logger = logging.getLogger(__name__)


class PowerBIService:
    def __init__(self):
        self.client_id = os.environ.get('POWERBI_CLIENT_ID')
        self.tenant_id = os.environ.get('POWERBI_TENANT_ID')
        self.client_secret = os.environ.get('POWERBI_CLIENT_SECRET')
        self.workspace_id = os.environ.get('POWERBI_WORKSPACE_ID')
        self.report_id = os.environ.get('POWERBI_REPORT_ID')
        self.enable_rls = os.environ.get('POWERBI_ENABLE_RLS', 'false').lower() in (
            '1', 'true', 'yes',
        )

        self.authority_url = (
            f'https://login.microsoftonline.com/{self.tenant_id}'
            if self.tenant_id
            else None
        )
        self.scope = ['https://analysis.windows.net/powerbi/api/.default']

    def is_configured(self) -> bool:
        return all([
            self.client_id,
            self.tenant_id,
            self.client_secret,
            self.workspace_id,
            self.report_id,
        ])

    def _get_access_token(self):
        """Authenticate with Azure AD for the Power BI REST API."""
        if not self.is_configured():
            return None

        try:
            client = msal.ConfidentialClientApplication(
                self.client_id,
                authority=self.authority_url,
                client_credential=self.client_secret,
            )
            result = client.acquire_token_for_client(scopes=self.scope)

            if 'access_token' in result:
                return result['access_token']

            logger.error(
                'Failed to get MSAL token: %s - %s',
                result.get('error'),
                result.get('error_description'),
            )
            return None
        except Exception as exc:
            logger.error('Error authenticating with MSAL: %s', exc)
            return None

    def get_embed_config(self, user):
        """
        Return embed token + URL when Power BI Embedded (or Pro capacity with
        embed-for-your-customers) is configured; otherwise a graceful fallback payload.
        """
        if not self.is_configured():
            return {
                'success': False,
                'configured': False,
                'message': (
                    'Power BI embedding is not configured. Add POWERBI_CLIENT_ID, '
                    'POWERBI_TENANT_ID, POWERBI_CLIENT_SECRET, POWERBI_WORKSPACE_ID, '
                    'and POWERBI_REPORT_ID to enable in-app reports.'
                ),
            }

        access_token = self._get_access_token()
        if not access_token:
            return {
                'success': False,
                'configured': True,
                'message': (
                    'Could not authenticate with Azure AD. Verify the service principal '
                    'is registered in Power BI Admin portal and has workspace access.'
                ),
            }

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }

        report_url = (
            f'https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}'
            f'/reports/{self.report_id}'
        )

        try:
            report_res = requests.get(report_url, headers=headers, timeout=30)
            report_res.raise_for_status()
            report_data = report_res.json()
            embed_url = report_data.get('embedUrl')
            dataset_id = report_data.get('datasetId')
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 'unknown'
            logger.error('Error fetching report embedUrl (HTTP %s): %s', status, exc)
            return {
                'success': False,
                'configured': True,
                'message': (
                    'Could not load the Power BI report. Confirm WORKSPACE_ID and '
                    'REPORT_ID, and that the workspace is on a Power BI Embedded '
                    '(or Premium/Pro) capacity that allows GenerateToken.'
                ),
            }
        except Exception as exc:
            logger.error('Error fetching report embedUrl: %s', exc)
            return {
                'success': False,
                'configured': True,
                'message': 'Failed to fetch report details from Power BI.',
            }

        token_url = (
            f'https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}'
            f'/reports/{self.report_id}/GenerateToken'
        )

        body: dict = {'accessLevel': 'View'}
        use_rls = bool(dataset_id) and (self.enable_rls or user.role == 'student')
        if use_rls:
            identity = self._embed_rls_identity(user)
            if identity is None:
                return {
                    'success': False,
                    'configured': True,
                    'message': (
                        'Student Power BI access requires a PRN on the user account and '
                        'POWERBI_ENABLE_RLS=true with a Student RLS role in the dataset.'
                    ),
                }
            body['identities'] = [{
                **identity,
                'datasets': [dataset_id],
            }]

        try:
            token_res = requests.post(token_url, headers=headers, json=body, timeout=30)
            token_res.raise_for_status()
            token_data = token_res.json()
        except requests.HTTPError as exc:
            detail = ''
            try:
                detail = exc.response.json().get('error', {}).get('message', '')
            except Exception:
                detail = str(exc)
            logger.error('Error generating embed token: %s', detail or exc)
            return {
                'success': False,
                'configured': True,
                'message': (
                    'Failed to generate an embed token. This usually means the workspace '
                    'is not on Embedded/Premium capacity, or the service principal lacks '
                    f'GenerateToken permission. {detail}'.strip()
                ),
            }
        except Exception as exc:
            logger.error('Error generating embed token: %s', exc)
            return {
                'success': False,
                'configured': True,
                'message': 'Failed to generate embed token.',
            }

        page_name = 'Page 2' if user.role == 'student' else None

        return {
            'success': True,
            'configured': True,
            'embed_token': token_data.get('token'),
            'embed_url': embed_url,
            'report_id': self.report_id,
            'expiration': token_data.get('expiration'),
            'page_name': page_name,
            'hide_page_navigation': user.role == 'student',
            'student_scoped': user.role == 'student',
        }

    @staticmethod
    def _embed_rls_identity(user) -> dict | None:
        """
        Map Django users to Power BI RLS identities.
        Students: username = PRN, role Student (dataset rule: Consolidated Scores.prn = USERNAME()).
        Staff: username = Django username, role Admin / Hod / Faculty.
        """
        if user.role == 'student':
            if not user.prn:
                return None
            return {'username': user.prn, 'roles': ['Student']}

        role_map = {
            'admin': 'Admin',
            'hod': 'Hod',
            'faculty': 'Faculty',
        }
        role_name = role_map.get(user.role)
        if not role_name:
            return None
        return {'username': user.username, 'roles': [role_name]}


powerbi_service = PowerBIService()
