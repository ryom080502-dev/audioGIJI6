# 音声議事録AI - デプロイメントガイド

## 概要
このガイドでは、音声議事録自動生成システムをGoogle Cloud Runにデプロイする手順を説明します。

## 前提条件

### 1. Google Cloudの準備
- Google Cloudアカウントを持っていること
- Google Cloud プロジェクトを作成済みであること
- 課金が有効になっていること

### 2. 必要なAPI
以下のAPIを有効化してください:
```bash
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 3. Gemini API キー
- Google AI Studioで Gemini API キーを取得
- URL: https://aistudio.google.com/app/apikey

## デプロイ方法

### オプション1: GitHub Actionsを使った自動デプロイ（推奨）

#### ステップ1: GitHubリポジトリの作成

1. GitHubで新しいリポジトリを作成
2. リポジトリ名: `voice-minutes-generator` （任意）
3. プライベートリポジトリを推奨

#### ステップ2: GitHub Secretsの設定

GitHubリポジトリの Settings > Secrets and variables > Actions で以下のシークレットを追加:

1. **GCP_PROJECT_ID**
   - Google CloudのプロジェクトID
   - 例: `my-project-12345`

2. **GCP_SA_KEY**
   - サービスアカウントのJSONキー
   - 取得方法:
     ```bash
     # サービスアカウントを作成
     gcloud iam service-accounts create github-actions \
       --display-name="GitHub Actions"

     # 必要な権限を付与
     gcloud projects add-iam-policy-binding PROJECT_ID \
       --member="serviceAccount:github-actions@PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/run.admin"

     gcloud projects add-iam-policy-binding PROJECT_ID \
       --member="serviceAccount:github-actions@PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/storage.admin"

     gcloud projects add-iam-policy-binding PROJECT_ID \
       --member="serviceAccount:github-actions@PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/iam.serviceAccountUser"

     # JSONキーを作成
     gcloud iam service-accounts keys create key.json \
       --iam-account=github-actions@PROJECT_ID.iam.gserviceaccount.com
     ```
   - key.jsonの内容をコピーしてGitHub Secretsに貼り付け

3. **GEMINI_API_KEY**
   - Google AI StudioのGemini APIキー

#### ステップ3: コードをプッシュ

```bash
cd "C:\Users\r-moc\Desktop\AI作成\音声議事録AI"

# Gitの初期設定（初回のみ）
git config user.name "Your Name"
git config user.email "your.email@example.com"

# ファイルをステージング
git add .

# コミット
git commit -m "Initial commit: Voice minutes generator"

# リモートリポジトリを追加
git remote add origin https://github.com/YOUR_USERNAME/voice-minutes-generator.git

# プッシュ
git branch -M main
git push -u origin main
```

プッシュすると自動的にGitHub Actionsが実行され、Cloud Runにデプロイされます。

#### ステップ4: デプロイ確認

1. GitHubリポジトリの「Actions」タブで進行状況を確認
2. デプロイ完了後、Cloud Runのコンソールでサービスを確認
3. URLが表示されるので、ブラウザでアクセス

### オプション2: 手動デプロイ

#### ステップ1: Google Cloud SDKの設定

```bash
# Google Cloudにログイン
gcloud auth login

# プロジェクトを設定
gcloud config set project PROJECT_ID

# リージョンを設定
gcloud config set run/region asia-northeast1
```

#### ステップ2: Dockerイメージのビルドとプッシュ

```bash
cd "C:\Users\r-moc\Desktop\AI作成\音声議事録AI"

# イメージをビルド
gcloud builds submit --tag gcr.io/PROJECT_ID/minutes-generator

# または、ローカルでビルドしてプッシュ
docker build -t gcr.io/PROJECT_ID/minutes-generator .
docker push gcr.io/PROJECT_ID/minutes-generator
```

#### ステップ3: Cloud Runにデプロイ

```bash
gcloud run deploy minutes-generator \
  --image gcr.io/PROJECT_ID/minutes-generator \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 10 \
  --set-env-vars GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

## 環境変数の設定

### 必須の環境変数

| 変数名 | 説明 | 例 |
|--------|------|-----|
| GEMINI_API_KEY | Google Gemini APIキー | AIza... |

