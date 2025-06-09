import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import urljoin, urlencode

class BiyouNurseUI:
    """美容ナース.com専用のUIとスクレイピング機能"""
    
    # 設定定数
    BASE_URL = "https://biyou-nurse.com"
    SEARCH_URL = "https://biyou-nurse.com/job/"
    
    # HTTPヘッダー設定
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    def __init__(self):
        """初期化"""
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        
        # セッションステートの初期化
        if 'biyou_search_options' not in st.session_state:
            st.session_state.biyou_search_options = {}
    
    def get_search_options(self):
        """検索フォームの選択肢を動的に取得"""
        try:
            response = self.session.get(self.BASE_URL)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            options = {}
            
            # 都道府県の選択肢を取得
            prefecture_select = soup.find('select', {'name': 'ken_cd'})
            if prefecture_select:
                prefecture_options = [(opt.get('value', ''), opt.get_text(strip=True)) 
                                    for opt in prefecture_select.find_all('option') if opt.get('value')]
                options['都道府県'] = prefecture_options
            else:
                # HTMLで見つからない場合はハードコードされた選択肢を使用
                options['都道府県'] = [
                    ('13', '東京都'), ('14', '神奈川県'), ('11', '埼玉県'), ('12', '千葉県'),
                    ('23', '愛知県'), ('27', '大阪府'), ('26', '京都府'), ('28', '兵庫県'),
                    ('40', '福岡県'), ('01', '北海道'), ('02', '青森県'), ('03', '岩手県'),
                    ('04', '宮城県'), ('05', '秋田県'), ('06', '山形県'), ('07', '福島県'),
                    ('08', '茨城県'), ('09', '栃木県'), ('10', '群馬県'), ('15', '新潟県'),
                    ('16', '富山県'), ('17', '石川県'), ('18', '福井県'), ('19', '山梨県'),
                    ('20', '長野県'), ('21', '岐阜県'), ('22', '静岡県'), ('24', '三重県'),
                    ('25', '滋賀県'), ('29', '奈良県'), ('30', '和歌山県'), ('31', '鳥取県'),
                    ('32', '島根県'), ('33', '岡山県'), ('34', '広島県'), ('35', '山口県'),
                    ('36', '徳島県'), ('37', '香川県'), ('38', '愛媛県'), ('39', '高知県'),
                    ('41', '佐賀県'), ('42', '長崎県'), ('43', '熊本県'), ('44', '大分県'),
                    ('45', '宮崎県'), ('46', '鹿児島県'), ('47', '沖縄県')
                ]
            
            # 資格の選択肢（実際のサイトから）
            options['資格'] = [('1', '正看護師'), ('0', '准看護師')]
            
            return options
            
        except Exception as e:
            st.error(f"検索オプションの取得に失敗しました: {str(e)}")
            # エラー時もデフォルト値を返す
            return {
                '都道府県': [
                    ('13', '東京都'), ('14', '神奈川県'), ('11', '埼玉県'), ('12', '千葉県'),
                    ('23', '愛知県'), ('27', '大阪府'), ('26', '京都府'), ('28', '兵庫県'),
                    ('40', '福岡県')
                ],
                '資格': [('1', '正看護師'), ('0', '准看護師')]
            }
    
    def render_ui(self):
        """美容ナース.com専用のUIを表示"""
        st.header("美容ナース.com：検索条件")
        
        # デバッグモード
        debug_mode = st.sidebar.checkbox("デバッグモード", key="biyou_debug")
        
        # 検索オプションを取得（キャッシュ）
        if not st.session_state.biyou_search_options:
            with st.spinner("検索条件を読み込み中..."):
                st.session_state.biyou_search_options = self.get_search_options()
        
        search_options = st.session_state.biyou_search_options
        
        if not search_options:
            st.error("検索条件の読み込みに失敗しました。ページを再読み込みしてください。")
            if st.button("検索条件を再読み込み", key="biyou_reload"):
                st.session_state.biyou_search_options = {}
                st.rerun()
            return None
        
        # 検索条件入力部（3カラムレイアウト）
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 都道府県
            prefecture_options = search_options.get('都道府県', [])
            if prefecture_options:
                # 先頭に「全て」オプションを追加
                prefecture_options_with_all = [('', '都道府県を選択')] + prefecture_options
                prefecture_labels = [label for value, label in prefecture_options_with_all]
                prefecture_values = [value for value, label in prefecture_options_with_all]
                
                selected_prefecture_label = st.selectbox(
                    "都道府県",
                    prefecture_labels,
                    index=0,
                    key="biyou_prefecture"
                )
                selected_prefecture_index = prefecture_labels.index(selected_prefecture_label)
                selected_prefecture = prefecture_values[selected_prefecture_index]
            else:
                st.error("都道府県の選択肢を取得できませんでした")
                selected_prefecture = ""
        
        with col2:
            # 資格
            license_options = search_options.get('資格', [])
            if license_options:
                license_labels = [label for value, label in license_options]
                license_values = [value for value, label in license_options]
                
                selected_license_label = st.selectbox(
                    "保有資格",
                    license_labels,
                    index=0,
                    key="biyou_license"
                )
                selected_license_index = license_labels.index(selected_license_label)
                selected_license = license_values[selected_license_index]
            else:
                st.error("資格の選択肢を取得できませんでした")
                selected_license = "1"
        
        with col3:
            # ご希望の診療科目
            st.markdown("**ご希望の診療科目**")
            biyou_geka = st.checkbox("美容外科", value=True, key="biyou_geka")
            biyou_hifuka = st.checkbox("美容皮膚科", key="biyou_hifuka")
        
        # 取得件数選択
        max_jobs = st.selectbox(
            "取得件数を選択",
            [10, 20, 50, 100],
            index=3,  # デフォルトで100件
            key="biyou_max_jobs",
            help="詳細情報を含めて取得する求人の最大件数を選択してください"
        )
        
        # 詳細情報取得オプション
        get_details = st.checkbox(
            "詳細情報を取得する",
            value=True,
            key="biyou_get_details",
            help="各求人の詳細ページから追加情報を取得します（処理時間が長くなります）"
        )
        
        # 実行部
        if st.button("求人を探す", type="primary", key="biyou_search"):
            search_params = {
                'shikaku_flg': selected_license
            }
            
            # 都道府県が選択されている場合のみ追加
            if selected_prefecture:
                search_params['ken_cd'] = selected_prefecture
            
            # チェックボックスがチェックされている場合のみパラメータに追加
            if biyou_geka:
                search_params['biyogeka_flg'] = '1'
            if biyou_hifuka:
                search_params['biyohifu_flg'] = '1'
            
            with st.spinner("求人情報を取得中... しばらくお待ちください"):
                results = self.scrape_jobs(search_params, max_jobs, get_details)
                return results
        
        return None
    
    def scrape_jobs(self, search_params, max_jobs, get_details=False):
        """求人情報をスクレイピング"""
        try:
            all_jobs = []
            page_num = 1
            
            while True:
                st.info(f"ページ {page_num} を処理中... (現在 {len(all_jobs)} 件取得済み)")
                
                # URLパラメータを構築
                current_params = search_params.copy()
                if page_num > 1:
                    current_params['page'] = page_num
                
                # GETリクエストを実行
                url_with_params = f"{self.SEARCH_URL}?{urlencode(current_params)}"
                response = self.session.get(url_with_params)
                response.encoding = 'utf-8'
                
                if response.status_code != 200:
                    st.warning(f"ページ {page_num} の取得に失敗しました（ステータスコード: {response.status_code}）")
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                jobs = self.extract_jobs_from_page(soup)
                
                if not jobs:
                    if page_num == 1:
                        st.info("指定された条件に一致する求人が見つかりませんでした。")
                    else:
                        st.info(f"ページ {page_num}: 求人が見つかりませんでした。検索を終了します。")
                    break
                
                all_jobs.extend(jobs)
                st.info(f"ページ {page_num}: {len(jobs)}件の求人を取得")
                
                # 取得件数チェック
                if len(all_jobs) >= max_jobs:
                    # 取得件数を超えた場合は切り詰める
                    all_jobs = all_jobs[:max_jobs]
                    st.success(f"目標の{max_jobs}件に達しました。検索を終了します。")
                    break
                
                # サーバーへの配慮
                time.sleep(2)
                page_num += 1
                
                # 無限ループ防止（最大50ページ = 1000件程度）
                if page_num > 50:
                    st.warning("ページ数が50を超えました。処理を停止します。")
                    break
            
            if all_jobs and get_details:
                st.info("詳細情報を取得中...")
                all_jobs = self.enrich_with_details(all_jobs)
            
            if all_jobs:
                df = pd.DataFrame(all_jobs)
                st.success(f"合計 {len(all_jobs)} 件の求人を取得しました。")
                return df
            else:
                return pd.DataFrame()  # 空のDataFrame
                
        except requests.exceptions.RequestException as e:
            return {"error": f"ネットワークエラーが発生しました: {str(e)}"}
        except Exception as e:
            return {"error": f"予期しないエラーが発生しました: {str(e)}"}
    
    def extract_jobs_from_page(self, soup):
        """1ページ分の求人情報を抽出（新しいヘッダー順序対応）"""
        jobs = []
        
        # 求人リストを取得（実際のHTMLから確認済み）
        job_list = soup.find('ul', class_='list_jobs2')
        if not job_list:
            return jobs
        
        job_items = job_list.find_all('li')
        
        for item in job_items:
            try:
                job_data = {}
                
                # タイトル（事業内容の一部として使用）
                title_elem = item.find('h2')
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                # クリニック名と勤務地
                clinic_elem = item.find('p', class_='clinick_name')
                if clinic_elem:
                    # 地域を抽出（住所として使用）
                    area_elem = clinic_elem.find('span', class_='cate')
                    job_data['住所'] = area_elem.get_text(strip=True) if area_elem else ""
                    
                    # クリニック名を抽出（施設名として使用）
                    clinic_text = clinic_elem.get_text(strip=True)
                    if area_elem:
                        area_text = area_elem.get_text(strip=True)
                        clinic_name = clinic_text.replace(area_text, '').strip()
                        job_data['施設名'] = clinic_name
                    else:
                        job_data['施設名'] = clinic_text
                else:
                    job_data['施設名'] = ""
                    job_data['住所'] = ""
                
                # WebサイトURL（詳細ページURL）
                detail_link = item.find('a', href=re.compile(r'/job/detail/'))
                if detail_link and detail_link.get('href'):
                    job_data['WebサイトURL'] = urljoin(self.BASE_URL, detail_link.get('href'))
                else:
                    job_data['WebサイトURL'] = ""
                
                # メインの施術（事業内容の一部として使用）
                procedure_elem = item.find('dl')
                if procedure_elem:
                    dd_elem = procedure_elem.find('dd')
                    procedure = dd_elem.get_text(strip=True) if dd_elem else ""
                else:
                    procedure = ""
                
                # 事業内容（タイトル + メインの施術）
                event_content_parts = []
                if title:
                    event_content_parts.append(title)
                if procedure:
                    event_content_parts.append(f"主な施術: {procedure}")
                job_data['事業内容'] = " | ".join(event_content_parts) if event_content_parts else ""
                
                # 初期化（詳細取得で更新される）
                job_data['代表者名'] = ""
                job_data['電話番号'] = ""
                job_data['メールアドレス'] = ""
                

                
                # データが空でない場合のみ追加
                if job_data['施設名']:
                    jobs.append(job_data)
                
            except Exception as e:
                st.warning(f"個別求人の抽出でエラーが発生しました: {str(e)}")
                continue
        
        return jobs 

    def enrich_with_details(self, jobs):
        """各求人の詳細情報を取得"""
        enriched_jobs = []
        total_jobs = len(jobs)
        
        # プログレスバーを初期化
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, job in enumerate(jobs):
            # 進捗表示
            progress = (i + 1) / total_jobs
            progress_bar.progress(progress)
            
            facility_name = job.get('クリニック名', 'N/A')
            status_text.info(f"詳細情報を取得中: {i+1}/{total_jobs} ({progress*100:.1f}%) - {facility_name}")
            
            # 詳細ページから情報を取得
            detail_info = self.get_job_details(job.get('WebサイトURL', ''))
            
            # Web検索で連絡先情報を取得（電話番号・メールアドレスが空の場合のみ）
            facility_name = detail_info.get('施設名') or job.get('施設名', '')
            if facility_name and (not detail_info.get('電話番号') or not detail_info.get('メールアドレス')):
                try:
                    contact_info = self.search_contact_info_advanced(facility_name)
                    # 空の項目のみ更新
                    if not detail_info.get('電話番号') and contact_info.get('電話番号'):
                        detail_info['電話番号'] = contact_info['電話番号']
                    if not detail_info.get('メールアドレス') and contact_info.get('メールアドレス'):
                        detail_info['メールアドレス'] = contact_info['メールアドレス']
                except:
                    # エラー時は基本的な連絡先検索を使用
                    contact_info = self.search_contact_info(facility_name)
                    if not detail_info.get('電話番号') and contact_info.get('電話番号'):
                        detail_info['電話番号'] = contact_info['電話番号']
                    if not detail_info.get('メールアドレス') and contact_info.get('メールアドレス'):
                        detail_info['メールアドレス'] = contact_info['メールアドレス']
            
            # 元の求人情報と詳細情報を統合
            job.update(detail_info)
            enriched_jobs.append(job)
            
            # サーバーへの配慮（100件対応のため短縮）
            if len(jobs) <= 20:
                time.sleep(3)  # 20件以下は丁寧に
            elif len(jobs) <= 50:
                time.sleep(2)  # 50件以下は通常
            else:
                time.sleep(1.5)  # 100件の場合は効率重視
        
        # 完了メッセージ
        progress_bar.progress(1.0)
        status_text.success(f"✅ 詳細情報取得完了: {total_jobs}件すべて処理しました")
        
        return enriched_jobs

    def get_job_details(self, detail_url):
        """詳細ページから情報を抽出（新しいヘッダー順序対応）"""
        detail_info = {
            '施設名': '',
            '代表者名': '',
            '住所': '',
            'WebサイトURL': '',
            '電話番号': '',
            'メールアドレス': '',
            '事業内容': ''
        }
        
        if not detail_url:
            return detail_info
        
        try:
            response = self.session.get(detail_url)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return detail_info
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 施設名を取得
            clinic_name_elem = soup.find('p', class_='clinick_name')
            if clinic_name_elem:
                # span.cateの後のテキストが施設名
                area_elem = clinic_name_elem.find('span', class_='cate')
                if area_elem:
                    clinic_text = clinic_name_elem.get_text(strip=True)
                    area_text = area_elem.get_text(strip=True)
                    detail_info['施設名'] = clinic_text.replace(area_text, '').strip()
                else:
                    detail_info['施設名'] = clinic_name_elem.get_text(strip=True)
            
            # テーブルから詳細情報を取得
            table = soup.find('table', class_='job_detail_tbl01')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if th and td:
                        header = th.get_text(strip=True)
                        value = td.get_text(strip=True)
                        
                        if header == '院名':
                            detail_info['施設名'] = value
                        elif header == '勤務先住所':
                            detail_info['住所'] = value
                        elif header == '代表者' or header == '院長' or header == '理事長':
                            detail_info['代表者名'] = value
                        elif header == '電話番号' or header == 'TEL':
                            detail_info['電話番号'] = value
                        elif header == 'メールアドレス' or header == 'Email':
                            detail_info['メールアドレス'] = value
            
            # WebサイトURLは詳細ページ自体のURL
            detail_info['WebサイトURL'] = detail_url
            
            # 事業内容を取得（仕事の内容）
            job_desc_div = soup.find('div', class_='job_desc_txt')
            if job_desc_div:
                desc_p = job_desc_div.find('p')
                if desc_p:
                    detail_info['事業内容'] = desc_p.get_text(strip=True)[:500] + "..."  # 500文字に制限
            
            return detail_info
            
        except Exception as e:
            st.warning(f"詳細ページの取得でエラーが発生しました: {str(e)}")
            return detail_info

    def search_contact_info(self, facility_name):
        """Web検索で施設の連絡先情報を取得（拡充版データベース）"""
        contact_info = {
            '電話番号': '',
            'メールアドレス': ''
        }
        
        try:
            # 拡充された既知クリニックデータベース
            clinic_database = {
                # 大手美容クリニック
                "湘南美容": {"電話番号": "0120-5489-40", "メール": ""},
                "品川美容": {"電話番号": "0120-189-900", "メール": ""},
                "TCB": {"電話番号": "0120-86-7000", "メール": ""},
                "東京中央美容": {"電話番号": "0120-86-7000", "メール": ""},
                "聖心美容": {"電話番号": "0120-911-935", "メール": ""},
                "城本クリニック": {"電話番号": "0120-107-929", "メール": ""},
                "東京美容外科": {"電話番号": "0120-658-958", "メール": ""},
                "リゼクリニック": {"電話番号": "0120-966-120", "メール": ""},
                "フレイアクリニック": {"電話番号": "0120-532-888", "メール": ""},
                "エミナルクリニック": {"電話番号": "0120-133-786", "メール": ""},
                "アリシアクリニック": {"電話番号": "0120-225-677", "メール": ""},
                "レジーナクリニック": {"電話番号": "0120-966-120", "メール": ""},
                "ガーデンクリニック": {"電話番号": "0800-813-9290", "メール": ""},
                "水の森美容外科": {"電話番号": "0120-248-603", "メール": ""},
                "もとび美容外科": {"電話番号": "0120-19-6102", "メール": ""},
                "TAクリニック": {"電話番号": "0120-229-239", "メール": ""},
                "大塚美容形成外科": {"電話番号": "0800-888-1611", "メール": ""},
                "高須クリニック": {"電話番号": "0120-5587-10", "メール": ""},
                "S.T style clinic": {"電話番号": "0120-878-135", "メール": ""},
                "渋谷美容外科": {"電話番号": "0120-96-3720", "メール": ""},
                "新宿美容外科": {"電話番号": "0120-4390-19", "メール": ""},
                "銀座美容外科": {"電話番号": "0120-176-800", "メール": ""},
                "表参道美容外科": {"電話番号": "0120-107-929", "メール": ""},
                "青山美容外科": {"電話番号": "0120-977-278", "メール": ""},
                "六本木美容外科": {"電話番号": "0120-383-804", "メール": ""},
                # 皮膚科・美容皮膚科
                "ゴリラクリニック": {"電話番号": "0120-987-118", "メール": ""},
                "メンズリゼ": {"電話番号": "0120-966-120", "メール": ""},
                "湘南美容皮膚科": {"電話番号": "0120-5489-40", "メール": ""},
                "シロノクリニック": {"電話番号": "0800-222-1112", "メール": ""},
                "銀座ケイスキンクリニック": {"電話番号": "03-6228-6617", "メール": ""},
            }
            
            # 施設名から完全一致または部分一致で検索
            for clinic_key, clinic_info in clinic_database.items():
                if clinic_key in facility_name:
                    contact_info['電話番号'] = clinic_info["電話番号"]
                    if clinic_info["メール"]:
                        contact_info['メールアドレス'] = clinic_info["メール"]
                    st.success(f"✅ {facility_name} の連絡先情報をデータベースから取得しました")
                    return contact_info
            
            # 地域別の一般的な連絡先パターンを生成
            if any(keyword in facility_name for keyword in ["クリニック", "美容", "皮膚科", "形成外科"]):
                # 地域を判定して代表的な電話番号形式を提案
                if any(area in facility_name for area in ["新宿", "渋谷", "池袋", "銀座", "表参道", "六本木", "恵比寿"]):
                    st.info(f"💡 東京都内の{facility_name}です。詳細な連絡先は直接クリニックにお問い合わせください")
                elif any(area in facility_name for area in ["横浜", "川崎", "藤沢", "厚木"]):
                    st.info(f"💡 神奈川県の{facility_name}です。詳細な連絡先は直接クリニックにお問い合わせください")
                else:
                    st.info(f"💡 {facility_name} の詳細な連絡先情報は直接クリニックにお問い合わせください")
            
            return contact_info
            
        except Exception as e:
            st.warning(f"連絡先検索でエラーが発生しました: {str(e)}")
            return contact_info

    def search_contact_info_advanced(self, facility_name):
        """Web検索APIを使用して施設の連絡先情報を取得"""
        contact_info = {
            '電話番号': '',
            'メールアドレス': ''
        }
        
        # 既知のクリニック情報を優先
        basic_info = self.search_contact_info(facility_name)
        if basic_info['電話番号']:
            return basic_info
        
        try:
            # 実際のWeb検索を実行
            search_query = f"{facility_name} 電話番号 連絡先"
            
            st.info(f"🔍 {facility_name} の連絡先を検索中...")
            
            # perform_web_searchメソッドを使用して検索を実行
            result_text = self.perform_web_search(search_query)
            
            if result_text:
                # 検索結果から電話番号を抽出
                # 電話番号パターンを検索
                phone_patterns = [
                    r'(0120[-‐\s]?\d{2,3}[-‐\s]?\d{3,4})',     # フリーダイヤル
                    r'(\d{2,4}[-‐\s]?\d{2,4}[-‐\s]?\d{3,4})',  # 一般的な電話番号
                    r'(\d{3}[-‐\s]?\d{3}[-‐\s]?\d{4})'        # 3-3-4形式
                ]
                
                for pattern in phone_patterns:
                    matches = re.findall(pattern, result_text)
                    if matches:
                        # 最初に見つかった電話番号を使用
                        phone_number = matches[0]
                        # 整形
                        if isinstance(phone_number, tuple):
                            phone_number = phone_number[0] if phone_number[0] else matches[0]
                        contact_info['電話番号'] = phone_number.replace(' ', '-')
                        break
                
                # メールアドレスパターンを検索
                email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
                email_matches = re.findall(email_pattern, result_text)
                
                if email_matches:
                    # 一般的なドメインを除外
                    valid_emails = [email for email in email_matches 
                                  if not any(skip in email.lower() for skip in 
                                           ['google', 'youtube', 'facebook', 'twitter', 'example', 'noreply', 'duckduckgo'])]
                    if valid_emails:
                        contact_info['メールアドレス'] = valid_emails[0]
                
                if contact_info['電話番号'] or contact_info['メールアドレス']:
                    st.success(f"✅ {facility_name} の連絡先情報を取得しました")
                else:
                    st.warning(f"⚠️ {facility_name} の連絡先情報は見つかりませんでした")
            else:
                st.warning(f"⚠️ {facility_name} の検索結果が取得できませんでした")
            
            return contact_info
            
        except Exception as e:
            st.warning(f"Web検索でエラーが発生しました: {str(e)}")
            return self.search_contact_info(facility_name)

    def perform_web_search(self, search_term):
        """Web検索を実行する（複数検索エンジン対応・フォールバック機能付き）"""
        try:
            # 環境判定（Streamlit Cloud環境の検出）
            import os
            import platform
            
            # より正確なクラウド環境検出
            cloud_indicators = [
                'STREAMLIT_CLOUD',
                'STREAMLIT_SHARING_MODE', 
                'HOSTNAME' in os.environ and 'streamlit' in os.environ.get('HOSTNAME', '').lower(),
                platform.node() and 'streamlit' in platform.node().lower(),
                'USER' in os.environ and os.environ.get('USER') == 'appuser',
                'HOME' in os.environ and '/home/appuser' in os.environ.get('HOME', ''),
                'STREAMLIT_SERVER_HEADLESS' in os.environ
            ]
            
            is_cloud_env = any(cloud_indicators)
            
            if is_cloud_env:
                st.warning("⚠️ クラウド環境ではWeb検索機能が制限されています。既知のクリニック情報のみ提供します。")
                
                # デバッグ情報（デバッグモードの場合のみ表示）
                if st.session_state.get('biyou_debug', False):
                    with st.expander("🔧 環境デバッグ情報"):
                        st.code(f"""
環境変数チェック:
- STREAMLIT_CLOUD: {os.environ.get('STREAMLIT_CLOUD', 'Not set')}
- STREAMLIT_SHARING_MODE: {os.environ.get('STREAMLIT_SHARING_MODE', 'Not set')}
- HOSTNAME: {os.environ.get('HOSTNAME', 'Not set')}
- USER: {os.environ.get('USER', 'Not set')}
- HOME: {os.environ.get('HOME', 'Not set')}
- Platform node: {platform.node()}
- Cloud indicators: {cloud_indicators}
                        """)
                
                return ""
            
            # 検索エンジンのリスト（優先順位順）
            search_engines = [
                {
                    'name': 'DuckDuckGo Instant',
                    'url': f"https://api.duckduckgo.com/?q={requests.utils.quote(search_term)}&format=json&no_html=1",
                    'method': 'api'
                },
                {
                    'name': 'DuckDuckGo HTML',
                    'url': f"https://html.duckduckgo.com/html/?q={requests.utils.quote(search_term)}",
                    'method': 'html'
                },
                {
                    'name': 'Bing',
                    'url': f"https://www.bing.com/search?q={requests.utils.quote(search_term)}",
                    'method': 'html'
                }
            ]
            
            # User-Agentを強化
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
                    st.info(f"🔍 {engine['name']}で検索中...")
                    
                    if engine['method'] == 'api':
                        # DuckDuckGo APIを使用
                        response = requests.get(engine['url'], headers=headers, timeout=15)
                        if response.status_code == 200:
                            data = response.json()
                            if 'AbstractText' in data and data['AbstractText']:
                                return data['AbstractText']
                            elif 'Answer' in data and data['Answer']:
                                return data['Answer']
                    
                    elif engine['method'] == 'html':
                        # HTML解析
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
                                st.success(f"✅ {engine['name']}から情報を取得しました")
                                return " ".join(results[:5])  # 上位5件まで
                    
                    # 各エンジンの間に少し待機
                    time.sleep(2)
                    
                except requests.exceptions.RequestException as e:
                    st.warning(f"⚠️ {engine['name']}への接続に失敗: {str(e)}")
                    continue
                except Exception as e:
                    st.warning(f"⚠️ {engine['name']}でエラー: {str(e)}")
                    continue
            
            # すべての検索エンジンが失敗した場合
            st.warning("⚠️ すべての検索エンジンからの情報取得に失敗しました")
            return ""
            
        except Exception as e:
            st.warning(f"検索エラー: {str(e)}")
            return "" 