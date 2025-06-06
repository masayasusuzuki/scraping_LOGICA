import streamlit as st
import pandas as pd
from scrapers.medical_concierge import MedicalConciergeUI
from scrapers.biyou_nurse import BiyouNurseUI

def main():
    """メインアプリケーション"""
    st.set_page_config(
        page_title="求人サイトスクレイピング",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # カスタムCSSでサイドバーをスタイリング
    st.markdown("""
    <style>
    /* サイドバーのスタイリング - 新しいStreamlitバージョン対応 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%) !important;
        border-right: 3px solid #3b82f6 !important;
    }
    
    section[data-testid="stSidebar"] > div {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%) !important;
        padding-top: 2rem !important;
    }
    
    /* サイドバー内のテキスト色 */
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 2px solid #3b82f6 !important;
    }
    
    /* ラジオボタンのスタイリング */
    section[data-testid="stSidebar"] label {
        color: #e5e7eb !important;
        font-weight: 500 !important;
    }
    
    section[data-testid="stSidebar"] label:hover {
        color: #ffffff !important;
    }
    
    /* ラジオボタンの選択状態 */
    section[data-testid="stSidebar"] input[type="radio"]:checked + label {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* カスタムヘッダーのスタイル */
    .sidebar-header {
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        margin-bottom: 1.5rem !important;
        padding-bottom: 0.75rem !important;
        border-bottom: 2px solid #3b82f6 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    /* レガシー対応 */
    .css-1d391kg,
    .css-1outpf7,
    .st-emotion-cache-16txtl3 {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%) !important;
    }
    
    .css-1d391kg *,
    .css-1outpf7 *,
    .st-emotion-cache-16txtl3 * {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # サイドバー：サイト選択
    with st.sidebar:
        st.markdown('<div class="sidebar-header">対象サイト選択</div>', unsafe_allow_html=True)
        selected_site = st.radio(
            "",
            ["美容ナース.com", "メディカル・コンシェルジュネット"],
            index=0,
            label_visibility="collapsed"
        )
    
    # メイン画面：動的UI表示エリア
    if selected_site == "美容ナース.com":
        biyou_ui = BiyouNurseUI()
        results = biyou_ui.render_ui()
        
        # 結果表示エリア
        if results is not None:
            render_results(results, selected_site)
    
    elif selected_site == "メディカル・コンシェルジュネット":
        medical_ui = MedicalConciergeUI()
        results = medical_ui.render_ui()
        
        # 結果表示エリア
        if results is not None:
            render_results(results, selected_site)

def render_results(results, site_name):
    """スクレイピング結果の表示エリア"""
    st.markdown("---")
    st.header("取得結果")
    
    if isinstance(results, dict) and "error" in results:
        st.error(f"エラーが発生しました: {results['error']}")
        return
    
    if isinstance(results, pd.DataFrame) and not results.empty:
        # 取得件数表示
        st.success(f"{len(results)}件の求人が見つかりました。")
        
        # 求人一覧テーブル（指定された7項目のみ）
        st.subheader("求人一覧テーブル")
        
        # 施設名の統一（クリニック名がある場合は施設名として扱う）
        display_results = results.copy()
        if 'クリニック名' in display_results.columns and '施設名' not in display_results.columns:
            display_results['施設名'] = display_results['クリニック名']
        elif 'クリニック名' in display_results.columns and '施設名' in display_results.columns:
            # 施設名が空の場合はクリニック名を使用
            display_results['施設名'] = display_results['施設名'].fillna(display_results['クリニック名'])
            display_results['施設名'] = display_results.apply(
                lambda row: row['クリニック名'] if (pd.isna(row['施設名']) or row['施設名'] == '') else row['施設名'], axis=1
            )
        
        # 求人URLの列名を統一
        if '詳細ページURL' in display_results.columns:
            display_results['求人URL'] = display_results['詳細ページURL']
        
        # 業務内容の列名を統一
        if '仕事の内容' in display_results.columns:
            display_results['業務内容'] = display_results['仕事の内容']
        
        # 指定された7項目のカラム順序
        target_columns = [
            '施設名', '代表者名', '勤務地', '求人URL', '電話番号', 'メールアドレス', '業務内容'
        ]
        
        # 存在するカラムのみを選択
        available_target_columns = [col for col in target_columns if col in display_results.columns]
        
        if available_target_columns:
            # 指定された項目のみを表示
            target_data = display_results[available_target_columns]
            st.dataframe(
                target_data,
                use_container_width=True,
                hide_index=True,
                height=400
            )
        else:
            # 指定項目が見つからない場合は全データを表示
            st.dataframe(
                results,
                use_container_width=True,
                hide_index=True,
                height=400
            )
        
        # CSVダウンロードボタン
        # カラムの順序を整理（ユーザー指定の順序）
        column_order = [
            '施設名', 'クリニック名', '代表者名', '勤務地', '詳細ページURL', '電話番号', 'メールアドレス', '仕事の内容',
            '求人No', 'タイトル', '職種', '施設', '業務 (働き方)', '給与', '交通',
            'メインの施術', '所在地', '情報源サイト名'
        ]
        
        # 存在するカラムのみを選択
        available_columns = [col for col in column_order if col in results.columns]
        
        # 最終的な表示用カラム順序（ユーザー指定）
        final_column_order = [
            '施設名', '代表者名', '勤務地', '求人URL', '電話番号', 'メールアドレス', '業務内容'
        ]
        
        # 追加情報も含める場合
        additional_columns = [
            '求人No', 'タイトル', '職種', '給与', '交通', 'メインの施術', '所在地', '情報源サイト名'
        ]
        
        # 存在するカラムのみを最終選択
        final_available_columns = [col for col in final_column_order if col in display_results.columns]
        additional_available_columns = [col for col in additional_columns if col in display_results.columns]
        
        # メイン情報＋追加情報の順序で結合
        all_display_columns = final_available_columns + additional_available_columns
        ordered_results = display_results[all_display_columns]
        
        csv_data = ordered_results.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="CSVファイルをダウンロード",
            data=csv_data,
            file_name=f"{site_name}_求人情報_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # 統計情報
        with st.expander("データ統計"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("総件数", len(results))
            with col2:
                unique_locations = results['勤務地'].nunique() if '勤務地' in results.columns else 0
                st.metric("勤務地数", unique_locations)
            with col3:
                # 美容ナース.comの場合はクリニック名、その他は職種でカウント
                if site_name == "美容ナース.com" and 'クリニック名' in results.columns:
                    unique_clinics = results['クリニック名'].nunique()
                    st.metric("クリニック数", unique_clinics)
                else:
                    unique_jobs = results['職種'].nunique() if '職種' in results.columns else 0
                    st.metric("職種数", unique_jobs)
            with col4:
                # 詳細情報取得率
                detail_count = len([idx for idx, row in results.iterrows() 
                                 if any(row.get(col) for col in ['施設名', '所在地', '電話番号'])])
                detail_rate = (detail_count / len(results)) * 100 if len(results) > 0 else 0
                st.metric("詳細情報取得率", f"{detail_rate:.1f}%")
    
    elif isinstance(results, pd.DataFrame) and results.empty:
        st.warning("指定された条件では求人が見つかりませんでした。検索条件を変更してお試しください。")
    
    else:
        st.error("データの取得に失敗しました。しばらく時間をおいてから再度お試しください。")

if __name__ == "__main__":
    main() 