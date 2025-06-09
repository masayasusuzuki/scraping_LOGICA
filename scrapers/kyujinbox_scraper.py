import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import random
import html
import re
import pandas as pd
import json

class KyujinboxScraper:
    """求人ボックスのスクレイパー"""
    
    def __init__(self):
        self.base_url = "https://xn--pckua2a7gp15o89zb.com/"
        self.session = requests.Session()
        self.session.headers.update(self.get_headers())
        
    def get_headers(self):
        """リクエストヘッダーを生成"""
        return {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Referer': 'https://xn--pckua2a7gp15o89zb.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
    
    def get_employment_types(self):
        """求人ボックストップページから雇用形態の選択肢を取得"""
        try:
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            select_element = soup.find('select', {'name': 'employType'})
            
            if not select_element:
                # デフォルトの選択肢を返す
                return [
                    {"text": "正社員", "data_search_word": "正社員"},
                    {"text": "アルバイト・パート", "data_search_word": "バイト"},
                    {"text": "派遣社員", "data_search_word": "派遣"},
                    {"text": "契約社員", "data_search_word": "契約"},
                ]
            
            options = []
            for option in select_element.find_all('option'):
                if option.get('value') and option.get('data-search_word'):
                    options.append({
                        "text": option.text.strip(),
                        "data_search_word": option.get('data-search_word')
                    })
            
            return options if options else [
                {"text": "正社員", "data_search_word": "正社員"},
                {"text": "アルバイト・パート", "data_search_word": "バイト"},
            ]
            
        except Exception as e:
            # エラーが発生した場合はデフォルトの選択肢を返す
            return [
                {"text": "正社員", "data_search_word": "正社員"},
                {"text": "アルバイト・パート", "data_search_word": "バイト"},
                {"text": "派遣社員", "data_search_word": "派遣"},
                {"text": "契約社員", "data_search_word": "契約"},
            ]
    
    def generate_search_url(self, employment_type_word, keyword, area):
        """検索URLを生成"""
        try:
            # 求人ボックスの実際のURL形式に合わせる
            # 例: https://xn--pckua2a7gp15o89zb.com/看護師の仕事-東京都?e=1
            
            # 検索クエリを構築
            url_parts = []
            
            if keyword:
                url_parts.append(f"{keyword}の仕事")
            
            if area:
                # 都道府県名を正規化
                area_normalized = area
                if not area.endswith(('都', '道', '府', '県')):
                    # 都道府県名でない場合は、一般的な地域として扱う
                    if area in ['東京', '大阪', '京都']:
                        area_normalized = area + ('都' if area == '東京' else '府')
                    elif area == '北海道':
                        area_normalized = area
                    else:
                        # その他の場合はそのまま使用
                        area_normalized = area
                url_parts.append(area_normalized)
            
            if not url_parts:
                # キーワードもエリアもない場合は、雇用形態のみ
                if employment_type_word:
                    url_parts.append(f"{employment_type_word}の仕事")
                else:
                    return self.base_url
            
            # URL作成
            path_part = "-".join(url_parts)
            encoded_path = urllib.parse.quote(path_part, safe='-')
            
            # 雇用形態パラメータを追加
            params = []
            if employment_type_word:
                employment_map = {
                    "正社員": "1",
                    "バイト": "2", 
                    "派遣": "3",
                    "契約": "4"
                }
                emp_id = employment_map.get(employment_type_word, "")
                if emp_id:
                    params.append(f"e={emp_id}")
            
            # 最終URL構築
            search_url = f"{self.base_url}{encoded_path}"
            if params:
                search_url += f"?{'&'.join(params)}"
            
            return search_url
            
        except Exception as e:
            return None
    
    def make_request(self, url, max_retries=3, timeout=30):
        """リクエストを送信（リトライ機能付き）"""
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    sleep_time = random.uniform(2, 4)
                    time.sleep(sleep_time)
                else:
                    time.sleep(random.uniform(0.5, 1.5))
                
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                return response, None
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 503 and attempt < max_retries - 1:
                    continue
                return None, f"HTTPエラー: {e.response.status_code} - {e}"
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    continue
                return None, "リクエストがタイムアウトしました"
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    continue
                return None, f"リクエストエラー: {str(e)}"
        
        return None, "最大再試行回数に達しました"
    
    def extract_phone_number(self, text):
        """テキストから電話番号を抽出"""
        if not text:
            return None
        
        # 電話番号のパターン定義
        phone_patterns = [
            # フリーダイヤル・特番
            r'0120[-\s]?\d{3}[-\s]?\d{3}',
            r'0800[-\s]?\d{3}[-\s]?\d{4}',
            r'0570[-\s]?\d{3}[-\s]?\d{3}',
            r'050[-\s]?\d{4}[-\s]?\d{4}',
            
            # 携帯電話
            r'0[987]0[-\s]?\d{4}[-\s]?\d{4}',
            
            # 固定電話
            r'0[3-6][-\s]?\d{4}[-\s]?\d{4}',
            r'0[1-9]\d[-\s]?\d{3,4}[-\s]?\d{4}',
            r'0[1-9]\d{2}[-\s]?\d{2,3}[-\s]?\d{4}',
            
            # キーワード付きパターン
            r'電話[：:\s]*([0-9０-９][0-9０-９\-\(\)\s]{8,13})',
            r'TEL[：:\s]*([0-9０-９][0-9０-９\-\(\)\s]{8,13})',
        ]
        
        for pattern in phone_patterns:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                phone = matches.group(1) if len(matches.groups()) > 0 else matches.group(0)
                
                # 数字のみ抽出して検証
                digits_only = re.sub(r'[^\d]', '', phone)
                
                # 電話番号として有効な桁数かチェック（10桁または11桁）
                if len(digits_only) not in [10, 11]:
                    continue
                
                # 0で始まることを確認
                if not digits_only.startswith('0'):
                    continue
                
                # フォーマット調整
                if digits_only.startswith('0120') and len(digits_only) == 10:
                    return f"{digits_only[:4]}-{digits_only[4:7]}-{digits_only[7:]}"
                elif len(digits_only) == 11:
                    return f"{digits_only[:3]}-{digits_only[3:7]}-{digits_only[7:]}"
                elif len(digits_only) == 10:
                    if digits_only.startswith('03') or digits_only.startswith('06'):
                        return f"{digits_only[:2]}-{digits_only[2:6]}-{digits_only[6:]}"
                    else:
                        return f"{digits_only[:3]}-{digits_only[3:6]}-{digits_only[6:]}"
                
                return phone
        
        return None
    
    def extract_representative(self, text):
        """テキストから代表者名を抽出"""
        if not text:
            return ""
        
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'[\[\]【】［］()（）「」『』≪≫<>＜＞""\'\']+', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        patterns = [
            r'代表者\s*[\n\r:：]*\s*([^\n\r（(【［[{]+)',
            r'代表取締役\s*[\n\r:：]*\s*([^\n\r（(【［[{]+)',
            r'院長\s*[\n\r:：]*\s*([^\n\r:：（(【［[{]+)',
            r'理事長\s*[\n\r:：]*\s*([^\n\r:：（(【［[{]+)',
        ]
        
        for pattern in patterns:
            matches = re.search(pattern, text, re.DOTALL)
            if matches and matches.group(1):
                name = matches.group(1).strip()
                if name and name != "者" and len(name) > 1:
                    name = re.sub(r'所在住所.*$', '', name)
                    name = re.sub(r'住所.*$', '', name)
                    name = re.sub(r'[0-9０-９]{5,}.*$', '', name)
                    name = name.strip()
                    if len(name) > 1:
                        return name
        
        return ""
    
    def search_contact_info_web(self, facility_name, debug_mode=False):
        """Web検索で企業の連絡先情報を取得（強化版）"""
        contact_info = {
            "phone": "",
            "email": "",
            "representative": ""
        }
        
        try:
            if debug_mode:
                st.info(f"🔍 Web検索開始: {facility_name}")
            
            # 複数の検索クエリパターンを試行
            search_patterns = [
                f"{facility_name} 電話番号 TEL",
                f"{facility_name} 連絡先 お問い合わせ",
                f"{facility_name} 会社概要 電話",
                f"{facility_name} 代表 TEL 電話"
            ]
            
            best_phone = ""
            best_email = ""
            best_representative = ""
            
            for idx, search_query in enumerate(search_patterns):
                if debug_mode:
                    st.info(f"🔍 検索パターン {idx+1}: {search_query}")
                
                # Web検索を実行
                result_text = self.perform_web_search(search_query)
                
                if result_text:
                    if debug_mode:
                        st.code(f"検索結果（最初の300文字）: {result_text[:300]}...")
                    
                    # 電話番号を抽出（複数パターン対応）
                    phone = self.extract_phone_number_enhanced(result_text, facility_name, debug_mode)
                    if phone and not best_phone:
                        best_phone = phone
                        if debug_mode:
                            st.success(f"✅ 電話番号発見: {phone}")
                    
                    # メールアドレス抽出
                    email = self.extract_email_enhanced(result_text, facility_name, debug_mode)
                    if email and not best_email:
                        best_email = email
                        if debug_mode:
                            st.success(f"✅ メールアドレス発見: {email}")
                    
                    # 代表者名抽出
                    representative = self.extract_representative_enhanced(result_text, facility_name, debug_mode)
                    if representative and not best_representative:
                        best_representative = representative
                        if debug_mode:
                            st.success(f"✅ 代表者名発見: {representative}")
                    
                    # 十分な情報が集まったら早期終了
                    if best_phone and best_email:
                        break
                
                # レート制限
                time.sleep(1)
            
            contact_info["phone"] = best_phone
            contact_info["email"] = best_email
            contact_info["representative"] = best_representative
            
            if debug_mode:
                st.json({
                    "電話番号": contact_info["phone"] or "見つかりませんでした",
                    "メールアドレス": contact_info["email"] or "見つかりませんでした", 
                    "代表者": contact_info["representative"] or "見つかりませんでした"
                })
            
            return contact_info
            
        except Exception as e:
            if debug_mode:
                st.error(f"🔍 Web検索エラー: {str(e)}")
            return contact_info
    
    def extract_phone_number_enhanced(self, text, facility_name, debug_mode=False):
        """強化された電話番号抽出"""
        # 複数の電話番号パターン
        phone_patterns = [
            # TEL: 形式
            re.compile(r'(?:TEL|Tel|tel|電話|☎)[:：\s]*(\d{2,4}[-‐\s]?\d{2,4}[-‐\s]?\d{4})'),
            # お問い合わせ: 形式
            re.compile(r'(?:お問い合わせ|問い合わせ|連絡先)[:：\s]*(\d{2,4}[-‐\s]?\d{2,4}[-‐\s]?\d{4})'),
            # 代表電話: 形式
            re.compile(r'(?:代表|本社|受付)[:：\s]*(\d{2,4}[-‐\s]?\d{2,4}[-‐\s]?\d{4})'),
            # 一般的な電話番号パターン
            re.compile(r'(\d{2,4}[-‐]\d{2,4}[-‐]\d{4})'),
            # ハイフンなし（10-11桁）
            re.compile(r'(\d{10,11})'),
        ]
        
        best_phone = ""
        
        for pattern in phone_patterns:
            matches = pattern.findall(text)
            for match in matches:
                # 電話番号の妥当性チェック
                clean_phone = re.sub(r'[-‐\s]', '', match)
                
                # 10-11桁であることを確認
                if 10 <= len(clean_phone) <= 11:
                    # 先頭が0で始まることを確認（日本の電話番号）
                    if clean_phone.startswith('0'):
                        # ハイフンで整形
                        if len(clean_phone) == 10:
                            formatted_phone = f"{clean_phone[:3]}-{clean_phone[3:6]}-{clean_phone[6:]}"
                        else:  # 11桁
                            formatted_phone = f"{clean_phone[:3]}-{clean_phone[3:7]}-{clean_phone[7:]}"
                        
                        if debug_mode:
                            st.info(f"📞 電話番号候補: {formatted_phone}")
                        
                        return formatted_phone
        
        return best_phone
    
    def extract_email_enhanced(self, text, facility_name, debug_mode=False):
        """強化されたメールアドレス抽出"""
        # メールアドレスパターン
        email_patterns = [
            # 一般的なメールアドレス
            re.compile(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'),
            # info@形式を優先
            re.compile(r'(info@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'),
            # contact@形式を優先
            re.compile(r'(contact@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'),
        ]
        
        # 除外すべきドメインリスト
        exclude_domains = [
            'google', 'youtube', 'facebook', 'twitter', 'instagram', 
            'linkedin', 'example', 'noreply', 'duckduckgo', 'bing',
            'yahoo', 'gmail', 'hotmail', 'outlook', 'test', 'sample'
        ]
        
        best_email = ""
        
        for pattern in email_patterns:
            matches = pattern.findall(text)
            for email in matches:
                # 除外ドメインチェック
                if not any(domain in email.lower() for domain in exclude_domains):
                    # 画像ファイル等を除外
                    if not any(ext in email.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.css', '.js']):
                        if debug_mode:
                            st.info(f"📧 メールアドレス候補: {email}")
                        return email
        
        return best_email
    
    def extract_representative_enhanced(self, text, facility_name, debug_mode=False):
        """強化された代表者名抽出"""
        # 代表者名パターン
        representative_patterns = [
            re.compile(r'(?:代表取締役|社長|代表者|CEO|会長|理事長|院長|所長|代表)[:：\s]*([^\s\n]{2,10})', re.MULTILINE),
            re.compile(r'([^\s\n]{2,6})\s*(?:代表取締役|社長|CEO)', re.MULTILINE),
            re.compile(r'代表[:：]\s*([^\s\n]{2,10})', re.MULTILINE),
        ]
        
        for pattern in representative_patterns:
            matches = pattern.findall(text)
            for match in matches:
                # 日本語名らしい文字列かチェック
                if len(match) >= 2 and len(match) <= 8:
                    # 数字や記号が含まれていないかチェック
                    if not re.search(r'[0-9\-_@.]', match):
                        if debug_mode:
                            st.info(f"👤 代表者候補: {match}")
                        return match
        
        return ""
    
    def perform_web_search(self, search_term):
        """Web検索を実行する"""
        try:
            import os
            import platform
            
            # クラウド環境検出
            cloud_indicators = [
                'STREAMLIT_CLOUD' in os.environ,
                'STREAMLIT_SHARING_MODE' in os.environ, 
                'HOSTNAME' in os.environ and 'streamlit' in os.environ.get('HOSTNAME', '').lower(),
                platform.node() and 'streamlit' in platform.node().lower(),
                'USER' in os.environ and os.environ.get('USER') == 'appuser',
                'HOME' in os.environ and '/home/appuser' in os.environ.get('HOME', ''),
                'STREAMLIT_SERVER_HEADLESS' in os.environ
            ]
            
            is_cloud_env = any(cloud_indicators)
            
            if is_cloud_env:
                # クラウド環境では検索を無効化
                return ""
            
            # 検索エンジンのリスト
            search_engines = [
                {
                    'name': 'DuckDuckGo',
                    'url': f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(search_term)}",
                },
                {
                    'name': 'Bing',
                    'url': f"https://www.bing.com/search?q={urllib.parse.quote(search_term)}",
                }
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ja,en-US;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            for engine in search_engines:
                try:
                    response = requests.get(engine['url'], headers=headers, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        results = []
                        
                        if 'duckduckgo' in engine['url']:
                            # DuckDuckGo HTML結果の解析
                            result_elements = soup.find_all(['h2', 'span'], class_=lambda x: x and 'result' in str(x))
                            snippet_elements = soup.find_all('a', class_='result__snippet')
                            
                            for elem in result_elements[:3]:
                                text = elem.get_text(strip=True)
                                if text and len(text) > 10:
                                    results.append(text)
                            
                            for elem in snippet_elements[:3]:
                                text = elem.get_text(strip=True)
                                if text and len(text) > 10:
                                    results.append(text)
                        
                        elif 'bing' in engine['url']:
                            # Bing結果の解析
                            result_elements = soup.find_all('h2')
                            snippet_elements = soup.find_all('p')
                            
                            for elem in result_elements[:3]:
                                text = elem.get_text(strip=True)
                                if text and len(text) > 10:
                                    results.append(text)
                            
                            for elem in snippet_elements[:3]:
                                text = elem.get_text(strip=True)
                                if text and len(text) > 20:
                                    results.append(text)
                        
                        if results:
                            return " ".join(results[:5])  # 上位5件まで
                    
                    # 各エンジンの間に少し待機
                    time.sleep(2)
                    
                except requests.exceptions.RequestException:
                    continue
            
            return ""
            
        except Exception:
            return ""
    
    def extract_jobs_from_page(self, soup, page_url, debug_mode=False):
        """検索結果ページからJSON構造化データを使用して求人情報を直接抽出"""
        jobs = []
        
        try:
            if debug_mode:
                st.info("🐛 DEBUG: 検索結果ページからJSON構造化データを抽出中...")
            
            # 求人ボックスの構造化データを含む求人カードを取得
            job_cards = soup.select('section.p-result_card')
            
            if debug_mode:
                st.info(f"🐛 DEBUG: {len(job_cards)} 個の求人カードを発見")
            
            for idx, card in enumerate(job_cards):
                try:
                    # data-func-show-arg属性を持つaタグを探す
                    json_link = card.find('a', {'data-func-show-arg': True})
                    
                    if not json_link:
                        if debug_mode and idx < 3:
                            st.warning(f"🐛 DEBUG: カード {idx+1} でJSON属性が見つかりません")
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
                                'uniqueId': job_data.get('uniqueId')
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
                        unique_id = job_info.get('unique_id', '')
                        if unique_id:
                            job_info['website_url'] = f"{self.base_url}/jb/{unique_id}"
                        else:
                            job_info['website_url'] = ''
                        
                        # 最低限の情報が揃っている場合のみリストに追加
                        if job_info.get('facility_name') and job_info.get('title'):
                            jobs.append(job_info)
                            
                            if debug_mode and idx < 3:
                                st.success(f"🐛 DEBUG: カード {idx+1} 情報抽出完了")
                                st.json({
                                    'facility_name': job_info['facility_name'],
                                    'title': job_info['title'],
                                    'work_area': job_info['work_area'],
                                    'website_url': job_info['website_url'],
                                    'original_url': job_info['original_url'],
                                    'unique_id': job_info['unique_id']
                                })
                        else:
                            if debug_mode and idx < 3:
                                st.warning(f"🐛 DEBUG: カード {idx+1} 必要な情報が不足")
                    
                    except json.JSONDecodeError as e:
                        if debug_mode and idx < 3:
                            st.error(f"🐛 DEBUG: カード {idx+1} JSON解析エラー: {str(e)}")
                        continue
                
                except Exception as e:
                    if debug_mode:
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
            
            # 施設名（会社名）を詳細ページから取得
            facility_patterns = [
                re.compile(r'(?:会社名|法人名|施設名|病院名|クリニック名|事業所名|企業名)[:：]?\s*(.+?)(?:\n|$)', re.MULTILINE),
                re.compile(r'(?:勤務先|運営会社|運営法人)[:：]?\s*(.+?)(?:\n|$)', re.MULTILINE),
            ]
            
            for pattern in facility_patterns:
                facility_matches = pattern.findall(page_text)
                if facility_matches:
                    facility_name = facility_matches[0].strip()[:100]
                    if len(facility_name) > 2:
                        details['facility_name'] = facility_name
                        if debug_mode:
                            st.success(f"🐛 DEBUG: 施設名発見: {facility_name}")
                        break
            
            # 代表者名を詳細ページから取得
            representative = self.extract_representative(page_text)
            if representative:
                details['representative'] = representative
                if debug_mode:
                    st.success(f"🐛 DEBUG: 代表者名発見: {representative}")
            
            # 電話番号の抽出（より包括的）
            phone_patterns = [
                re.compile(r'(?:電話|TEL|Tel|tel)[:：]?\s*(\d{2,4}[-‐\s]?\d{2,4}[-‐\s]?\d{4})'),  # 電話: 形式
                re.compile(r'(\d{2,4}[-‐]\d{2,4}[-‐]\d{4})'),  # 一般的な電話番号
                re.compile(r'(\d{10,11})'),  # ハイフンなし
            ]
            
            for pattern in phone_patterns:
                phone_matches = pattern.findall(page_text)
                if phone_matches:
                    phone = phone_matches[0]
                    details['phone'] = phone
                    if debug_mode:
                        st.success(f"🐛 DEBUG: 電話番号発見: {phone}")
                    break
            
            # メールアドレスの抽出
            email_patterns = [
                re.compile(r'(?:メール|E-mail|Email|email)[:：]?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'),
                re.compile(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'),
            ]
            
            for pattern in email_patterns:
                email_matches = pattern.findall(page_text)
                if email_matches:
                    # .pngや.jpgなどの画像ファイルを除外
                    valid_emails = [em for em in email_matches if not any(ext in em.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.css', '.js'])]
                    if valid_emails:
                        details['email'] = valid_emails[0]
                        if debug_mode:
                            st.success(f"🐛 DEBUG: メールアドレス発見: {valid_emails[0]}")
                        break
            
            # 住所情報を詳細ページから取得
            address_patterns = [
                re.compile(r'(?:住所|所在地|Address)[:：]?\s*(.+?[都道府県].+?[市区町村].+?)(?:\n|<|$)', re.MULTILINE),
                re.compile(r'([東京都|大阪府|京都府|北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県].+?[市区町村].+?)(?:\n|$)', re.MULTILINE),
                re.compile(r'(?:住所|所在地|勤務地)[:：\s]*([^\n\r]+)'),
            ]
            
            for pattern in address_patterns:
                address_matches = pattern.findall(page_text)
                if address_matches:
                    address = address_matches[0].strip()[:200]  # 最大200文字
                    if len(address) > 5:  # 住所として妥当な長さ
                        details['address'] = address
                        if debug_mode:
                            st.success(f"🐛 DEBUG: 住所発見: {address[:50]}...")
                        break
            
            # ウェブサイトURLの抽出（大幅に改善）
            website_patterns = [
                re.compile(r'(?:ホームページ|Website|URL|HP|公式サイト)[:：]?\s*(https?://[^\s\n<>\"\']+)'),
                re.compile(r'(?:詳細は|詳しくは).*(https?://[^\s\n<>\"\']+)'),
                re.compile(r'(https?://(?:www\.)?[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(?:\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})*\.(?:com|co\.jp|jp|org|net|info)/[^\s\n<>\"\']*)', re.IGNORECASE),
                re.compile(r'(https?://(?:www\.)?[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(?:\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})*\.(?:com|co\.jp|jp|org|net|info))', re.IGNORECASE),
            ]
            
            # 除外すべきドメイン（より包括的）
            exclude_domains = [
                'xn--pckua2a7gp15o89zb.com',  # 求人ボックス自体
                'google.com', 'google.co.jp',
                'yahoo.co.jp', 'yahoo.com',
                'youtube.com', 'youtu.be',  # YouTube
                'facebook.com', 'fb.com',
                'twitter.com', 'x.com',
                'instagram.com',
                'linkedin.com',
                'tiktok.com',
                'line.me',
                'amazon.co.jp', 'amazon.com',
                'rakuten.co.jp',
                'mercari.com',
                'indeed.com', 'indeed.co.jp',
                'rikunabi.com', 'mynavi.jp',
                'en-japan.com', 'doda.jp',
                'cookpad.com',
                'wikipedia.org',
                'cloudfront.net',
                'googleapis.com',
                'gstatic.com'
            ]
            
            for pattern in website_patterns:
                website_matches = pattern.findall(page_text)
                if website_matches:
                    # 有効なウェブサイトを抽出
                    valid_websites = []
                    for url in website_matches:
                        # URL正規化
                        clean_url = url.rstrip('.,;:)')
                        
                        # 除外ドメインチェック
                        is_excluded = any(domain in clean_url.lower() for domain in exclude_domains)
                        
                        # 画像ファイルや無効なパスの除外
                        is_invalid_file = any(ext in clean_url.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.css', '.js', '.pdf'])
                        
                        # 有効なURLの場合のみ追加
                        if not is_excluded and not is_invalid_file and len(clean_url) > 10:
                            valid_websites.append(clean_url)
                    
                    if valid_websites:
                        # 最も企業サイトらしいURLを選択
                        best_url = None
                        for url in valid_websites:
                            # co.jp ドメインを優先
                            if '.co.jp' in url.lower():
                                best_url = url
                                break
                            # .jp ドメインを次に優先
                            elif '.jp' in url.lower() and not best_url:
                                best_url = url
                            # その他のドメインは最後
                            elif not best_url:
                                best_url = url
                        
                        if best_url:
                            details['website_url'] = best_url
                            if debug_mode:
                                st.success(f"🐛 DEBUG: ウェブサイトURL発見: {best_url}")
                                if len(valid_websites) > 1:
                                    st.info(f"🐛 DEBUG: 他の候補: {valid_websites[1:]}")
                            break
            
            # 事業内容の抽出
            business_patterns = [
                re.compile(r'(?:事業内容|業務内容|事業概要|Business)[:：]?\s*(.+?)(?:\n\n|\n[A-Z]|\n\d+\.|\n•|\n-|$)', re.MULTILINE | re.DOTALL),
                re.compile(r'(?:業種|事業|Business)[:：]?\s*(.+?)(?:\n|$)', re.MULTILINE),
            ]
            
            for pattern in business_patterns:
                business_matches = pattern.findall(page_text)
                if business_matches:
                    business_content = business_matches[0].strip()[:500]  # 最大500文字
                    if len(business_content) > 10:  # 10文字以上の場合のみ採用
                        details['business_content'] = business_content
                        if debug_mode:
                            st.success(f"🐛 DEBUG: 事業内容発見: {business_content[:50]}...")
                        break
            
            return details, None
            
        except Exception as e:
            error_msg = f"詳細情報取得エラー: {str(e)}"
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
            max_pages = min(10, (max_jobs // 10) + 1)
            
            # 検索結果ページから直接JSON構造化データを抽出
            while page_num <= max_pages and len(all_jobs) < max_jobs:
                # ページネーション対応
                if page_num == 1:
                    current_url = search_url
                else:
                    if "?" in search_url:
                        current_url = search_url + f"&p={page_num}"
                    else:
                        current_url = search_url + f"?p={page_num}"
                
                if debug_mode:
                    st.info(f"🐛 DEBUG: ページ {page_num} へアクセス中: {current_url}")
                
                response, error = self.make_request(current_url)
                if error:
                    if debug_mode:
                        st.error(f"🐛 DEBUG: ページ {page_num} でエラー発生: {error}")
                    if page_num == 1:
                        return None, error
                    else:
                        break
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # JSON構造化データから求人情報を抽出
                jobs = self.extract_jobs_from_page(soup, current_url, debug_mode=debug_mode)
                
                if debug_mode:
                    st.info(f"🐛 DEBUG: ページ {page_num} から {len(jobs)} 件の求人を抽出")
                
                if not jobs:
                    if debug_mode:
                        st.warning(f"🐛 DEBUG: ページ {page_num} で求人が見つかりませんでした")
                    break
                
                # 各求人に対してWeb検索で補完情報を取得
                for idx, job in enumerate(jobs):
                    if len(all_jobs) >= max_jobs:
                        break
                    
                    if progress_callback:
                        progress_callback(len(all_jobs) + 1, max_jobs)
                    
                    if debug_mode and len(all_jobs) < 3:
                        st.info(f"🐛 DEBUG: 求人 {len(all_jobs) + 1} を処理中: {job.get('facility_name', 'Unknown')}")
                    
                    # Web検索で連絡先情報を取得
                    if job.get('facility_name'):
                        if debug_mode and len(all_jobs) < 2:  # 最初の2件のみ詳細なWeb検索ログを表示
                            st.info(f"🔍 施設名 '{job['facility_name']}' のWeb検索を開始...")
                        
                        contact_info = self.search_contact_info_web(
                            job['facility_name'], 
                            debug_mode=(debug_mode and len(all_jobs) < 2)
                        )
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
                    
                    if debug_mode and len(all_jobs) <= 3:
                        st.success(f"🐛 DEBUG: 求人 {len(all_jobs)} 処理完了")
                        st.json({
                            'facility_name': formatted_job['facility_name'],
                            'address': formatted_job['address'],
                            'phone_number': formatted_job['phone_number'],
                            'email': formatted_job['email'],
                            'representative': formatted_job['representative'],
                            'website_url': formatted_job['website_url'],
                            'business_content': formatted_job['business_content'][:100] + '...' if len(formatted_job['business_content']) > 100 else formatted_job['business_content']
                        })
                
                # 次のページへ
                page_num += 1
                time.sleep(1)  # レート制限
            
            if debug_mode:
                st.success(f"🐛 DEBUG: スクレイピング完了 - 最終的に {len(all_jobs)} 件の求人情報を取得")
            
            return all_jobs, None
            
        except Exception as e:
            error_msg = f"スクレイピング中にエラーが発生しました: {str(e)}"
            if debug_mode:
                st.error(f"🐛 DEBUG: {error_msg}")
                st.code(f"例外詳細: {type(e).__name__}: {str(e)}")
            return None, error_msg


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
            [10, 20, 30, 50, 100],
            index=0,  # デフォルトで10件
            key="kyujinbox_max_jobs",
            help="取得する求人の最大件数を選択してください（上限100件）"
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
                job_list, error = self.scraper.scrape_jobs(
                    selected_employment_word, 
                    keyword, 
                    area,
                    max_jobs,
                    progress_callback,
                    debug_mode
                )
                
                # プログレスバーをクリア
                progress_bar.empty()
                status_text.empty()
                
                if error:
                    st.error(error)
                    if debug_mode:
                        st.code(f"エラー詳細: {error}")
                    return None
                
                if not job_list:
                    st.warning("求人情報を取得できませんでした。検索条件を変更してお試しください。")
                    if debug_mode:
                        st.info("🐛 DEBUG: 空の結果が返されました")
                    return None
                
                # データフレームに変換
                df_data = []
                for job in job_list:
                    df_data.append({
                        '施設名': job['facility_name'],
                        '代表者名': job['representative'],
                        '住所': job['address'],
                        'WebサイトURL': job['website_url'],
                        '電話番号': job['phone_number'],
                        'メールアドレス': job['email'],
                        '事業内容': job['business_content']
                    })
                
                df = pd.DataFrame(df_data)
                
                if debug_mode:
                    st.success(f"🐛 DEBUG: データフレーム作成完了 - {len(df)}行, {len(df.columns)}列")
                
                st.success(f"{len(df)}件の求人情報を取得しました。")
                
                return df
        
        else:
            st.info("検索条件を入力して求人を探してください。")
            return None