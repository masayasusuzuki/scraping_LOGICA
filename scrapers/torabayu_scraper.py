import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import random
import html
import re
import pandas as pd

class TorabayuScraper:
    """とらばーゆ求人サイトのスクレイパー（地域対応）"""
    
    def __init__(self, region="tokyo"):
        self.region = region
        self.region_urls = {
            "tokyo": "https://toranet.jp/prefectures/tokyo/",
            "kanagawa": "https://toranet.jp/prefectures/kanagawa/",
            "chiba": "https://toranet.jp/prefectures/chiba/",
            "saitama": "https://toranet.jp/prefectures/saitama/"
        }
        self.base_url = self.region_urls.get(region, self.region_urls["tokyo"])
        self.session = requests.Session()
        self.session.headers.update(self.get_headers())
        
    def get_headers(self):
        """リクエストヘッダーを生成"""
        return {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Referer': 'https://toranet.jp/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
    
    def is_valid_job_url(self, url):
        """有効な求人URLかチェック"""
        if not url:
            return False
        
        invalid_paths = ['favorite_jobs', 'login', 'register', 'contact', 'about']
        for path in invalid_paths:
            if path in url:
                return False
        
        valid = (
            ('toranet.jp' in url and ('job' in url or 'kyujin' in url or 'prefectures' in url)) or
            ('job_detail' in url)
        )
        
        return valid
    
    def make_request(self, url, max_retries=5, timeout=30):
        """リクエストを送信（リトライ機能付き）"""
        if not self.is_valid_job_url(url):
            return None, f"無効なURL: {url}"
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    sleep_time = random.uniform(3, 7)
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
        """テキストから電話番号を抽出（郵便番号との誤認識を防止）"""
        if not text:
            return None
        
        # 郵便番号パターンを事前に除外
        # 7桁の数字（123-4567形式）や〒マーク付近の数字は除外
        postal_patterns = [
            r'〒\s*\d{3}[-\s]?\d{4}',
            r'郵便番号[：:\s]*\d{3}[-\s]?\d{4}',
            r'^\d{3}-\d{4}$',  # 単体で存在する7桁番号
        ]
        
        # 電話番号の厳密なパターン定義
        phone_patterns = [
            # フリーダイヤル・特番（0120, 0800, 0570, 050, 0180）
            r'0120[-\s]?\d{3}[-\s]?\d{3}',
            r'0800[-\s]?\d{3}[-\s]?\d{4}',
            r'0570[-\s]?\d{3}[-\s]?\d{3}',
            r'050[-\s]?\d{4}[-\s]?\d{4}',
            r'0180[-\s]?\d{3}[-\s]?\d{3}',
            
            # 携帯電話（090, 080, 070, 060, 020）
            r'0[987206]0[-\s]?\d{4}[-\s]?\d{4}',
            
            # 固定電話（2桁市外局番：03, 06など）
            r'0[3-6][-\s]?\d{4}[-\s]?\d{4}',
            
            # 固定電話（3桁市外局番：011, 045, 052など）
            r'0[1-9]\d[-\s]?\d{3,4}[-\s]?\d{4}',
            
            # 固定電話（4桁市外局番：地方番号）
            r'0[1-9]\d{2}[-\s]?\d{2,3}[-\s]?\d{4}',
            
            # キーワード付きパターン（より厳密）
            r'電話番号[：:\s]*([0-9０-９][0-9０-９\-\(\)\s]{8,13})',
            r'TEL[：:\s]*([0-9０-９][0-9０-９\-\(\)\s]{8,13})',
            r'Tel[：:\s]*([0-9０-９][0-9０-９\-\(\)\s]{8,13})',
            r'電話[：:\s]*([0-9０-９][0-9０-９\-\(\)\s]{8,13})',
        ]
        
        # まず郵便番号をチェックして除外
        for postal_pattern in postal_patterns:
            if re.search(postal_pattern, text):
                # 郵便番号が含まれている場合は、その部分を除外して処理
                text = re.sub(postal_pattern, '', text)
        
        # 電話番号を抽出
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
                
                # 郵便番号形式（7桁）を除外
                if len(digits_only) == 7:
                    continue
                
                # フォーマット調整
                if digits_only.startswith('0120') and len(digits_only) == 10:
                    return f"{digits_only[:4]}-{digits_only[4:7]}-{digits_only[7:]}"
                elif len(digits_only) == 11:
                    # 携帯電話形式
                    return f"{digits_only[:3]}-{digits_only[3:7]}-{digits_only[7:]}"
                elif len(digits_only) == 10:
                    # 固定電話形式
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
    
    def extract_address(self, text):
        """テキストから住所を抽出"""
        if not text:
            return ""
        
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        patterns = [
            r'勤務地\s*[\n\r:：]*\s*([^\n\r]{5,100})',
            r'所在住所\s*[\n\r:：]*\s*([^\n\r]{5,100})',
            r'所在地\s*[\n\r:：]*\s*([^\n\r]{5,100})',
            r'〒\d{3}-\d{4}\s*([^\n\r]{5,100})',
        ]
        
        for pattern in patterns:
            matches = re.search(pattern, text, re.DOTALL)
            if matches and matches.group(1):
                address = matches.group(1).strip()
                address = re.sub(r'\s+', ' ', address)
                return address
        
        return ""
    
    def clean_facility_name(self, name):
        """施設名をクリーニング"""
        if not name:
            return "情報なし"
        
        # 不要なテキストを削除
        name = re.sub(r'の求人詳細$', '', name)
        name = re.sub(r'の求人情報$', '', name)
        name = re.sub(r'の求人$', '', name)
        name = re.sub(r'詳細$', '', name)
        name = re.sub(r'【.*?】', '', name)
        name = re.sub(r'「.*?」', '', name)
        name = re.sub(r'\(.*?\)', '', name)
        name = re.sub(r'（.*?）', '', name)
        name = re.sub(r'とらばーゆ', '', name)
        
        # 職種名を削除
        job_patterns = [
            '看護師', '介護士', '医師', '薬剤師', '保育士', '栄養士', 
            '正社員', 'パート', 'アルバイト', '契約社員', '派遣'
        ]
        for pattern in job_patterns:
            name = re.sub(f'{pattern}(募集)?$', '', name)
            name = re.sub(f'^{pattern}', '', name)
        
        name = re.sub(r'\s+', ' ', name).strip()
        name = re.sub(r'^[、,.:：・]+', '', name)
        name = re.sub(r'[、,.:：・]+$', '', name)
        
        return name.strip()
    
    def find_all_job_links(self, soup, search_url, max_jobs):
        """求人リンクを全て取得"""
        all_links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            if not href:
                continue
                
            if not href.startswith('http'):
                if href.startswith('/'):
                    href = f"https://toranet.jp{href}"
                else:
                    href = f"https://toranet.jp/{href}"
            
            if self.is_valid_job_url(href):
                text = a_tag.get_text().strip()
                all_links.append({
                    'href': href,
                    'text': text,
                    'contains_detail_text': '詳細' in text or 'detail' in href.lower() or '求人' in text
                })
        
        # 詳細リンクを優先
        detail_links = [link for link in all_links if link['contains_detail_text']]
        pattern_links = [link for link in all_links if re.search(r'job.*detail|kyujin|recruit', link['href'])]
        
        combined_links = []
        seen_urls = set()
        
        for link in detail_links + pattern_links:
            if link['href'] not in seen_urls:
                combined_links.append(link)
                seen_urls.add(link['href'])
        
        for link in all_links:
            if link['href'] not in seen_urls and search_url not in link['href'] and 'toranet.jp' in link['href']:
                combined_links.append(link)
                seen_urls.add(link['href'])
        
        return [link['href'] for link in combined_links][:max_jobs]
    
    def get_job_listings(self, keyword, specific_area=None, max_jobs=10):
        """求人一覧を取得（地域対応）"""
        encoded_keyword = urllib.parse.quote(keyword)
        
        # 地域ごとのベースURL構築
        if specific_area and specific_area != "全域":
            # 特定地域が選択された場合は、その地域で検索
            area_encoded = urllib.parse.quote(specific_area)
            base_search_url = f"{self.base_url}job_search/kw/{encoded_keyword}/area/{area_encoded}"
        else:
            # 全域または地域未選択の場合
            base_search_url = f"{self.base_url}job_search/kw/{encoded_keyword}"
        
        all_job_links = []
        current_page = 1
        max_pages = 10
        
        while len(all_job_links) < max_jobs and current_page <= max_pages:
            if current_page == 1:
                search_url = base_search_url
            else:
                search_url = f"{base_search_url}/page/{current_page}"
            
            response, error = self.make_request(search_url)
            if error:
                if current_page > 1:
                    break
                else:
                    return None, error, search_url
            
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                page_job_links = self.find_all_job_links(soup, search_url, max_jobs)
                
                if not page_job_links:
                    if current_page == 1:
                        # 検索ページ自体が求人詳細かチェック
                        if any(tag.name in ['h1', 'h2'] and ('求人情報' in tag.text or '仕事内容' in tag.text) 
                               for tag in soup.find_all(['h1', 'h2'])):
                            return [search_url], None, search_url
                        return None, "求人リンクが見つかりませんでした", search_url
                    else:
                        break
                
                existing_links = set(all_job_links)
                for link in page_job_links:
                    if link not in existing_links and len(all_job_links) < max_jobs:
                        all_job_links.append(link)
                        existing_links.add(link)
                
                current_page += 1
                
                if len(all_job_links) >= max_jobs:
                    break
                    
                time.sleep(random.uniform(1.0, 3.0))
                
            except Exception as e:
                if current_page == 1:
                    return None, f"パース中にエラーが発生しました: {str(e)}", search_url
                else:
                    break
        
        return all_job_links, None, base_search_url
    
    def get_job_details(self, detail_url):
        """求人詳細情報を取得"""
        if not self.is_valid_job_url(detail_url):
            return None, f"無効な詳細ページURL: {detail_url}"
        
        time.sleep(random.uniform(0.3, 1.0))
        
        response, error = self.make_request(detail_url)
        if error:
            return None, error
        
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 施設名抽出
            facility_name = "情報なし"
            facility_name_selectors = [
                'div.corpNameWrap > span', 
                'div.corpName', 
                'h1.company-name',
                'div.company-name',
                'h1', 'h2',
                'div.corpInfo',
                'span.name',
                '.corp-name',
                '.company'
            ]
            
            for selector in facility_name_selectors:
                facility_name_element = soup.select_one(selector)
                if facility_name_element:
                    facility_name = self.clean_facility_name(facility_name_element.text.strip())
                    break
            
            # タイトルからの抽出（フォールバック）
            if facility_name == "情報なし":
                title_tag = soup.find('title')
                if title_tag:
                    title_text = title_tag.text.strip()
                    for separator in ['|', '-', '：', ':', '／', '/']: 
                        if separator in title_text:
                            parts = title_text.split(separator)
                            for part in parts:
                                part = part.strip()
                                if 5 < len(part) < 50 and not re.search(r'求人|募集|採用|とらばーゆ|転職', part):
                                    facility_name = self.clean_facility_name(part)
                                    break
                            if facility_name != "情報なし":
                                break
            
            # 代表者抽出
            representative = ""
            representative_elements = soup.select('p.styles_content__HWIR6')
            for element in representative_elements:
                prev_el = element.find_previous()
                if prev_el and prev_el.name == 'h3' and '代表者' in prev_el.text:
                    content = element.text.strip()
                    if content and content != "者" and len(content) > 1:
                        representative = content
                        break
            
            if not representative:
                page_text = soup.get_text()
                representative = self.extract_representative(page_text)
            
            # 勤務地抽出
            location = ""
            location_elements = soup.select('p.styles_content__HWIR6')
            for element in location_elements:
                prev_el = element.find_previous()
                if prev_el and prev_el.name == 'h3' and '勤務地' in prev_el.text:
                    content = element.text.strip()
                    if content and len(content) > 5:
                        location = content
                        break
            
            if not location:
                page_text = soup.get_text()
                location = self.extract_address(page_text)
            
            # 電話番号抽出
            phone_number = "情報なし"
            phone_elements = soup.select('p.styles_content__HWIR6')
            for element in phone_elements:
                prev_el = element.find_previous()
                if prev_el and prev_el.name == 'h3' and ('代表電話番号' in prev_el.text or '電話番号' in prev_el.text):
                    content = element.text.strip()
                    if content:
                        digits = re.sub(r'[^\d]', '', content)
                        if digits and len(digits) >= 10:
                            if digits.startswith('0120'):
                                phone_number = f"{digits[:4]}-{digits[4:7]}-{digits[7:10]}"
                            elif len(digits) == 10:
                                phone_number = f"{digits[:2]}-{digits[2:6]}-{digits[6:10]}"
                            elif len(digits) == 11:
                                phone_number = f"{digits[:3]}-{digits[3:7]}-{digits[7:11]}"
                            else:
                                phone_number = digits
                        break
            
            if phone_number == "情報なし":
                page_text = soup.get_text()
                extracted_number = self.extract_phone_number(page_text)
                if extracted_number:
                    phone_number = extracted_number
            
            # 業務内容抽出
            job_description = "情報なし"
            job_sections = soup.find_all('h3', string=lambda s: s and ('職種/仕事内容' in s or '仕事内容' in s))
            for section in job_sections:
                parent_th = section.find_parent('th')
                if parent_th:
                    td = parent_th.find_next_sibling('td')
                    if td:
                        job_description = td.text.strip()
                        break
            
            if job_description == "情報なし":
                job_content_elements = soup.select('td.styles_content__cGhMI.styles_commonContent__NDgRD.styles_recruitCol__rbAHs')
                for element in job_content_elements:
                    prev_th = element.find_previous('th')
                    if prev_th and prev_th.find('p') and ('職種/仕事内容' in prev_th.text or '仕事内容' in prev_th.text):
                        job_description = element.text.strip()
                        break
            
            # 住所のクリーニング
            if location and facility_name and facility_name != "情報なし" and facility_name in location:
                parts = location.split(facility_name)
                if len(parts) > 1:
                    location = parts[1].strip()
                    location = re.sub(r'^[、,:：\s]+', '', location)
            
            location = re.sub(r'^勤務地[：:]\s*', '', location)
            location = re.sub(r'代表電話.*$', '', location)
            location = re.sub(r'事業内容.*$', '', location)
            location = location.strip()
            
            # 代表者のクリーニング
            if representative:
                representative = re.sub(r'所在住所.*$', '', representative)
                representative = re.sub(r'住所.*$', '', representative)
                representative = re.sub(r'[0-9０-９]{5,}.*$', '', representative)
                representative = re.sub(r'東京都.*$', '', representative)
                representative = re.sub(r'代表電話.*$', '', representative)
                representative = representative.strip()
            
            short_description = job_description[:100] + "..." if len(job_description) > 100 else job_description
            
            return {
                "facility_name": facility_name,
                "representative": representative,
                "location": location,
                "phone_number": phone_number,
                "job_description": job_description,
                "short_description": short_description,
                "source_url": detail_url
            }, None
            
        except Exception as e:
            return None, f"詳細情報の解析中にエラーが発生しました: {str(e)}"
    
    def scrape_jobs(self, keyword, specific_area=None, max_jobs=10, progress_callback=None):
        """求人情報をスクレイピング（地域対応）"""
        try:
            # 求人リンク取得
            job_links, error, search_url = self.get_job_listings(keyword, specific_area, max_jobs)
            
            if error:
                return None, error
            
            if not job_links:
                return None, "求人が見つかりませんでした"
            
            job_list = []
            total_jobs = len(job_links)
            error_count = 0
            error_limit = min(total_jobs // 2, 50)
            
            for idx, link in enumerate(job_links):
                if progress_callback:
                    progress_callback(idx + 1, total_jobs)
                
                job_details, error = self.get_job_details(link)
                
                if error:
                    error_count += 1
                    if error_count >= error_limit:
                        break
                elif job_details:
                    job_list.append(job_details)
            
            return job_list, None
            
        except Exception as e:
            return None, f"スクレイピング中にエラーが発生しました: {str(e)}"


class TorabayuUI:
    """とらばーゆスクレイパーのUI（地域対応）"""
    
    def __init__(self, region="tokyo"):
        self.region = region
        self.region_names = {
            "tokyo": "東京",
            "kanagawa": "神奈川", 
            "chiba": "千葉",
            "saitama": "埼玉"
        }
        self.scraper = TorabayuScraper(region)
        
        # 地域ごとの主要エリア
        self.area_options = {
            "tokyo": ["全域", "23区", "23区外", "新宿区", "渋谷区", "港区", "中央区", "千代田区", "豊島区", "文京区", "台東区", "品川区", "大田区", "世田谷区", "目黒区"],
            "kanagawa": ["全域", "横浜市", "川崎市", "相模原市", "神奈川県央/北部", "横須賀/三浦", "湘南/西湘"],
            "chiba": ["全域", "千葉市", "船橋市", "松戸市", "市川市", "柏市", "市原市", "八千代市", "流山市", "浦安市"],
            "saitama": ["全域", "さいたま市", "川口市", "川越市", "所沢市", "越谷市", "草加市", "春日部市", "熊谷市", "上尾市"]
        }
    
    def render_ui(self):
        """UIを描画して結果を返す"""
        region_name = self.region_names.get(self.region, self.region)
        st.header(f"とらばーゆ {region_name}：検索条件")
        
        # デバッグモード
        debug_mode = st.sidebar.checkbox("デバッグモード", key=f"torabayu_{self.region}_debug")
        
        # 検索キーワード
        search_keyword = st.text_input(
            "職種名や施設名を入力してください", 
            placeholder="看護師など",
            key=f"torabayu_{self.region}_keyword"
        )
        
        # 取得件数設定
        max_jobs = st.selectbox(
            "取得件数を選択",
            [10, 20, 50, 100, 200, 300],
            index=0,  # デフォルトで10件
            key=f"torabayu_{self.region}_max_jobs",
            help="取得する求人の最大件数を選択してください"
        )
        
        # 実行部
        start_button = st.button("求人を探す", type="primary", key=f"torabayu_{self.region}_start")
        
        # 検索実行
        if search_keyword and start_button:
            with st.spinner("求人情報を取得中... しばらくお待ちください"):
                # プログレスバー
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def progress_callback(current, total):
                    progress_bar.progress(current / total)
                    status_text.text(f"求人情報を取得中... ({current}/{total})")
                
                # 地域指定は削除されたのでNoneを渡す
                job_list, error = self.scraper.scrape_jobs(search_keyword, None, max_jobs, progress_callback)
                
                # プログレスバーをクリア
                progress_bar.empty()
                status_text.empty()
                
                if error:
                    st.error(error)
                    return None
                
                if not job_list:
                    st.warning("求人情報を取得できませんでした。")
                    return None
                
                # データフレームに変換
                df_data = []
                for job in job_list:
                    df_data.append({
                        '施設名': job['facility_name'],
                        '代表者名': job['representative'] if job['representative'] else '',
                        '勤務地': job['location'] if job['location'] else '',
                        '求人URL': job['source_url'],
                        '電話番号': job['phone_number'] if job['phone_number'] != "情報なし" else '',
                        'メールアドレス': '',  # 現在未実装
                        '業務内容': job['short_description']
                    })
                
                df = pd.DataFrame(df_data)
                
                return df
        
        else:
            if not search_keyword:
                st.info("職種名や施設名を入力して求人を探してください。")
            return None
    
