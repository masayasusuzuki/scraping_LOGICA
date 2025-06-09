import requests
import urllib.parse
import json
from typing import Optional, Dict, Any


class GooglePlacesAPI:
    """
    Google Places APIを使用して施設情報を取得するクラス
    
    Google Places APIの使用には以下が必要です：
    1. Google Cloud Platformでプロジェクトを作成
    2. Places APIを有効化
    3. APIキーを生成し、Places APIへのアクセスを許可
    4. 請求先アカウントの設定（無料枠を超える場合）
    """
    
    def __init__(self, api_key: str):
        """
        初期化
        
        Args:
            api_key (str): Google Places APIキー
        """
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
    
    def _handle_api_error(self, status: str, context: str) -> str:
        """
        APIエラーステータスを分析し、詳細なエラーメッセージを返す
        
        Args:
            status (str): APIレスポンスのステータス
            context (str): エラーが発生したコンテキスト
            
        Returns:
            str: 詳細なエラーメッセージ
        """
        error_messages = {
            'REQUEST_DENIED': (
                'APIキーが無効か、Places APIが有効化されていません。\n'
                '以下を確認してください：\n'
                '1. APIキーが正しいか\n'
                '2. Google Cloud ConsoleでPlaces APIが有効になっているか\n'
                '3. APIキーにPlaces APIの使用権限があるか\n'
                '4. 請求先アカウントが設定されているか（無料枠を超える場合）'
            ),
            'OVER_QUERY_LIMIT': 'APIクエリ制限を超過しました。しばらく待ってから再試行してください。',
            'ZERO_RESULTS': f'{context}で該当する結果が見つかりませんでした。',
            'INVALID_REQUEST': f'{context}のリクエストパラメータが無効です。',
            'NOT_FOUND': f'{context}で指定されたplace_idが見つかりませんでした。',
            'UNKNOWN_ERROR': f'{context}でサーバーエラーが発生しました。再試行してください。'
        }
        
        return error_messages.get(status, f'{context}で不明なエラーが発生しました: {status}')
    
    def search_place(self, facility_name: str) -> Optional[str]:
        """
        施設名でGoogle Places検索を実行し、place_idを取得
        
        Args:
            facility_name (str): 検索する施設名
            
        Returns:
            Optional[str]: place_id（見つからない場合はNone）
        """
        try:
            # Text Search APIのエンドポイント
            search_url = f"{self.base_url}/textsearch/json"
            
            params = {
                'query': facility_name,
                'key': self.api_key,
                'language': 'ja',  # 日本語での結果を優先
                'region': 'jp'     # 日本での検索を優先
            }
            
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 検索結果がある場合、最初の結果のplace_idを返す
            if data.get('status') == 'OK' and data.get('results'):
                return data['results'][0]['place_id']
            
            # エラーステータスの詳細処理
            status = data.get('status')
            error_msg = self._handle_api_error(status, '施設検索')
            print(f"施設検索エラー: {facility_name}")
            print(f"ステータス: {status}")
            print(f"詳細: {error_msg}")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"検索リクエストエラー: {e}")
            return None
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print(f"レスポンス解析エラー: {e}")
            return None
    
    def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        place_idから詳細情報を取得
        
        Args:
            place_id (str): Google Places の place_id
            
        Returns:
            Optional[Dict[str, Any]]: 施設の詳細情報（取得失敗時はNone）
        """
        try:
            # Place Details APIのエンドポイント
            details_url = f"{self.base_url}/details/json"
            
            params = {
                'place_id': place_id,
                'fields': 'name,formatted_phone_number,international_phone_number,formatted_address,rating',
                'key': self.api_key,
                'language': 'ja'
            }
            
            response = requests.get(details_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('result'):
                return data['result']
            
            # エラーステータスの詳細処理
            status = data.get('status')
            error_msg = self._handle_api_error(status, '詳細情報取得')
            print(f"詳細取得エラー place_id: {place_id}")
            print(f"ステータス: {status}")
            print(f"詳細: {error_msg}")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"詳細取得リクエストエラー: {e}")
            return None
        except (KeyError, json.JSONDecodeError) as e:
            print(f"詳細レスポンス解析エラー: {e}")
            return None
    
    def test_api_key(self) -> bool:
        """
        APIキーが有効かどうかをテストする
        
        Returns:
            bool: APIキーが有効な場合True、無効な場合False
        """
        print("APIキーをテスト中...")
        
        # 簡単な検索でAPIキーをテスト
        test_result = self.search_place("東京駅")
        
        if test_result:
            print("✅ APIキーは有効です")
            return True
        else:
            print("❌ APIキーが無効または制限があります")
            return False
    
    def get_phone_number_from_facility_name(self, facility_name: str) -> Optional[str]:
        """
        施設名から電話番号を取得するメイン関数
        
        Args:
            facility_name (str): 検索する施設名（例：湘南美容クリニック 渋谷）
            
        Returns:
            Optional[str]: 電話番号（例：03-1234-5678）、取得失敗時はNone
        """
        print(f"施設検索開始: {facility_name}")
        
        # Step 1: 施設名でplace_idを検索
        place_id = self.search_place(facility_name)
        if not place_id:
            print(f"place_id取得失敗: {facility_name}")
            return None
        
        print(f"place_id取得成功: {place_id}")
        
        # Step 2: place_idから詳細情報を取得
        details = self.get_place_details(place_id)
        if not details:
            print(f"詳細情報取得失敗: {place_id}")
            return None
        
        # Step 3: 電話番号を抽出
        # formatted_phone_numberを優先、なければinternational_phone_numberを使用
        phone_number = details.get('formatted_phone_number') or details.get('international_phone_number')
        
        if phone_number:
            print(f"電話番号取得成功: {phone_number}")
            return phone_number
        else:
            print(f"電話番号なし: {details.get('name', 'Unknown')}")
            return None


def get_phone_number_from_facility_name(facility_name: str, api_key: str = "AIzaSyDDjzFTsW1X7r2vu9lIy6PtTo9HLmxElJc") -> Optional[str]:
    """
    施設名から電話番号を取得する便利関数
    
    Args:
        facility_name (str): 検索する施設名（例：湘南美容クリニック 渋谷）
        api_key (str): Google Places APIキー（デフォルト値あり）
        
    Returns:
        Optional[str]: 電話番号（例：03-1234-5678）、取得失敗時はNone
    """
    api = GooglePlacesAPI(api_key)
    return api.get_phone_number_from_facility_name(facility_name)


def test_api_key_validity(api_key: str = "AIzaSyDDjzFTsW1X7r2vu9lIy6PtTo9HLmxElJc") -> bool:
    """
    APIキーの有効性をテストする便利関数
    
    Args:
        api_key (str): テストするAPIキー
        
    Returns:
        bool: APIキーが有効な場合True
    """
    api = GooglePlacesAPI(api_key)
    return api.test_api_key()


if __name__ == "__main__":
    print("=== Google Places API 施設電話番号取得システム ===\n")
    
    # まずAPIキーをテスト
    print("Step 1: APIキー有効性チェック")
    if not test_api_key_validity():
        print("\n⚠️ APIキーに問題があります。使用方法を確認してください：")
        print("1. Google Cloud Consoleでプロジェクトを作成")
        print("2. Places APIを有効化")
        print("3. APIキーを生成し、適切な制限を設定")
        print("4. 請求先アカウントを設定（無料枠を超える場合）")
        print("\n有効なAPIキーを取得してから再実行してください。")
        exit(1)
    
    print("\nStep 2: 施設電話番号取得テスト")
    test_facilities = [
        "湘南美容クリニック 渋谷",
        "スターバックス 渋谷スカイ店",
        "東京駅"
    ]
    
    for facility in test_facilities:
        print(f"\n【テスト】 {facility}")
        phone = get_phone_number_from_facility_name(facility)
        if phone:
            print(f"✅ 電話番号: {phone}")
        else:
            print("❌ 電話番号取得失敗")
        print("-" * 50)
    
    print("\n=== テスト完了 ===")
    print("APIキーが有効であれば、上記のように施設の電話番号が取得できます。")
    print("実際の使用時は example_usage.py を参考にしてください。") 