"""
認証サービス - JWT認証とFirestore連携
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
import bcrypt
import os
import logging
from google.cloud import firestore

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        """認証サービスの初期化"""
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 480  # 8時間
        
        # Firestoreクライアントの初期化
        self.db = None
        self.users_collection = None
        try:
            # Firestoreの認証情報が設定されているかチェック
            if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("FIRESTORE_PROJECT_ID"):
                self.db = firestore.Client()
                self.users_collection = self.db.collection("users")
                logger.info("Firestore接続成功")
            else:
                logger.info("Firestore認証情報が設定されていません。デモモードで動作します")
        except Exception as e:
            logger.warning(f"Firestore接続エラー: {str(e)}. デモモードで動作します")
            self.db = None

        # デモ用のユーザーデータ（Firestoreが利用できない場合に使用）
        self._demo_users = self._create_demo_users()
    
    def _create_demo_users(self) -> Dict:
        """デモ用のユーザーを作成（開発・テスト用）"""
        demo_password = "demo123"
        hashed = bcrypt.hashpw(demo_password.encode('utf-8'), bcrypt.gensalt())
        
        return {
            "demo": {
                "username": "demo",
                "password_hash": hashed.decode('utf-8'),
                "name": "デモユーザー",
                "created_at": datetime.now().isoformat()
            },
            "admin": {
                "username": "admin",
                "password_hash": hashed.decode('utf-8'),
                "name": "管理者",
                "created_at": datetime.now().isoformat()
            }
        }
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        ユーザー認証
        
        Args:
            username: ユーザー名
            password: パスワード
            
        Returns:
            認証成功時はユーザー情報、失敗時はNone
        """
        try:
            # Firestoreからユーザー情報を取得
            if self.db:
                user_ref = self.users_collection.document(username)
                user_doc = user_ref.get()
                
                if not user_doc.exists:
                    logger.warning(f"ユーザーが見つかりません: {username}")
                    return None
                
                user_data = user_doc.to_dict()
            else:
                # デモモード
                user_data = self._demo_users.get(username)
                if not user_data:
                    logger.warning(f"デモユーザーが見つかりません: {username}")
                    return None
            
            # パスワードの検証
            stored_password_hash = user_data.get("password_hash")
            if not stored_password_hash:
                logger.error(f"パスワードハッシュが存在しません: {username}")
                return None
            
            # bcryptでパスワード検証
            is_valid = bcrypt.checkpw(
                password.encode('utf-8'),
                stored_password_hash.encode('utf-8')
            )
            
            if not is_valid:
                logger.warning(f"パスワードが一致しません: {username}")
                return None
            
            logger.info(f"ユーザー認証成功: {username}")
            return {
                "username": username,
                "name": user_data.get("name", username)
            }
        
        except Exception as e:
            logger.error(f"認証処理エラー: {str(e)}")
            return None
    
    def create_access_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        JWTアクセストークンを生成
        
        Args:
            data: トークンに含めるデータ
            expires_delta: 有効期限（デフォルト: 8時間）
            
        Returns:
            JWTトークン
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        logger.info(f"アクセストークン生成: {data.get('sub')}, 有効期限: {expire}")
        return encoded_jwt
    
    async def create_user(self, username: str, password: str, name: str) -> bool:
        """
        新規ユーザーを作成
        
        Args:
            username: ユーザー名
            password: パスワード
            name: 表示名
            
        Returns:
            成功時True、失敗時False
        """
        try:
            # パスワードのハッシュ化
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            user_data = {
                "username": username,
                "password_hash": password_hash.decode('utf-8'),
                "name": name,
                "created_at": datetime.now().isoformat()
            }
            
            if self.db:
                # Firestoreに保存
                self.users_collection.document(username).set(user_data)
                logger.info(f"新規ユーザー作成成功: {username}")
            else:
                # デモモードでは作成をシミュレート
                self._demo_users[username] = user_data
                logger.info(f"デモモードで新規ユーザー作成: {username}")
            
            return True
        
        except Exception as e:
            logger.error(f"ユーザー作成エラー: {str(e)}")
            return False
    
    async def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        パスワード変更
        
        Args:
            username: ユーザー名
            old_password: 現在のパスワード
            new_password: 新しいパスワード
            
        Returns:
            成功時True、失敗時False
        """
        try:
            # 現在のパスワードで認証
            user = await self.authenticate_user(username, old_password)
            if not user:
                logger.warning(f"パスワード変更失敗: 認証エラー - {username}")
                return False
            
            # 新しいパスワードのハッシュ化
            new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            
            if self.db:
                # Firestoreを更新
                self.users_collection.document(username).update({
                    "password_hash": new_password_hash.decode('utf-8'),
                    "password_updated_at": datetime.now().isoformat()
                })
            else:
                # デモモード
                if username in self._demo_users:
                    self._demo_users[username]["password_hash"] = new_password_hash.decode('utf-8')
            
            logger.info(f"パスワード変更成功: {username}")
            return True
        
        except Exception as e:
            logger.error(f"パスワード変更エラー: {str(e)}")
            return False
