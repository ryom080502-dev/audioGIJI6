"""
Google Cloud Storage サービス
署名付きURLを生成してクライアントから直接アップロードできるようにする
"""
import os
from datetime import datetime, timedelta
from google.cloud import storage
from google.auth import compute_engine
from google.auth.transport import requests as google_requests
import logging

logger = logging.getLogger(__name__)

class GCSService:
    def __init__(self):
        """GCSサービスの初期化"""
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.bucket_name = f"{self.project_id}-audio-uploads"

        try:
            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)
            logger.info(f"GCS初期化成功: バケット {self.bucket_name}")
        except Exception as e:
            logger.error(f"GCS初期化エラー: {str(e)}")
            raise

    def generate_upload_signed_url(self, filename: str, content_type: str = "audio/*") -> str:
        """
        アップロード用の署名付きURLを生成（Cloud Run環境対応）

        IAM signBlob APIを使用して署名付きURLを生成

        Args:
            filename: アップロードするファイル名
            content_type: ファイルのMIMEタイプ

        Returns:
            署名付きURL
        """
        try:
            from google.auth import default
            from google.auth.transport.requests import AuthorizedSession
            import google.auth

            blob = self.bucket.blob(filename)

            # デフォルトの認証情報を取得
            credentials, project = default()

            # メタデータサーバーからサービスアカウントのメールアドレスを取得
            try:
                # Cloud Run環境
                import requests as http_requests
                metadata_server = "http://metadata.google.internal/computeMetadata/v1/"
                metadata_flavor = {'Metadata-Flavor': 'Google'}
                service_account_email = http_requests.get(
                    metadata_server + 'instance/service-accounts/default/email',
                    headers=metadata_flavor
                ).text
                logger.info(f"サービスアカウント: {service_account_email}")
            except Exception:
                # フォールバック
                service_account_email = "643484544688-compute@developer.gserviceaccount.com"
                logger.warning(f"メタデータサーバーからの取得失敗、デフォルトを使用: {service_account_email}")

            # 署名付きURLを生成（IAM signBlobを使用）
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=15),
                method="PUT",
                content_type=content_type,
                service_account_email=service_account_email,
            )

            logger.info(f"署名付きURL生成成功: {filename}")
            return url

        except Exception as e:
            logger.error(f"署名付きURL生成エラー: {str(e)}")
            raise

    def generate_download_signed_url(self, filename: str) -> str:
        """
        ダウンロード用の署名付きURLを生成

        Args:
            filename: ダウンロードするファイル名

        Returns:
            署名付きURL
        """
        try:
            blob = self.bucket.blob(filename)

            # 署名付きURLを生成（1時間有効）
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=1),
                method="GET",
            )

            logger.info(f"ダウンロード用署名付きURL生成成功: {filename}")
            return url

        except Exception as e:
            logger.error(f"ダウンロード用署名付きURL生成エラー: {str(e)}")
            raise

    def delete_file(self, filename: str) -> bool:
        """
        ファイルを削除

        Args:
            filename: 削除するファイル名

        Returns:
            削除成功ならTrue
        """
        try:
            blob = self.bucket.blob(filename)
            blob.delete()
            logger.info(f"ファイル削除成功: {filename}")
            return True

        except Exception as e:
            logger.error(f"ファイル削除エラー: {str(e)}")
            return False

    def download_to_temp(self, filename: str, temp_path: str) -> bool:
        """
        ファイルを一時ディレクトリにダウンロード

        Args:
            filename: ダウンロードするファイル名
            temp_path: 保存先のパス

        Returns:
            ダウンロード成功ならTrue
        """
        try:
            blob = self.bucket.blob(filename)
            blob.download_to_filename(temp_path)
            logger.info(f"ファイルダウンロード成功: {filename} -> {temp_path}")
            return True

        except Exception as e:
            logger.error(f"ファイルダウンロードエラー: {str(e)}")
            return False