### オプションの環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| PORT | サーバーのポート | 8080 |
| DEMO_MODE | デモモード（true/false） | true |

## デプロイ後の設定

### 1. カスタムドメインの設定（オプション）

```bash
# ドメインをマッピング
gcloud run domain-mappings create \
  --service minutes-generator \
  --domain your-domain.com \
  --region asia-northeast1
```

### 2. 認証の設定（本番環境）

デモモードを無効にして、Firebase Authenticationを設定する場合:

1. Firebase Consoleでプロジェクトを作成
2. Firebase Authenticationを有効化
3. サービスアカウントキーをダウンロード
4. Cloud Runの環境変数に設定:
   ```bash
   gcloud run services update minutes-generator \
     --set-env-vars DEMO_MODE=false \
     --set-env-vars FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}' \
     --region asia-northeast1
   ```

### 3. ログの確認

```bash
# ログを表示
gcloud run logs read --service minutes-generator --region asia-northeast1

# リアルタイムでログを追跡
gcloud run logs tail --service minutes-generator --region asia-northeast1
```

## トラブルシューティング

### デプロイが失敗する場合

1. **ビルドエラー**
   ```bash
   # ビルドログを確認
   gcloud builds list --limit=5
   gcloud builds log [BUILD_ID]
   ```

2. **起動エラー**
   ```bash
   # Cloud Runのログを確認
   gcloud run logs read --service minutes-generator --limit=50
   ```

3. **権限エラー**
   - サービスアカウントに必要な権限があるか確認
   - APIが有効になっているか確認

### よくある問題

#### 問題1: メモリ不足
```bash
# メモリを増やす
gcloud run services update minutes-generator \
  --memory 4Gi \
  --region asia-northeast1
```

#### 問題2: タイムアウト
```bash
# タイムアウトを延長
gcloud run services update minutes-generator \
  --timeout 3600 \
  --region asia-northeast1
```

#### 問題3: 日本語フォントが表示されない
- Dockerfileに `fonts-noto-cjk` が含まれているか確認
- イメージを再ビルドしてデプロイ

## コスト管理

### Cloud Runの料金

- **CPU使用量**: リクエスト処理中のみ課金
- **メモリ使用量**: リクエスト処理中のみ課金
- **リクエスト数**: 月間200万リクエストまで無料

### 推奨設定

```bash
# 最小インスタンス数を0に設定（コスト削減）
gcloud run services update minutes-generator \
  --min-instances 0 \
  --region asia-northeast1

# 最大インスタンス数を制限
gcloud run services update minutes-generator \
  --max-instances 5 \
  --region asia-northeast1
```

## セキュリティ

### 1. 認証の有効化（本番環境推奨）

```bash
# 認証を要求する
gcloud run services update minutes-generator \
  --no-allow-unauthenticated \
  --region asia-northeast1
```

### 2. VPCの設定（オプション）

```bash
# VPCコネクタを作成
gcloud compute networks vpc-access connectors create minutes-connector \
  --network default \
  --region asia-northeast1 \
  --range 10.8.0.0/28

# Cloud RunサービスにVPCを設定
gcloud run services update minutes-generator \
  --vpc-connector minutes-connector \
  --region asia-northeast1
```

## 更新とメンテナンス

### コードを更新する場合

```bash
# GitHub経由（自動デプロイ）
git add .
git commit -m "Update: description"
git push origin main

# 手動デプロイ
gcloud builds submit --tag gcr.io/PROJECT_ID/minutes-generator
gcloud run deploy minutes-generator \
  --image gcr.io/PROJECT_ID/minutes-generator \
  --region asia-northeast1
```

### ロールバック

```bash
# 以前のリビジョンを確認
gcloud run revisions list --service minutes-generator --region asia-northeast1

# 特定のリビジョンにロールバック
gcloud run services update-traffic minutes-generator \
  --to-revisions REVISION_NAME=100 \
  --region asia-northeast1
```

## サポート

問題が発生した場合:
1. Cloud Runのログを確認
2. ビルドログを確認
3. GitHubのIssuesで報告

## 参考リンク

- [Cloud Run ドキュメント](https://cloud.google.com/run/docs)
- [Gemini API ドキュメント](https://ai.google.dev/docs)
- [GitHub Actions ドキュメント](https://docs.github.com/ja/actions)
