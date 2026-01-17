"""
Google Gemini APIを使用した音声解析サービス
"""
import google.generativeai as genai
import os
import logging
from typing import Dict, List, Any
import time

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        """Gemini APIサービスの初期化"""
        # APIキーの設定（GEMINI_API_KEY と GOOGLE_API_KEY の両方をサポート）
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("APIキーが設定されていません。.envファイルにGEMINI_API_KEYを設定してください")
            raise ValueError(
                "APIキーが見つかりません。.envファイルに以下を設定してください:\n"
                "GEMINI_API_KEY=your-api-key-here"
            )

        # Gemini APIの設定
        try:
            genai.configure(api_key=api_key)
            logger.info("Gemini API設定完了")
        except Exception as e:
            logger.error(f"Gemini API設定エラー: {str(e)}")
            raise

        # モデルの設定
        # Gemini 2.5/2.0は音声ファイルを直接処理できる
        # v1beta APIで利用可能なモデルを優先順位順に試す
        model_names = [
            "models/gemini-2.5-flash",      # Gemini 2.5 Flash (推奨)
            "models/gemini-2.0-flash",      # Gemini 2.0 Flash
            "models/gemini-flash-latest",   # 最新のFlashモデル
            "models/gemini-2.5-pro",        # Gemini 2.5 Pro (高性能)
            "models/gemini-pro-latest",     # 最新のProモデル
            "gemini-pro",                   # フォールバック
        ]

        self.model_name = None
        model_initialized = False
        last_error = None

        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(model_name)
                self.model_name = model_name
                logger.info(f"使用モデル: {model_name}")
                model_initialized = True
                break
            except Exception as e:
                logger.warning(f"{model_name} 利用不可: {str(e)}")
                last_error = e
                continue

        if not model_initialized:
            logger.error(f"すべてのモデルが利用できません。最後のエラー: {str(last_error)}")
            raise ValueError(
                "Geminiモデルを初期化できませんでした。\n"
                "APIキーが正しいか、利用可能なモデルがあるか確認してください。"
            )
        
        # プロンプトテンプレート
        # 分割されたセグメントごとのプロンプト（簡易版）
        self.segment_prompt = """あなたは優秀な書記です。以下の音声内容を解析し、内容を詳細に記録してください。

【重要な指示】
1. 音声の内容を全て聞き取り、漏れなく記録してください
2. 箇条書きには「・」（中黒）のみを使用してください
3. 「*」（アスタリスク）や「#」（ハッシュ）は使用しないでください
4. この音声セグメントで話された内容を時系列で詳細に記録してください
5. 話者が誰か分かる場合は記載してください
6. 決定事項やアクション項目があれば特に明記してください

【出力形式】
話された内容を時系列で詳細に記録してください。箇条書き（・）を使用して整理してください。

音声内容を解析してください。"""

        self.merge_prompt = """以下は同じ会議を時間ごとに分割して解析した複数の記録です。
これらを統合して、読みやすく整理された1つの議事録にまとめてください。

【統合の指示】
1. 全ての分割記録の内容を漏れなく含めてください
2. 重複する内容があれば削除し、一度だけ記載してください
3. 時系列順に整理し、会議全体の流れが分かるようにしてください
4. 箇条書きには「・」（中黒）のみを使用してください
5. 「*」（アスタリスク）や「#」（ハッシュ）は絶対に使用しないでください
6. 5つのセクションに「 1.」～「 5.」の形式で必ず整理してください
7. 各セクションは明確に分けて、読みやすく構成してください
8. 決定事項とネクストアクションは特に丁寧にまとめてください

【必須出力形式】
## 1. 会議の概要
（会議全体の目的、参加者、主なテーマを2-3行で簡潔に記載）

## 2. 議論内容
（議論された内容を時系列で、「・」を使って箇条書きで整理）

・（最初の議題）
   内容の詳細説明

・（次の議題）
   内容の詳細説明

・（さらに次の議題）
   内容の詳細説明

## 3. 決定事項
（会議で決まったことを「・」で箇条書きにして明確に記載）

・（決定事項1）
・（決定事項2）
・（決定事項3）

## 4. ネクストアクション
（次に実施すべき行動を、担当者と期限を含めて「・」で箇条書きに記載）

・（アクション1）- 担当: XX、期限: XX
・（アクション2）- 担当: XX、期限: XX
・（アクション3）- 担当: XX、期限: XX

## 5. 補足・確認事項
（追加の補足情報や、後で確認が必要な事項があれば「・」で箇条書きに記載、なければ「なし」）

・（補足事項1）
・（確認事項1）

---
【分割された記録】
{summaries}

上記の分割記録を統合して、上記の5つのセクション形式で出力してください。"""
    
    async def analyze_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """
        音声ファイルをGemini APIで解析

        Args:
            audio_file_path: 解析する音声ファイルのパス

        Returns:
            解析結果（要約と確認事項）
        """
        try:
            logger.info(f"Gemini APIで音声を解析: {audio_file_path}")
            logger.info(f"使用モデル: {self.model_name}")

            # 音声ファイルをアップロード
            try:
                audio_file = genai.upload_file(path=audio_file_path)
                logger.info(f"ファイルアップロード完了: {audio_file.name}")
            except Exception as e:
                logger.error(f"ファイルアップロードエラー: {str(e)}")
                raise ValueError(
                    f"音声ファイルのアップロードに失敗しました。\n"
                    f"ファイル形式を確認してください。\n"
                    f"エラー詳細: {str(e)}"
                )

            # アップロード処理の完了を待機
            max_wait_time = 60  # 最大60秒待機
            wait_count = 0
            while audio_file.state.name == "PROCESSING":
                if wait_count >= max_wait_time / 2:
                    raise TimeoutError("ファイル処理がタイムアウトしました")
                logger.info("ファイル処理中...")
                time.sleep(2)
                audio_file = genai.get_file(audio_file.name)
                wait_count += 1

            if audio_file.state.name == "FAILED":
                raise ValueError(f"ファイル処理に失敗しました: {audio_file.state.name}")

            logger.info(f"ファイル処理完了: {audio_file.state.name}")

            # Geminiで解析（セグメント用のプロンプトを使用）
            logger.info("Gemini APIに解析リクエストを送信")
            try:
                response = self.model.generate_content(
                    [self.segment_prompt, audio_file],
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,  # 創造性を抑えて正確性を重視
                        max_output_tokens=4096,
                    )
                )
            except Exception as e:
                error_msg = str(e)
                logger.error(f"generate_contentエラー: {error_msg}")

                # より詳細なエラーメッセージを提供
                if "404" in error_msg or "not found" in error_msg.lower():
                    raise ValueError(
                        f"使用中のモデル '{self.model_name}' は音声ファイルの処理に対応していません。\n"
                        f"APIキーの権限を確認するか、Google AI Studioで利用可能なモデルを確認してください。\n"
                        f"エラー詳細: {error_msg}"
                    )
                elif "not supported" in error_msg.lower():
                    raise ValueError(
                        f"このAPIキーでは音声ファイルの処理がサポートされていません。\n"
                        f"有料プランへのアップグレードが必要な可能性があります。"
                    )
                else:
                    raise
            
            # レスポンスのパース
            result_text = response.text
            logger.info("解析完了")
            
            # 確認事項の抽出
            confirmation_items = self._extract_confirmation_items(result_text)
            
            # 確認事項部分を要約から除去
            summary = self._remove_confirmation_section(result_text)
            
            # アップロードしたファイルを削除
            try:
                genai.delete_file(audio_file.name)
                logger.info("アップロードファイルを削除")
            except Exception as e:
                logger.warning(f"ファイル削除エラー: {str(e)}")
            
            return {
                "summary": summary.strip(),
                "confirmation_items": confirmation_items
            }
        
        except Exception as e:
            logger.error(f"Gemini API解析エラー: {str(e)}")
            raise
    
    async def merge_summaries(self, summaries: List[str]) -> str:
        """
        複数の議事録要約を統合
        
        Args:
            summaries: 統合する要約のリスト
            
        Returns:
            統合された要約
        """
        try:
            logger.info(f"{len(summaries)} 個の要約を統合")
            
            # 要約を番号付きで結合
            numbered_summaries = "\n\n".join(
                [f"--- セグメント {i+1} ---\n{summary}" 
                 for i, summary in enumerate(summaries)]
            )
            
            prompt = self.merge_prompt.format(summaries=numbered_summaries)
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=8192,
                )
            )
            
            merged_summary = response.text
            logger.info("要約の統合完了")
            
            return merged_summary.strip()
        
        except Exception as e:
            logger.error(f"要約統合エラー: {str(e)}")
            # エラーの場合は単純に結合
            return "\n\n".join(summaries)
    
    def _extract_confirmation_items(self, text: str) -> List[str]:
        """
        テキストから確認事項を抽出
        
        Args:
            text: 解析結果テキスト
            
        Returns:
            確認事項のリスト
        """
        items = []
        
        # 【💡確認事項】セクションを探す
        if "【💡確認事項】" in text or "💡確認事項" in text:
            # セクションを分割
            parts = text.split("【💡確認事項】")
            if len(parts) < 2:
                parts = text.split("💡確認事項")
            
            if len(parts) >= 2:
                confirmation_section = parts[1]
                
                # 次のセクション（##で始まる）までを取得
                next_section_idx = confirmation_section.find("\n##")
                if next_section_idx != -1:
                    confirmation_section = confirmation_section[:next_section_idx]
                
                # 箇条書きを抽出（•、-、*、数字.で始まる行）
                for line in confirmation_section.split("\n"):
                    line = line.strip()
                    if not line or line.lower() == "なし":
                        continue
                    
                    # 箇条書き記号を除去
                    for prefix in ["• ", "- ", "* ", "・"]:
                        if line.startswith(prefix):
                            line = line[len(prefix):].strip()
                            break
                    
                    # 数字付き箇条書き（1. 2. など）を除去
                    if line and line[0].isdigit() and ". " in line[:4]:
                        line = line.split(". ", 1)[1].strip()
                    
                    if line:
                        items.append(line)
        
        logger.info(f"確認事項を {len(items)} 件抽出")
        return items
    
    def _remove_confirmation_section(self, text: str) -> str:
        """
        テキストから確認事項セクションを除去
        
        Args:
            text: 元のテキスト
            
        Returns:
            確認事項を除去したテキスト
        """
        if "【💡確認事項】" in text:
            return text.split("【💡確認事項】")[0].strip()
        elif "💡確認事項" in text:
            return text.split("💡確認事項")[0].strip()
        return text
