import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import urljoin

class MedicalConciergeUI:
    """メディカル・コンシェルジュネット専用のUIとスクレイピング機能"""
    
    # 設定定数
    BASE_URL = "https://www.concier.net"
    SEARCH_URL = "https://www.concier.net/jobs/search"
    SEARCH_ENDPOINT = "https://www.concier.net/jobs/search"
    
    # HTTPヘッダー設定
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    def __init__(self):
        """初期化"""
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        
        # セッションステートの初期化
        if 'search_options' not in st.session_state:
            st.session_state.search_options = {}
    
    def get_search_options(self):
        """検索フォームの選択肢を動的に取得"""
        try:
            response = self.session.get(self.SEARCH_URL)
            response.encoding = 'shift_jis'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            options = {}
            
            # 職種の選択肢を取得（radioボタンから）
            job_radios = soup.find_all('input', {'type': 'radio', 'name': 'jobId'})
            if job_radios:
                job_options = []
                for radio in job_radios:
                    value = radio.get('value', '')
                    # ラジオボタンの次のテキストまたは親要素のテキストを取得
                    label_elem = radio.find_parent('label')
                    if label_elem:
                        label_text = label_elem.get_text(strip=True)
                        # 先頭の空白文字を除去
                        label_text = label_text.strip()
                        if value and label_text:
                            job_options.append((value, label_text))
                
                options['職種'] = job_options
            
            # 働き方の選択肢を取得（name属性を修正）
            work_select = soup.find('select', {'name': 'worktypeId'})
            if work_select:
                work_options = [(opt.get('value', ''), opt.get_text(strip=True)) 
                                  for opt in work_select.find_all('option') if opt.get('value')]
                options['働き方'] = work_options
            
            # 都道府県の選択肢を取得
            local_select = soup.find('select', {'name': 'localId'})
            if local_select:
                local_options = [(opt.get('value', ''), opt.get_text(strip=True)) 
                                   for opt in local_select.find_all('option') if opt.get('value')]
                options['都道府県'] = local_options
            
            # 施設区分の選択肢を取得
            facility_select = soup.find('select', {'name': 'facilityId'})
            if facility_select:
                facility_options = [(opt.get('value', ''), opt.get_text(strip=True)) 
                                   for opt in facility_select.find_all('option') if opt.get('value')]
                options['施設区分'] = facility_options
            
            return options
            
        except Exception as e:
            st.error(f"検索オプションの取得に失敗しました: {str(e)}")
            return {}
    
    def render_ui(self):
        """メディカル・コンシェルジュネット専用のUIを表示"""
        st.header("メディカル・コンシェルジュネット：検索条件")
        
        # 検索オプションを取得（キャッシュ）
        if not st.session_state.search_options:
            with st.spinner("検索条件を読み込み中..."):
                st.session_state.search_options = self.get_search_options()
        
        search_options = st.session_state.search_options
        
        if not search_options:
            st.error("検索条件の読み込みに失敗しました。ページを再読み込みしてください。")
            if st.button("検索条件を再読み込み"):
                st.session_state.search_options = {}
                st.rerun()
            return None
        
        # 検索条件入力部（2カラムレイアウト）
        col1, col2 = st.columns(2)
        
        with col1:
            # 職種
            job_options = search_options.get('職種', [])
            if job_options:
                job_labels = [label for value, label in job_options]
                job_values = [value for value, label in job_options]
                
                selected_job_label = st.selectbox(
                    "職種",
                    job_labels,
                    index=0
                )
                # ラベルから対応する値を取得
                selected_job_index = job_labels.index(selected_job_label)
                selected_job = job_values[selected_job_index]
            else:
                st.error("職種の選択肢を取得できませんでした")
                selected_job = ""
            
            # 働き方
            work_options = search_options.get('働き方', [])
            if work_options:
                work_labels = [label for value, label in work_options]
                work_values = [value for value, label in work_options]
                
                selected_work_label = st.selectbox(
                    "働き方",
                    work_labels,
                    index=0
                )
                # ラベルから対応する値を取得
                selected_work_index = work_labels.index(selected_work_label)
                selected_work = work_values[selected_work_index]
            else:
                st.error("働き方の選択肢を取得できませんでした")
                selected_work = ""
        
        with col2:
            # 都道府県
            local_options = search_options.get('都道府県', [])
            if local_options:
                local_labels = [label for value, label in local_options]
                local_values = [value for value, label in local_options]
                
                selected_local_label = st.selectbox(
                    "都道府県",
                    local_labels,
                    index=0
                )
                # ラベルから対応する値を取得
                selected_local_index = local_labels.index(selected_local_label)
                selected_local = local_values[selected_local_index]
            else:
                st.error("都道府県の選択肢を取得できませんでした")
                selected_local = ""
            
            # 施設区分
            facility_options = search_options.get('施設区分', [])
            if facility_options:
                facility_labels = [label for value, label in facility_options]
                facility_values = [value for value, label in facility_options]
                
                selected_facility_label = st.selectbox(
                    "施設区分",
                    facility_labels,
                    index=0
                )
                # ラベルから対応する値を取得
                selected_facility_index = facility_labels.index(selected_facility_label)
                selected_facility = facility_values[selected_facility_index]
            else:
                st.error("施設区分の選択肢を取得できませんでした")
                selected_facility = ""
        
        # フリーワード入力部
        freeword = st.text_input("フリーワード", placeholder="キーワードを入力してください（任意）")
        
        # 実行部
        if st.button("この条件で検索する", type="primary"):
            search_params = {
                'jobId': selected_job,
                'worktypeId': selected_work,
                'localId': selected_local,
                'facilityId': selected_facility,
                'freeword': freeword
            }
            
            with st.spinner("求人情報を取得中... しばらくお待ちください"):
                results = self.scrape_jobs(search_params)
                return results
        
        return None
    
    def scrape_jobs(self, search_params):
        """求人情報をスクレイピング"""
        try:
            all_jobs = []
            page_num = 1
            
            # 初回検索（POST）
            response = self.session.post(self.SEARCH_ENDPOINT, data=search_params)
            response.encoding = 'shift_jis'
            
            if response.status_code != 200:
                return {"error": f"検索リクエストに失敗しました（ステータスコード: {response.status_code}）"}
            
            while True:
                st.info(f"ページ {page_num} を処理中...")
                
                soup = BeautifulSoup(response.text, 'html.parser')
                jobs = self.extract_jobs_from_page(soup)
                
                if not jobs:
                    break
                
                all_jobs.extend(jobs)
                st.info(f"ページ {page_num}: {len(jobs)}件の求人を取得")
                
                # 次ページのリンクを探す
                next_link = self.find_next_page_link(soup)
                if not next_link:
                    break
                
                # 次ページへアクセス
                time.sleep(2)  # サーバーへの配慮
                next_url = urljoin(self.BASE_URL, next_link)
                response = self.session.get(next_url)
                response.encoding = 'shift_jis'
                
                if response.status_code != 200:
                    break
                
                page_num += 1
                
                # 無限ループ防止
                if page_num > 50:
                    st.warning("ページ数が50を超えました。処理を停止します。")
                    break
            
            if all_jobs:
                df = pd.DataFrame(all_jobs)
                return df
            else:
                return pd.DataFrame()  # 空のDataFrame
                
        except requests.exceptions.RequestException as e:
            return {"error": f"ネットワークエラーが発生しました: {str(e)}"}
        except Exception as e:
            return {"error": f"予期しないエラーが発生しました: {str(e)}"}
    
    def get_job_details(self, detail_url):
        """詳細ページから追加情報を取得"""
        try:
            time.sleep(3)  # サーバーへの配慮（詳細ページアクセス時は少し長めに）
            response = self.session.get(detail_url)
            response.encoding = 'shift_jis'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            details = {
                '施設名': '',
                '代表者名': '',
                '所在地': '',
                '電話番号': '',
                'メールアドレス': '',
                '業務内容': ''
            }
            
            # テーブルから情報を抽出
            table = soup.find('table', class_='job-dtl-cont')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    th_elem = row.find('th')
                    td_elem = row.find('td')
                    
                    if th_elem and td_elem:
                        key = th_elem.get_text(strip=True)
                        value = td_elem.get_text(strip=True)
                        
                        # 各項目を抽出
                        if '勤務地' in key:
                            details['所在地'] = value
                        elif '施設' in key:
                            details['施設名'] = value
                        elif '業務詳細' in key:
                            # 改行や特殊文字を整理
                            details['業務内容'] = value.replace('\n', ' ').replace('\r', '').strip()
            
            # 担当者情報から電話番号を抽出（会社の電話番号として）
            contact_info = soup.find('dd', class_='clearfix')
            if contact_info:
                contact_text = contact_info.get_text()
                # 電話番号のパターンを探す
                import re
                phone_pattern = r'(\d{4}-\d{2}-\d{4}|\d{3}-\d{4}-\d{4})'
                phone_match = re.search(phone_pattern, contact_text)
                if phone_match:
                    details['電話番号'] = phone_match.group(1) + '（紹介会社）'
            
            return details
            
        except Exception as e:
            # エラーが発生した場合は空の値を返す
            return {
                '施設名': '',
                '代表者名': '',
                '所在地': '',
                '電話番号': '',
                'メールアドレス': '',
                '業務内容': ''
            }
    
    def extract_jobs_from_page(self, soup):
        """1ページ分の求人情報を抽出"""
        jobs = []
        
        # 求人ブロックを取得
        job_blocks = soup.find_all('div', class_='job-dtl-itm')
        
        for block in job_blocks:
            try:
                job_data = {}
                
                # 求人No
                no_elem = block.find('div', class_='job-dtl-no')
                if no_elem:
                    p_elem = no_elem.find('p')
                    job_data['求人No'] = p_elem.get_text(strip=True) if p_elem else ""
                else:
                    job_data['求人No'] = ""
                
                # タイトル
                title_elem = block.find('div', class_='job-dtl-ttl')
                if title_elem:
                    h3_elem = title_elem.find('h3')
                    job_data['タイトル'] = h3_elem.get_text(strip=True) if h3_elem else ""
                else:
                    job_data['タイトル'] = ""
                
                # 詳細ページURL
                btn_elem = block.find('div', class_='job-dtl-btn')
                if btn_elem:
                    a_elem = btn_elem.find('a', class_='btn')
                    if a_elem and a_elem.get('href'):
                        detail_url = urljoin(self.BASE_URL, a_elem.get('href'))
                        job_data['詳細ページURL'] = detail_url
                        
                        # 詳細ページから追加情報を取得
                        st.info(f"詳細情報を取得中: {job_data['求人No']}")
                        additional_details = self.get_job_details(detail_url)
                        job_data.update(additional_details)
                    else:
                        job_data['詳細ページURL'] = ""
                        # 詳細ページがない場合は空の値を設定
                        job_data.update({
                            '施設名': '',
                            '代表者名': '',
                            '所在地': '',
                            '電話番号': '',
                            'メールアドレス': '',
                            '業務内容': ''
                        })
                else:
                    job_data['詳細ページURL'] = ""
                    job_data.update({
                        '施設名': '',
                        '代表者名': '',
                        '所在地': '',
                        '電話番号': '',
                        'メールアドレス': '',
                        '業務内容': ''
                    })
                
                # テーブルデータの抽出
                table_elem = block.find('table', class_='job-dtl-cont')
                if table_elem:
                    table_data = self.extract_table_data(table_elem)
                    job_data.update(table_data)
                
                # 基本フィールドの初期化（取得できなかった場合）
                default_fields = ['職種', '勤務地', '施設', '業務 (働き方)', '給与', '交通']
                for field in default_fields:
                    if field not in job_data:
                        job_data[field] = ""
                
                # 情報源サイト名
                job_data['情報源サイト名'] = "メディカル・コンシェルジュネット"
                
                jobs.append(job_data)
                
            except Exception as e:
                st.warning(f"個別求人の抽出でエラーが発生しました: {str(e)}")
                continue
        
        return jobs
    
    def extract_table_data(self, table_elem):
        """テーブルからデータを抽出"""
        table_data = {}
        
        rows = table_elem.find_all('tr')
        for row in rows:
            try:
                th_elem = row.find('th')
                td_elem = row.find('td')
                
                if th_elem and td_elem:
                    key = th_elem.get_text(strip=True)
                    value = td_elem.get_text(strip=True)
                    
                    # キーの正規化
                    if '職種' in key:
                        table_data['職種'] = value
                    elif '勤務地' in key:
                        table_data['勤務地'] = value
                    elif '施設' in key:
                        table_data['施設'] = value
                    elif '業務' in key or '働き方' in key:
                        table_data['業務 (働き方)'] = value
                    elif '給与' in key or '時給' in key or '月給' in key:
                        table_data['給与'] = value
                    elif '交通' in key or 'アクセス' in key:
                        table_data['交通'] = value
                    else:
                        # その他のフィールドもそのまま保存
                        table_data[key] = value
            
            except Exception as e:
                continue
        
        return table_data
    
    def find_next_page_link(self, soup):
        """次ページのリンクを探す"""
        try:
            # ページネーション部分を探す
            pagination = soup.find('div', class_='pagination') or soup.find('div', class_='pager')
            
            if pagination:
                # 「次へ」や「＞」などのテキストを持つリンクを探す
                next_links = pagination.find_all('a')
                for link in next_links:
                    text = link.get_text(strip=True)
                    if any(keyword in text for keyword in ['次', '＞', 'next', 'Next', '>']):
                        return link.get('href')
            
            # ページ番号リンクで次のページを探す
            current_page_num = self.get_current_page_number(soup)
            if current_page_num:
                next_page_num = current_page_num + 1
                page_links = soup.find_all('a', href=re.compile(r'page~\d+'))
                for link in page_links:
                    if f'page~{next_page_num}' in link.get('href', ''):
                        return link.get('href')
            
            return None
            
        except Exception as e:
            return None
    
    def get_current_page_number(self, soup):
        """現在のページ番号を取得"""
        try:
            # URLパラメータやページ情報から現在のページ番号を推測
            pagination = soup.find('div', class_='pagination') or soup.find('div', class_='pager')
            if pagination:
                current = pagination.find('span', class_='current') or pagination.find('strong')
                if current:
                    text = current.get_text(strip=True)
                    match = re.search(r'\d+', text)
                    if match:
                        return int(match.group())
            return 1
        except:
            return 1 