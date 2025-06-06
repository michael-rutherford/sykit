# dicom_tools/posda/api.py

import os
import requests as req


class PosdaAPI:
    def __init__(self, api_url, auth_token):
        self.api_url = api_url.rstrip('/')
        self.headers = { 'Authorization': f'Bearer {auth_token}' }

    def query_posda_api(self, endpoint):
        url = f"{self.api_url}{endpoint}"
        try:
            resp = req.get(url, headers=self.headers)
            if resp.status_code == 200:
                return resp, url, True
            print(f'Bad response: {resp.status_code} - {resp.text}')
        except Exception as e:
            print(f'Error processing request: {e}')
        return None, url, False

    def get_study(self, study_instance_uid):
        resp, _, success = self.query_posda_api(f'/studies/{study_instance_uid}')
        return resp.json() if success else None

    # # investigate - Doesn't work
    # def get_study_series(self, study_instance_uid):
    #     resp, _, success = self.query_posda_api(f'/studies/{study_instance_uid}/series')
    #     return resp.json() if success else None

    def get_series(self, series_instance_uid):
        resp, _, success = self.query_posda_api(f'/series/{series_instance_uid}')
        return resp.json() if success else None

    def get_series_files(self, series_instance_uid):
        resp, _, success = self.query_posda_api(f'/series/{series_instance_uid}/files')
        return resp.json().get('file_ids', []) if success else []

    def get_file_info(self, file_id):
        resp, _, success = self.query_posda_api(f'/files/{file_id}')
        return resp.json() if success else None

    def get_file_pixels(self, file_id):
        resp, _, success = self.query_posda_api(f'/files/{file_id}/pixels')
        return resp.content if success else None

    def get_file_data(self, file_id):
        resp, _, success = self.query_posda_api(f'/files/{file_id}/data')
        return resp.content if success else None

    def get_file_path(self, file_id):
        resp, _, success = self.query_posda_api(f'/files/{file_id}/path')
        return resp.json() if success else None

    def get_file_details(self, file_id):
        resp, _, success = self.query_posda_api(f'/files/{file_id}/details')
        return resp.json() if success else None

    def get_dicom_dump(self, file_id):
        resp, _, success = self.query_posda_api(f'/dump/{file_id}')
        return resp.text if success else None

    def download_series(self, series_instance_uid, timepoint=None, output_path=None):
        sid = f"{series_instance_uid}:{timepoint}" if timepoint else series_instance_uid
        file_ids = self.get_series_files(sid)
        if not file_ids:
            print("No files found.")
            return

        series_path = os.path.join(output_path, series_instance_uid)
        os.makedirs(series_path, exist_ok=True)

        print(f"Downloading {len(file_ids)} files...")
        for file_id in file_ids:
            file_content = self.get_file_data(file_id)
            if file_content:
                file_path = os.path.join(series_path, f"{file_id}.dcm")
                with open(file_path, 'wb') as f:
                    f.write(file_content)

    def download_file(self, file_id, output_path):
        file_info = self.get_file_info(file_id)
        
        ext = None
        if file_info:
            match file_info['file_type']:
                case type if type.startswith('parsed dicom file'):
                    ext = 'dcm'
                case type if type.startswith('Nifti Image (gzipped)'):
                    ext = 'nii.gz'
                case type if type.startswith('Nifti Image'):
                    ext = 'nii'                    
                case type if type.startswith('TIFF image data'):
                    ext = 'tif'
                case type if type.contains('ASCII'):
                    ext = 'txt'
                case type if type.startswith('PDF document'):
                    ext = 'pdf'
                case type if type.startswith('text/csv'):
                    ext = 'csv'
                case type if type.startswith('HTML document'):
                    ext = 'html'
                case type if type.startswith('XML  document'):
                    ext = 'xml'
                case type if type.startswith('JSON data'):
                    ext = 'json'
                case type if type.startswith('GIF image data'):
                    ext = 'gif'
                case type if type.startswith('JPEG image data'):
                    ext = 'jpg'
                case type if type.startswith('PNG image data'):
                    ext = 'png'                    
                case type if type.startswith('gzip compressed data'):
                    ext = 'gz'
                case type if type.startswith('Zip archive data'):
                    ext = 'zip'                    
                case type if type.startswith('Perl script'):
                    ext = 'pl'
                case type if type.startswith('Python script'):
                    ext = 'py'
                case type if type.startswith('SQLite'):
                    ext = 'db'
                case _:
                    ext = None
                    
            if ext and not ext.startswith('.'):
                ext = f".{ext}"

        file_content = self.get_file_data(file_id)
        if file_content:
            os.makedirs(output_path, exist_ok=True)
            file_path = os.path.join(output_path, f"{file_id}{ext if ext else ''}")
            with open(file_path, 'wb') as f:
                f.write(file_content)
            return file_path
        return None