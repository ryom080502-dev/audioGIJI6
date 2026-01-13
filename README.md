# 音声議事録AI - 自動議事録生成システム

音声ファイルから自動で議事録を生成するWebアプリケーション

Google Gemini 2.5 Flashを活用し、音声から高精度な議事録を自動生成。100MB以上の大容量ファイルにも対応し、Word/PDF形式で出力可能です。

## 機能概要

- 🎤 **大容量ファイル対応**: 100MB以上のファイルも自動分割・処理
- 🤖 **AI自動解析**: Google Gemini 2.5 Flashで高精度な文字起こしと要約
- 📝 **5セクション構成**: 会議の概要、議論内容、決定事項、ネクストアクション、補足事項
- ✏️ **インタラクティブ編集**: 生成された議事録を簡単に編集
- 💡 **確認事項の抽出**: AIが判断に迷う項目を自動検出
- 📄 **複数形式エクスポート**: Word/PDF形式でのダウンロード
- 🎨 **見やすいデザイン**: 読みやすいフォントサイズと箇条書き形式
- 🔐 **セキュアな認証**: JWT認証による安全なアクセス管理

## 技術スタック

### Backend
- **FastAPI** - 高速でモダンなPython Webフレームワーク
- **Google Gemini API** - 最先端のAI音声解析
- **PyDub** - 音声ファイルの圧縮・分割処理
- **Cloud Firestore** - ユーザー管理

### Frontend
- **HTML5 + Tailwind CSS** - モダンでレスポンシブなUI
- **Vanilla JavaScript** - シンプルで高速な実装

### Infrastructure
- **Google Cloud Run** - サーバーレスコンテナ実行環境
- **Artifact Registry** - Dockerイメージ管理
- **GitHub Actions** - CI/CDパイプライン

## セットアップ

### 前提条件

- Python 3.13以上
- FFmpeg（音声処理に必要）
- Google Cloud Platform アカウント（本番デプロイ時）
- Gemini API キー（必須）

### ローカル開発環境

1. **リポジトリのクローン**
   ```bash
   git clone <repository-url>
   cd 音声議事録AI
   ```

2. **Python仮想環境の作成**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **依存関係のインストール**
   ```bash
   pip install -r requirements.txt
   ```

4. **環境変数の設定**
   ```bash
   # .env.exampleをコピーして.envを作成
   cp .env.example .env

   # .envファイルを編集して以下を設定:
   # - GEMINI_API_KEY: GeminiのAPIキー（必須）
   # - JWT_SECRET_KEY: JWT認証用の秘密鍵（本番環境では必ず変更）
   # - GOOGLE_APPLICATION_CREDENTIALS: Firestore認証情報（オプション）
   ```

5. **アプリケーションの起動**
   ```bash
   python main.py

   # または
   uvicorn main:app --reload --host 0.0.0.0 --port 8080
   ```

6. **ブラウザでアクセス**
   ```
   http://localhost:8080

   # ログインページ: http://localhost:8080/index.html
   # ダッシュボード: http://localhost:8080/dashboard.html
   ```

### デモアカウント

開発環境では以下のデモアカウントが利用可能です:

- **ユーザー名**: demo
- **パスワード**: demo123

## デプロイ

詳細な手順は [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) を参照してください。

### クイックスタート: Google Cloud Runへのデプロイ

1. **GitHub Secretsの設定**

   以下のSecretをGitHubリポジトリに設定:
   - `GCP_PROJECT_ID`: Google CloudプロジェクトID
   - `GCP_SA_KEY`: サービスアカウントキー（JSON）
   - `GEMINI_API_KEY`: Gemini APIキー

2. **mainブランチへのPush**
   ```bash
   git add .
   git commit -m "Initial deployment"
   git push origin main
   ```

   GitHub Actionsが自動的にビルド・デプロイを実行します。

3. **デプロイ確認**

   GitHub ActionsのログでCloud RunのURLを確認し、ブラウザでアクセス。

## アーキテクチャ

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       ↓
┌──────────────────────────────────┐
│      Frontend (HTML/JS/CSS)      │
│  - ログイン画面                    │
│  - ファイルアップロードUI           │
│  - 議事録編集エディタ               │
└──────────────┬───────────────────┘
               │
               ↓ REST API
┌──────────────────────────────────┐
│       Backend (FastAPI)          │
│  ┌────────────────────────────┐  │
│  │   Audio Processor          │  │
│  │   - 圧縮 (64kbps, mono)    │  │
│  │   - 分割 (30分単位)         │  │
│  └────────────────────────────┘  │
│  ┌────────────────────────────┐  │
│  │   Gemini Service           │  │
│  │   - 音声解析               │  │
│  │   - 要約生成               │  │
│  │   - 確認事項抽出            │  │
│  └────────────────────────────┘  │
│  ┌────────────────────────────┐  │
│  │   Document Generator       │  │
│  │   - Word出力               │  │
│  │   - PDF出力                │  │
│  └────────────────────────────┘  │
└──────────────┬───────────────────┘
               │
               ↓
┌──────────────────────────────────┐
│      External Services           │
│  - Gemini API (音声解析)          │
│  - Cloud Firestore (ユーザー管理)  │
└──────────────────────────────────┘
```

## 使用方法

### 1. メタデータ入力
- 作成日、作成者、お客様名、打合せ場所を入力
- タイトルが自動生成される

### 2. 音声アップロード
- ドラッグ&ドロップまたはファイル選択で音声ファイルをアップロード
- 対応形式: MP3, WAV, M4A, MP4など
- 最大500MB

### 3. AI解析
- 自動で音声を文字起こし
- 議事録の要約を生成
- 確認が必要な項目を抽出

### 4. 編集と確認
- 生成された議事録を編集
- 確認事項をチェックボックスで選択

### 5. エクスポート
- Word形式またはPDF形式でダウンロード

## 音声処理の仕組み

### 100MB以上のファイル対応

1. **圧縮処理**
   - モノラル化（ステレオ → モノ）
   - サンプリングレート: 16kHz
   - ビットレート: 64kbps

2. **分割処理**
   - 圧縮後も100MBを超える場合、30分単位で分割
   - 各セグメントを個別に解析
   - 最終的に統合

## セキュリティ

- JWT認証によるアクセス制御
- パスワードはbcryptでハッシュ化
- HTTPS通信（Cloud Run）
- 環境変数による機密情報の管理

## トラブルシューティング

### 音声ファイルのアップロードに失敗する
- ファイル形式が対応しているか確認
- ファイルサイズが500MB以下か確認
- ネットワーク接続を確認

### 議事録の生成に時間がかかる
- 大容量ファイルの場合、処理に数分かかることがあります
- 進捗バーで状態を確認できます

### ログインできない
- ユーザー名・パスワードを確認
- デモアカウント（demo/demo123）を試してください

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## サポート

問題が発生した場合は、GitHubのIssuesで報告してください。
