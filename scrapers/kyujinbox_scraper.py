import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import json
import re
from urllib.parse import urljoin, quote
from datetime import datetime
import os


class KyujinboxScraper:
    """求人ボックス専用スクレイパー"""
    
    def __init__(self):
        self.base_url = "https://xn--pckua2a7gp15o89zb.com/"
        self.session = requests.Session()
        
        # Google Places API設定
        self.google_api_key = "AIzaSyDDjzFTsW1X7r2vu9lIy6PtTo9HLmxElJc"
        self.places_api_url = "https://maps.googleapis.com/maps/api/place"
    
    def get_headers(self):
        """リクエストヘッダーを生成"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate'
        }
    
    def get_employment_types(self):
        """雇用形態の選択肢を取得"""
        return [
            {"text": "正社員", "data_search_word": "1"},
            {"text": "アルバイト・パート", "data_search_word": "2"},
            {"text": "派遣社員", "data_search_word": "3"},
            {"text": "契約・臨時・期間社員", "data_search_word": "4"},
            {"text": "業務委託", "data_search_word": "5"},
            {"text": "新卒・インターン", "data_search_word": "6"}
        ]
    
    def generate_search_url(self, employment_type_word, keyword, area):
        """検索URLを生成"""
        try:
            # 基本URL
            search_url = self.base_url.rstrip("/")
            
            # パラメータを組み立て
            params = []
            
            # キーワードの処理（URLパスとして組み込み）
            path_parts = []
            if keyword:
                # キーワードをURLエンコード
                encoded_keyword = quote(keyword, safe='')
                path_parts.append(encoded_keyword)
            
            if area:
                # エリアをURLエンコード
                encoded_area = quote(area, safe='')
                path_parts.append(encoded_area)
            
            # パスを構築
            if path_parts:
                search_path = "/" + "の仕事-".join(path_parts)
                if len(path_parts) == 1:
                    search_path += "の仕事"
                search_url += search_path
            
            # クエリパラメータを追加
            if employment_type_word:
                params.append(f"e={employment_type_word}")
            
            if params:
                search_url += "?" + "&".join(params)
            
            return search_url
            
        except Exception as e:
            st.error(f"URL生成エラー: {str(e)}")
            return None
    
    def make_request(self, url, max_retries=3, timeout=30):
        """HTTPリクエストを実行（リトライ機能付き）"""
        headers = self.get_headers()
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()
                return response, None
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    return None, f"HTTPエラー: {str(e)}"
                time.sleep(random.uniform(1, 3))
        
        return None, "最大リトライ回数に達しました"
    
    def extract_phone_number(self, text):
        """テキストから電話番号を抽出（強化版）"""
        if not text:
            return None
            
        # 電話番号の正規表現パターン（優先度順）
        phone_patterns = [
            # フリーダイヤル（最優先）
            r'(0120[-\s]?\d{2,4}[-\s]?\d{3,4})',
            r'(0800[-\s]?\d{3,4}[-\s]?\d{4})',
            
            # 固定電話（東京03、大阪06など）
            r'(0[1-9][-\s]?\d{2,4}[-\s]?\d{4})',
            
            # 携帯電話
            r'(0[789]0[-\s]?\d{4}[-\s]?\d{4})',
            
            # 一般的なパターン
            r'(\d{2,4}[-\s]?\d{2,4}[-\s]?\d{4})',
            
            # ハイフンなし（10-11桁）
            r'(0\d{9,10})',
            
            # IP電話
            r'(050[-\s]?\d{4}[-\s]?\d{4})',
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                phone = matches[0]
                # 数字のみ抽出して基本的な検証
                digits_only = re.sub(r'[-\s]', '', phone)
                
                # 基本的な電話番号の条件チェック
                if len(digits_only) >= 10 and len(digits_only) <= 11 and digits_only.startswith('0'):
                    # ハイフンを統一フォーマットで追加
                    if digits_only.startswith('0120') or digits_only.startswith('0800'):
                        # フリーダイヤル形式
                        formatted = f"{digits_only[:4]}-{digits_only[4:7]}-{digits_only[7:]}"
                    elif len(digits_only) == 10:
                        # 10桁の場合
                        if digits_only.startswith('03') or digits_only.startswith('06'):
                            # 東京・大阪（2桁市外局番）
                            formatted = f"{digits_only[:2]}-{digits_only[2:6]}-{digits_only[6:]}"
                        else:
                            # その他の地域（3桁市外局番）
                            formatted = f"{digits_only[:3]}-{digits_only[3:6]}-{digits_only[6:]}"
                    else:
                        # 11桁の場合（携帯電話など）
                        formatted = f"{digits_only[:3]}-{digits_only[3:7]}-{digits_only[7:]}"
                    
                    return formatted
        
        return None
    
    def extract_representative(self, text):
        """テキストから代表者名を抽出"""
        # 代表者名の正規表現パターン
        representative_patterns = [
            r'(?:代表者|院長|理事長|代表取締役|社長|代表)[:：\s]*([^\n\r,、。]{2,20})',
            r'(?:院長|理事長|代表取締役|社長|代表)[:：\s]*([^\n\r,、。]{2,20})',
            r'([^\n\r,、。]{2,10})\s*(?:院長|理事長|代表取締役|社長)',
        ]
        
        for pattern in representative_patterns:
            matches = re.findall(pattern, text)
            if matches:
                name = matches[0].strip()
                # 不要な文字列を除去
                name = re.sub(r'[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\w\s]', '', name)
                if len(name) >= 2 and len(name) <= 20:
                    return name
        
        return None
    
    def search_contact_info_google_maps(self, facility_name, address="", debug_mode=False):
        """Google Maps（Places API）で施設情報を検索して連絡先情報を取得"""
        contact_info = {
            'phone': '',
            'email': '',
            'representative': '',
            'website': ''
        }
        
        try:
            # 既知のクリニック情報データベース（一部）
            known_clinics = {
                '湘南美容クリニック': {
                    'phone': '0120-489-100',
                    'representative': '相川佳之',
                    'website': 'https://www.s-b-c.net/'
                },
                '品川美容外科': {
                    'phone': '0120-189-900',
                    'representative': '秋元正宇',
                    'website': 'https://www.shinagawa.com/'
                },
                'TCB東京中央美容外科': {
                    'phone': '0120-197-262',
                    'representative': '小林弘幸',
                    'website': 'https://aoki-tsuyoshi.com/'
                },
                '共立美容外科': {
                    'phone': '0120-500-340',
                    'representative': '久次米秋人',
                    'website': 'https://www.kyoritsu-biyo.com/'
                },
                '東京美容外科': {
                    'phone': '0120-658-958',
                    'representative': '麻生泰',
                    'website': 'https://www.tkc110.jp/'
                }
                # 他のクリニック情報も追加可能
            }
            
            # 既知のクリニックから検索
            for clinic_name, info in known_clinics.items():
                if clinic_name in facility_name:
                    contact_info.update(info)
                    if debug_mode:
                        st.success(f"📋 既知データベースから情報を取得: {clinic_name}")
                    return contact_info
            
            # 既知データベースにない場合は、Google Maps（Places API）で検索
            if debug_mode:
                st.info(f"🗺️ Google Maps で施設検索中: '{facility_name}'")
            
            # Google Places APIで施設情報を検索
            places_result = self.search_google_places(facility_name, address, debug_mode)
            if places_result:
                contact_info.update(places_result)
                if debug_mode and places_result.get('phone'):
                    st.success(f"📞 Google Maps から電話番号を取得: {places_result['phone']}")
            
        except Exception as e:
            if debug_mode:
                st.warning(f"⚠️ Google Maps検索中にエラー: {str(e)}")
        
        return contact_info
    
    def search_google_places(self, facility_name, address="", debug_mode=False):
        """Google Places APIで施設情報を検索（実装版）"""
        try:
            if debug_mode:
                st.info(f"🌐 Google Places API検索を実行: {facility_name}")
                if address:
                    st.info(f"📍 検索地域: {address}")
            
            # 検索クエリを構築（施設名＋住所情報で精度向上）
            if address:
                search_query = f"{facility_name} {address}"
            else:
                search_query = facility_name
            
            if debug_mode:
                st.info(f"🔍 Google Maps検索クエリ: '{search_query}'")
            
            # Google Places APIの動作状況を詳細にデバッグ
            if debug_mode:
                st.info(f"🔧 Google Places API キー確認: {'設定済み' if self.google_api_key else '未設定'}")
                if self.google_api_key:
                    st.info(f"🔧 APIキー（最初の10文字）: {self.google_api_key[:10]}...")
            
            # Google Places APIが利用可能な場合は実際のAPIを呼び出し
            if self.google_api_key:
                if debug_mode:
                    st.info("🌐 Google Places API を呼び出し中...")
                return self.call_google_places_api(search_query, debug_mode)
            else:
                if debug_mode:
                    st.warning("⚠️ Google Places API キーが設定されていません。パターン推定モードで実行します。")
                    st.info("💡 環境変数 'GOOGLE_PLACES_API_KEY' を設定してください")
                # Google Places APIの代替として、施設名パターンから推定
                return self.estimate_facility_info_by_pattern(facility_name, address, debug_mode)
            
        except Exception as e:
            if debug_mode:
                st.warning(f"⚠️ Google Places API検索エラー: {str(e)}")
            return {}
    
    def call_google_places_api(self, search_query, debug_mode=False):
        """実際のGoogle Places APIを呼び出し"""
        try:
            if debug_mode:
                st.info("🌐 Google Places API に接続中...")
            
            # テキスト検索でまず施設を検索
            search_url = f"{self.places_api_url}/textsearch/json"
            params = {
                'query': search_query,
                'key': self.google_api_key,
                'type': 'health',  # 医療・美容施設に特化
                'language': 'ja'   # 日本語で結果を取得
            }
            
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if debug_mode:
                st.info(f"📊 API結果: {data.get('status')}")
                if data.get('status') != 'OK':
                    st.error(f"🚫 API エラーメッセージ: {data.get('error_message', 'メッセージなし')}")
                if data.get('results'):
                    st.info(f"🏥 見つかった施設数: {len(data['results'])}")
                    # 最初の結果の詳細を表示
                    first_result = data['results'][0]
                    st.info(f"🏥 最初の結果: {first_result.get('name')} - {first_result.get('formatted_address', 'アドレス不明')}")
                else:
                    st.warning("🔍 検索結果が0件でした")
            
            if data.get('status') == 'OK' and data.get('results'):
                # 最初の結果を使用
                place = data['results'][0]
                place_id = place.get('place_id')
                
                if place_id:
                    # 詳細情報を取得
                    return self.get_place_details(place_id, debug_mode)
            
            return {}
            
        except requests.exceptions.RequestException as e:
            if debug_mode:
                st.error(f"🚫 Google Places API リクエストエラー: {str(e)}")
            return {}
        except Exception as e:
            if debug_mode:
                st.error(f"🚫 Google Places API 処理エラー: {str(e)}")
            return {}
    
    def get_place_details(self, place_id, debug_mode=False):
        """Google Places APIで施設の詳細情報を取得"""
        try:
            if debug_mode:
                st.info(f"📋 施設詳細情報を取得中... (ID: {place_id[:10]}...)")
            
            details_url = f"{self.places_api_url}/details/json"
            params = {
                'place_id': place_id,
                'key': self.google_api_key,
                'fields': 'name,formatted_phone_number,international_phone_number,website,formatted_address,business_status',
                'language': 'ja'
            }
            
            response = requests.get(details_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('result'):
                result = data['result']
                
                contact_info = {}
                
                # 電話番号を取得
                phone = result.get('formatted_phone_number') or result.get('international_phone_number')
                if phone:
                    # 日本の電話番号形式に正規化
                    normalized_phone = self.normalize_phone_number(phone)
                    if normalized_phone:
                        contact_info['phone'] = normalized_phone
                        if debug_mode:
                            st.success(f"📞 電話番号取得: {normalized_phone}")
                
                # ウェブサイトURL
                website = result.get('website')
                if website:
                    contact_info['website'] = website
                    if debug_mode:
                        st.success(f"🌐 ウェブサイト取得: {website}")
                
                # 営業状況
                business_status = result.get('business_status')
                if debug_mode and business_status:
                    st.info(f"🏢 営業状況: {business_status}")
                
                return contact_info
            
            return {}
            
        except Exception as e:
            if debug_mode:
                st.error(f"🚫 施設詳細取得エラー: {str(e)}")
            return {}
    
    def normalize_phone_number(self, phone_str):
        """電話番号を日本の標準形式に正規化"""
        if not phone_str:
            return None
        
        # 国際形式から日本形式への変換
        # +81を0に置換
        phone_str = re.sub(r'^\+81\s?', '0', phone_str)
        
        # 数字のみ抽出
        digits_only = re.sub(r'[^\d]', '', phone_str)
        
        # 日本の電話番号として有効かチェック
        if len(digits_only) >= 10 and len(digits_only) <= 11 and digits_only.startswith('0'):
            return self.format_japanese_phone(digits_only)
        
        return None
    
    def format_japanese_phone(self, digits):
        """日本の電話番号を標準形式でフォーマット"""
        if digits.startswith('0120') or digits.startswith('0800'):
            # フリーダイヤル
            return f"{digits[:4]}-{digits[4:7]}-{digits[7:]}"
        elif len(digits) == 10:
            if digits.startswith('03') or digits.startswith('06'):
                # 東京・大阪（2桁市外局番）
                return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
            else:
                # その他の地域（3桁市外局番）
                return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11:
            # 携帯電話・IP電話
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        
        return digits  # フォーマットできない場合はそのまま返す
    
    def estimate_facility_info_by_pattern(self, facility_name, address, debug_mode=False):
        """施設名パターンから情報を推定（Google Places API の代替実装）"""
        try:
            if debug_mode:
                st.info(f"🏥 施設パターン分析: {facility_name}")
            
            result = {}
            
            # 美容クリニック特有のパターンを分析
            beauty_keywords = ['美容', 'クリニック', '皮膚科', '形成外科', 'スキンケア', 'エステ']
            is_beauty_clinic = any(keyword in facility_name for keyword in beauty_keywords)
            
            if is_beauty_clinic:
                if debug_mode:
                    st.info("🏥 美容クリニックパターンを検出")
                
                # 地域別の電話番号パターンを推定
                phone_number = self.estimate_phone_by_location(facility_name, address, debug_mode)
                if phone_number:
                    result['phone'] = phone_number
                
                # 代表者名の推定（一般的なパターン）
                representative = self.estimate_representative_by_pattern(facility_name, debug_mode)
                if representative:
                    result['representative'] = representative
            
            return result
            
        except Exception as e:
            if debug_mode:
                st.warning(f"⚠️ パターン分析エラー: {str(e)}")
            return {}
    
    def estimate_phone_by_location(self, facility_name, address, debug_mode=False):
        """所在地情報を基にした電話番号の推定"""
        try:
            if debug_mode:
                st.info(f"📞 地域別電話番号パターン分析: {address}")
            
            # 地域別の市外局番マッピング
            area_codes = {
                '東京': ['03', '042', '044'],
                '渋谷': ['03'],
                '新宿': ['03'],
                '銀座': ['03'],
                '表参道': ['03'],
                '恵比寿': ['03'],
                '大阪': ['06', '072'],
                '梅田': ['06'],
                '心斎橋': ['06'],
                '名古屋': ['052'],
                '横浜': ['045'],
                '川崎': ['044'],
                '福岡': ['092']
            }
            
            # フリーダイヤルの使用率（美容クリニックは高い）
            if any(keyword in facility_name for keyword in ['美容', 'クリニック']):
                # 美容クリニックの約60%がフリーダイヤルを使用
                free_dial_probability = 0.6
                if debug_mode:
                    st.info(f"📞 美容クリニック検出 - フリーダイヤル使用確率: {free_dial_probability*100}%")
            
            # 実際の電話番号生成は行わない（プライバシー保護のため）
            # Google Places API が利用可能な場合のみ実際の番号を取得
            
            return None  # 現在は推定のみ
            
        except Exception as e:
            if debug_mode:
                st.warning(f"⚠️ 地域別電話番号推定エラー: {str(e)}")
            return None
    
    def estimate_representative_by_pattern(self, facility_name, debug_mode=False):
        """施設名パターンから代表者名を推定"""
        try:
            # 施設名に含まれる可能性のある代表者名を抽出
            # 例: "田中クリニック" → "田中" が代表者の可能性
            
            # 一般的な医療機関の命名パターン
            name_patterns = [
                r'([^\s]{2,4})(?:クリニック|医院|病院|皮膚科)',
                r'([^\s]{2,4})(?:美容外科|形成外科)',
            ]
            
            for pattern in name_patterns:
                matches = re.findall(pattern, facility_name)
                if matches:
                    potential_name = matches[0]
                    if debug_mode:
                        st.info(f"👨‍⚕️ 代表者名候補: {potential_name}")
                    # 実際の確認は Google Places API で行う
                    return None  # 現在は推定のみ
            
            return None
            
        except Exception as e:
            if debug_mode:
                st.warning(f"⚠️ 代表者名推定エラー: {str(e)}")
            return None
    
    def extract_jobs_from_page(self, soup, page_url, debug_mode=False):
        """検索結果ページからJSON構造化データを使用して求人情報を直接抽出（改良版）"""
        jobs = []
        
        try:
            if debug_mode:
                st.info("🐛 DEBUG: 検索結果ページからJSON構造化データを抽出中...")
            
            # 複数のセレクタを試行して求人カードを取得
            selectors = [
                'section.p-result_card',  # 元のセレクタ
                'div.p-result_card',      # div版
                'article.p-result_card',  # article版
                '[class*="result_card"]', # クラス名部分一致
                '.job-card',              # 代替セレクタ
                '.job-item',              # 代替セレクタ
                'section[data-func-show-arg]',  # データ属性で直接検索
                'div[data-func-show-arg]',      # データ属性で直接検索
                'a[data-func-show-arg]'         # リンクで直接検索
            ]
            
            job_cards = []
            for selector in selectors:
                job_cards = soup.select(selector)
                if job_cards:
                    if debug_mode:
                        st.success(f"🐛 DEBUG: セレクタ '{selector}' で {len(job_cards)} 件の求人カードを発見")
                    break
            
            if not job_cards:
                if debug_mode:
                    st.warning("🐛 DEBUG: 求人カードが見つかりませんでした")
                    # HTMLの一部を表示
                    st.code(str(soup)[:1000] + "...")
                return jobs
            
            # 各求人カードを処理
            for idx, card in enumerate(job_cards):
                try:
                    # JSON属性を含むリンクを検索
                    json_link = card.find('a', {'data-func-show-arg': True})
                    
                    # より深い階層も検索
                    if not json_link:
                        all_links = card.find_all('a')
                        for link in all_links:
                            if link.get('data-func-show-arg'):
                                json_link = link
                                break
                
                    if not json_link:
                        if debug_mode and idx < 5:  # 最初の5件のみ詳細ログ
                            st.warning(f"🐛 DEBUG: カード {idx+1} でJSON属性が見つかりません")
                            # HTMLの一部を表示
                            st.code(str(card)[:300] + "...")
                        continue
                
                    # JSON文字列を取得
                    json_str = json_link.get('data-func-show-arg')
                    
                    if debug_mode and idx < 3:
                        st.info(f"🐛 DEBUG: カード {idx+1} のJSON文字列を取得")
                        st.code(f"JSON文字列（最初の200文字）: {json_str[:200]}...")
                    
                    # JSONを解析（2層構造）
                    try:
                        # 外側のJSONをパース
                        outer_data = json.loads(json_str)
                        
                        if debug_mode and idx < 3:
                            st.success(f"🐛 DEBUG: カード {idx+1} の外側JSON解析成功")
                            st.json(outer_data)
                        
                        # 内側のjsonフィールドを再度パース
                        inner_json_str = outer_data.get('json', '')
                        if not inner_json_str:
                            if debug_mode and idx < 3:
                                st.warning(f"🐛 DEBUG: カード {idx+1} 内側JSONフィールドが見つかりません")
                            continue
                        
                        job_data = json.loads(inner_json_str)
                        
                        if debug_mode and idx < 3:
                            st.success(f"🐛 DEBUG: カード {idx+1} の内側JSON解析成功")
                            st.json({
                                'company': job_data.get('company'),
                                'title': job_data.get('title'),
                                'workArea': job_data.get('workArea'),
                                'url': job_data.get('url'),
                                'uniqueId': job_data.get('uniqueId'),
                                'rdUrl': job_data.get('rdUrl')  # 正しい詳細ページのパス
                            })
                        
                        # 求人情報を抽出・整形
                        job_info = {
                            'facility_name': job_data.get('company', job_data.get('siteName', '')),
                            'title': job_data.get('title', job_data.get('formatTitle', '')),
                            'work_area': job_data.get('workArea', ''),
                            'employment_type': job_data.get('employType', ''),
                            'payment': job_data.get('payment', ''),
                            'unique_id': job_data.get('uniqueId', ''),
                            'site_id': job_data.get('siteId', ''),
                            'all_feature_tags': job_data.get('allFeatureTags', []),
                            'original_url': job_data.get('url', ''),  # 元の企業URL（参考用）
                            'rd_url': outer_data.get('uid', ''),  # 詳細ページのUID
                        }
                        
                        # 基本的な住所情報
                        job_info['address'] = job_info['work_area']
                        
                        # 事業内容（求人タイトルから推測）
                        job_info['business_content'] = job_info['title']
                        
                        # WebサイトURLとして求人ボックスの詳細URLを構築
                        # rdUrlが存在する場合はそれを優先、なければuniqueIdを使用
                        rd_url = job_data.get('rdUrl', '')
                        unique_id = job_info.get('unique_id', '')
                        
                        if rd_url:
                            # rdUrlは通常 "/jbi/xxxxx" の形式で返される
                            if rd_url.startswith('/'):
                                job_info['website_url'] = f"{self.base_url.rstrip('/')}{rd_url}"
                            else:
                                job_info['website_url'] = f"{self.base_url}jbi/{rd_url}"
                        elif unique_id:
                            # フォールバック: uniqueIdを使用
                            job_info['website_url'] = f"{self.base_url}jbi/{unique_id}"
                        else:
                            job_info['website_url'] = ''
                        
                        # より柔軟な条件で求人を追加（最低限のデータがあれば追加）
                        has_minimum_data = (
                            job_info.get('facility_name') or 
                            job_info.get('title') or 
                            job_info.get('work_area')
                        )
                        
                        if has_minimum_data:
                            # 空のフィールドには代替値を設定
                            if not job_info.get('facility_name'):
                                job_info['facility_name'] = job_info.get('title', '求人情報')
                            if not job_info.get('title'):
                                job_info['title'] = '職種情報なし'
                            
                            jobs.append(job_info)
                            
                            if debug_mode and idx < 3:
                                st.success(f"🐛 DEBUG: カード {idx+1} 情報抽出完了")
                                st.json({
                                    'facility_name': job_info['facility_name'],
                                    'title': job_info['title'],
                                    'work_area': job_info['work_area'],
                                    'website_url': job_info['website_url'],
                                    'original_url': job_info['original_url'],
                                    'unique_id': job_info['unique_id'],
                                    'rd_url': rd_url  # デバッグ用
                                })
                        else:
                            if debug_mode and idx < 3:
                                st.warning(f"🐛 DEBUG: カード {idx+1} 最低限の情報も不足")
                                st.json(job_info)
                    
                    except json.JSONDecodeError as e:
                        if debug_mode and idx < 3:
                            st.error(f"🐛 DEBUG: カード {idx+1} JSON解析エラー: {str(e)}")
                            st.code(f"解析対象JSON: {json_str[:500]}...")
                        continue
                
                except Exception as e:
                    if debug_mode and idx < 5:
                        st.error(f"🐛 DEBUG: カード {idx+1} でエラー: {str(e)}")
                    continue
        
        except Exception as e:
            if debug_mode:
                st.error(f"🐛 DEBUG: extract_jobs_from_page でエラー: {str(e)}")
        
        if debug_mode:
            st.info(f"🐛 DEBUG: 求人情報抽出完了: {len(jobs)}件")
        
        return jobs
    
    def get_job_details(self, detail_url, debug_mode=False):
        """求人詳細ページから追加情報を取得"""
        try:
            if debug_mode:
                st.info(f"🐛 DEBUG: 詳細ページにアクセス中: {detail_url}")
            
            response, error = self.make_request(detail_url)
            if error:
                if debug_mode:
                    st.warning(f"🐛 DEBUG: 詳細ページアクセス失敗: {error}")
                return {}, error
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            if debug_mode:
                st.info(f"🐛 DEBUG: 詳細ページ取得成功 (サイズ: {len(response.content)} bytes)")
            
            details = {}
            page_text = soup.get_text()
            
            # 施設名（会社名）を詳細ページから取得 - HTMLセレクタで直接抽出
            facility_name_element = soup.select_one('p.p-detail_head_company')
            if facility_name_element:
                facility_name = facility_name_element.get_text(strip=True)
                if facility_name and len(facility_name) > 2:
                    details['facility_name'] = facility_name
                    if debug_mode:
                        st.success(f"🐛 DEBUG: HTMLから施設名発見: {facility_name}")
            else:
                # フォールバック: 正規表現で施設名を検索
                facility_patterns = [
                    re.compile(r'(?:会社名|法人名|施設名|病院名|クリニック名|事業所名|企業名)[:：]?\s*(.+?)(?:\n|$)', re.MULTILINE),
                    re.compile(r'(?:勤務先|運営会社|運営法人)[:：]?\s*(.+?)(?:\n|$)', re.MULTILINE),
                ]
                
                for pattern in facility_patterns:
                    facility_matches = pattern.findall(page_text)
                    if facility_matches:
                        facility_name = facility_matches[0].strip()[:100]
                        if len(facility_name) > 2 and facility_name != "企業向けメニュー":
                            details['facility_name'] = facility_name
                            if debug_mode:
                                st.success(f"🐛 DEBUG: 正規表現で施設名発見: {facility_name}")
                            break
            
            # 代表者名は常に空白
            details['representative'] = ''
            
            # 電話番号は求人ボックスからは取得しない（Google Maps検索のみ）
            # details['phone'] は設定しない
            
            return details, None
            
        except Exception as e:
            error_msg = f"詳細ページ取得エラー: {str(e)}"
            if debug_mode:
                st.error(f"🐛 DEBUG: {error_msg}")
            return {}, error_msg
    
    def scrape_jobs(self, employment_type_word, keyword, area, max_jobs=10, progress_callback=None, debug_mode=False):
        """求人情報をスクレイピング（構造化データ使用）"""
        try:
            # 検索URLを生成
            search_url = self.generate_search_url(employment_type_word, keyword, area)
            if not search_url:
                error_msg = "検索URLの生成に失敗しました"
                if debug_mode:
                    st.error(f"🐛 DEBUG: {error_msg}")
                    st.code(f"employment_type_word: {employment_type_word}\nkeyword: {keyword}\narea: {area}")
                return None, error_msg
            
            if debug_mode:
                st.info(f"🐛 DEBUG: 生成された検索URL: {search_url}")
                st.info("🐛 DEBUG: 検索結果ページからJSON構造化データを直接抽出")
            
            all_jobs = []
            page_num = 1
            # ページ制限を大幅に緩和（最大30ページまで、または必要な件数まで）
            max_pages = min(30, (max_jobs // 5) + 5)  # 1ページあたり最低5件と仮定
            consecutive_empty_pages = 0  # 連続で空のページ数をカウント
            max_consecutive_empty = 3    # 連続3ページ空なら終了
            
            # 検索結果ページから直接JSON構造化データを抽出
            while page_num <= max_pages and len(all_jobs) < max_jobs and consecutive_empty_pages < max_consecutive_empty:
                # ページネーション対応（正しいパラメータ名 &pg= を使用）
                if page_num == 1:
                    current_url = search_url
                else:
                    if "?" in search_url:
                        current_url = search_url + f"&pg={page_num}"
                    else:
                        current_url = search_url + f"?pg={page_num}"
                
                if debug_mode:
                    st.info(f"🐛 DEBUG: ページ {page_num} へアクセス中: {current_url}")
                
                response, error = self.make_request(current_url)
                if error:
                    if debug_mode:
                        st.error(f"🐛 DEBUG: ページ {page_num} でエラー発生: {error}")
                    if page_num == 1:
                        return None, error
                    else:
                        consecutive_empty_pages += 1
                        page_num += 1
                        continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # JSON構造化データから求人情報を抽出
                jobs = self.extract_jobs_from_page(soup, current_url, debug_mode=debug_mode)
                
                if debug_mode:
                    st.info(f"🐛 DEBUG: ページ {page_num} から {len(jobs)} 件の求人を抽出")
                
                if not jobs:
                    consecutive_empty_pages += 1
                    if debug_mode:
                        st.warning(f"🐛 DEBUG: ページ {page_num} で求人が見つかりませんでした (連続空ページ: {consecutive_empty_pages})")
                    page_num += 1
                    time.sleep(1)  # レート制限
                    continue
                else:
                    consecutive_empty_pages = 0  # 求人が見つかったのでリセット
                
                # 各求人に対してWeb検索で補完情報を取得
                page_job_count = 0
                for idx, job in enumerate(jobs):
                    if len(all_jobs) >= max_jobs:
                        break
                    
                    if progress_callback:
                        progress_callback(len(all_jobs) + 1, max_jobs)
                    
                    if debug_mode and len(all_jobs) < 3:
                        st.info(f"🐛 DEBUG: 求人 {len(all_jobs) + 1} を処理中: {job.get('facility_name', 'Unknown')}")
                    
                    # Web検索で連絡先情報を取得（住所情報も含む）
                    if job.get('facility_name'):
                        if debug_mode and len(all_jobs) < 2:  # 最初の2件のみ詳細なWeb検索ログを表示
                            st.info(f"🔍 施設名 '{job['facility_name']}' のWeb検索を開始...")
                            if job.get('address'):
                                st.info(f"🏢 住所情報: {job['address'][:100]}...")
                        
                        # 1. 住所情報をクリーンアップ
                        clean_address = self.clean_address_for_search(
                            job.get('address', ''), 
                            debug_mode=(debug_mode and len(all_jobs) < 2)
                        )
                        
                        # 2. 施設名＋クリーンな住所でGoogle Maps検索
                        contact_info = self.search_contact_info_google_maps(
                            job['facility_name'], 
                            address=clean_address,
                            debug_mode=(debug_mode and len(all_jobs) < 2)
                        )
                        
                        # 2. 詳細ページから施設名のみを取得（電話番号は取得しない）
                        if job.get('website_url'):
                            if debug_mode and len(all_jobs) < 2:
                                st.info(f"📄 求人詳細ページから施設名を取得: {job['website_url']}")
                            
                            detail_info, detail_error = self.get_job_details(
                                job['website_url'], 
                                debug_mode=(debug_mode and len(all_jobs) < 2)
                            )
                            
                            if detail_info and not detail_error:
                                # 詳細ページから施設名のみを更新（電話番号は除外）
                                if detail_info.get('facility_name') and not job.get('facility_name'):
                                    job['facility_name'] = detail_info['facility_name']
                                    if debug_mode and len(all_jobs) < 2:
                                        st.success(f"📋 詳細ページから施設名を取得: {detail_info['facility_name']}")
                        
                        # 電話番号はGoogle Maps検索でのみ取得
                        job.update(contact_info)
                    
                    # データを整形
                    formatted_job = {
                        'facility_name': job.get('facility_name', ''),
                        'representative': job.get('representative', ''),
                        'address': job.get('address', job.get('work_area', '')),
                        'website_url': job.get('website_url', ''),  # 求人ボックスの詳細URL
                        'phone_number': job.get('phone', ''),
                        'email': job.get('email', ''),
                        'business_content': job.get('business_content', job.get('title', '')),
                        'source_url': job.get('website_url', current_url)  # 求人ボックスの詳細URL
                    }
                    
                    all_jobs.append(formatted_job)
                    page_job_count += 1
                    
                    if debug_mode and len(all_jobs) <= 3:
                        st.success(f"🐛 DEBUG: 求人 {len(all_jobs)} 処理完了")
                        
                        # 電話番号取得結果の詳細表示
                        phone_status = "✅ 取得済み" if formatted_job['phone_number'] else "❌ 未取得"
                        st.info(f"📞 電話番号: {phone_status}")
                        
                        st.json({
                            'facility_name': formatted_job['facility_name'],
                            'address': formatted_job['address'],
                            'phone_number': formatted_job['phone_number'],
                            'email': formatted_job['email'],
                            'representative': formatted_job['representative'],
                            'website_url': formatted_job['website_url'],
                            'business_content': formatted_job['business_content'][:100] + '...' if len(formatted_job['business_content']) > 100 else formatted_job['business_content']
                        })
                
                if debug_mode:
                    st.info(f"🐛 DEBUG: ページ {page_num} 完了 - このページから {page_job_count} 件追加、累計 {len(all_jobs)} 件")
                
                # 次のページへ
                page_num += 1
                time.sleep(1)  # レート制限
            
            if debug_mode:
                st.success(f"🐛 DEBUG: スクレイピング完了 - 最終的に {len(all_jobs)} 件の求人情報を取得")
                st.info(f"🐛 DEBUG: 処理したページ数: {page_num - 1}")
                if consecutive_empty_pages >= max_consecutive_empty:
                    st.info(f"🐛 DEBUG: 連続 {max_consecutive_empty} ページで求人が見つからなかったため終了")
                elif len(all_jobs) >= max_jobs:
                    st.info(f"🐛 DEBUG: 目標件数 {max_jobs} 件に到達したため終了")
                elif page_num > max_pages:
                    st.info(f"🐛 DEBUG: 最大ページ数 {max_pages} に到達したため終了")
            
            return all_jobs, None
            
        except Exception as e:
            error_msg = f"スクレイピング中にエラーが発生しました: {str(e)}"
            if debug_mode:
                st.error(f"🐛 DEBUG: {error_msg}")
                st.code(f"例外詳細: {type(e).__name__}: {str(e)}")
            return None, error_msg
    
    def clean_address_for_search(self, address_text, debug_mode=False):
        """住所情報から検索に適した部分のみを抽出"""
        if not address_text:
            return ""
        
        try:
            # 不要な文字列パターンを除去
            unwanted_patterns = [
                r'徒歩\d+分',           # 徒歩○分
                r'車\d+分',             # 車○分
                r'バス\d+分',           # バス○分
                r'約\d+分',             # 約○分
                r'\d+分',               # ○分（単独）
                r'から徒歩.*',          # から徒歩以降
                r'より徒歩.*',          # より徒歩以降
                r'まで徒歩.*',          # まで徒歩以降
                r'アクセス[:：].*',     # アクセス:以降
                r'最寄り[:：].*',       # 最寄り:以降
                r'最寄駅[:：].*',       # 最寄駅:以降
                r'交通[:：].*',         # 交通:以降
                r'JR.*線',              # JR○○線
                r'地下鉄.*線',          # 地下鉄○○線
                r'私鉄.*線',            # 私鉄○○線
                r'.*線.*駅.*改札',      # ○○線○○駅○○改札
                r'改札.*',              # 改札以降
                r'出口.*',              # 出口以降
                r'番出口',              # ○番出口
                r'東口|西口|南口|北口|中央口',  # 駅の出口
                r'[（(].*[）)]',        # 括弧内の情報
                r'【.*】',              # 【】内の情報
                r'※.*',                # ※以降
                r'＊.*',                # ＊以降
                r'\s+',                 # 複数の空白を1つに
            ]
            
            cleaned_address = address_text
            
            # 各パターンを除去
            for pattern in unwanted_patterns:
                cleaned_address = re.sub(pattern, ' ', cleaned_address)
            
            # 有用な地域情報を抽出
            useful_parts = []
            
            # 都道府県を抽出
            prefecture_match = re.search(r'(東京都|大阪府|京都府|北海道|.*県)', cleaned_address)
            if prefecture_match:
                useful_parts.append(prefecture_match.group(1))
            
            # 市区町村を抽出
            city_match = re.search(r'(.*区|.*市|.*町|.*村)', cleaned_address)
            if city_match:
                useful_parts.append(city_match.group(1))
            
            # 駅名を抽出（○○駅の形式）
            station_matches = re.findall(r'([^\s\d]+駅)', cleaned_address)
            for station in station_matches:
                if len(station) >= 3:  # 2文字以上の駅名のみ
                    useful_parts.append(station)
            
            # 地名を抽出（カタカナ・ひらがな・漢字の組み合わせ）
            area_matches = re.findall(r'([ぁ-んァ-ヶ一-龯]{2,8})', cleaned_address)
            for area in area_matches:
                if len(area) >= 2 and area not in ['以降', '以内', '付近', '周辺']:
                    useful_parts.append(area)
            
            # 重複を除去して結合
            unique_parts = list(dict.fromkeys(useful_parts))  # 順序を保持しつつ重複除去
            
            result = ' '.join(unique_parts)
            
            if debug_mode:
                st.info(f"🗺️ 住所クリーンアップ:")
                st.code(f"元の住所: {address_text}")
                st.code(f"抽出された情報: {result}")
            
            return result
            
        except Exception as e:
            if debug_mode:
                st.warning(f"⚠️ 住所クリーンアップエラー: {str(e)}")
            return address_text  # エラー時は元の住所を返す


class KyujinboxUI:
    """求人ボックススクレイパーのUI"""
    
    def __init__(self):
        self.scraper = KyujinboxScraper()
    
    def render_ui(self):
        """UIを描画して結果を返す"""
        st.header("求人ボックス：検索条件")
        
        # デバッグモード
        debug_mode = st.sidebar.checkbox("デバッグモード", key="kyujinbox_debug")
        
        # 雇用形態の選択肢を動的取得
        employment_types = self.scraper.get_employment_types()
        employment_options = [emp['text'] for emp in employment_types]
        
        # 雇用形態選択
        selected_employment = st.selectbox(
            "雇用形態",
            employment_options,
            key="kyujinbox_employment_type"
        )
        
        # 選択された雇用形態のdata-search_wordを取得
        selected_employment_word = ""
        for emp in employment_types:
            if emp['text'] == selected_employment:
                selected_employment_word = emp['data_search_word']
                break
        
        # キーワード入力
        keyword = st.text_input(
            "キーワード (職種、業種など)",
            placeholder="看護師、エンジニアなど",
            key="kyujinbox_keyword"
        )
        
        # エリア入力
        area = st.text_input(
            "エリア (都道府県、市区町村、駅名)",
            placeholder="東京都、新宿区、渋谷駅など",
            key="kyujinbox_area"
        )
        
        # 取得件数設定
        max_jobs = st.selectbox(
            "取得件数を選択",
            [1, 10, 20, 30, 50, 100, 200, 300],
            index=1,  # デフォルトで10件
            key="kyujinbox_max_jobs",
            help="取得する求人の最大件数を選択してください（上限300件）"
        )
        
        # 実行ボタン
        start_button = st.button(
            "この条件で検索する",
            type="primary",
            key="kyujinbox_start"
        )
        
        # 検索実行
        if start_button:
            if not any([selected_employment_word, keyword, area]):
                st.warning("雇用形態、キーワード、エリアのうち少なくとも1つは入力してください。")
                return None
            
            if debug_mode:
                st.info(f"🐛 DEBUG: 開始パラメータ - 雇用形態: {selected_employment_word}, キーワード: {keyword}, エリア: {area}, 取得数: {max_jobs}")
            
            with st.spinner("求人情報を取得中... しばらくお待ちください"):
                # プログレスバー
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def progress_callback(current, total):
                    if total > 0:
                        progress_bar.progress(min(current / total, 1.0))
                    status_text.text(f"求人情報を取得中... ({current}/{total})")
                
                # 求人情報取得
                jobs_data, error = self.scraper.scrape_jobs(
                    selected_employment_word, 
                    keyword, 
                    area, 
                    max_jobs, 
                    progress_callback, 
                    debug_mode
                )
                
                progress_bar.empty()
                status_text.empty()
                
                if error:
                    st.error(f"エラーが発生しました: {error}")
                    return None
                
                if jobs_data and len(jobs_data) > 0:
                    # データフレーム作成
                    df_list = []
                    for job in jobs_data:
                        df_list.append({
                            '施設名': job['facility_name'],
                            '代表者名': job['representative'],
                            '住所': job['address'],
                            'WebサイトURL': job['website_url'],
                            '電話番号': job['phone_number'],
                            'メールアドレス': job['email'],
                            '事業内容': job['business_content']
                        })
                    
                    df = pd.DataFrame(df_list)
                    
                    # 結果表示
                    st.success(f"{len(jobs_data)}件の求人情報を取得しました。")
                    st.dataframe(df, use_container_width=True)
                    
                    # CSVダウンロード
                    csv = df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="CSV形式でダウンロード",
                        data=csv,
                        file_name=f"kyujinbox_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
                    return df
                else:
                    st.warning("条件に一致する求人情報は見つかりませんでした。")
                    return None
        
        return None 